"""Phase 11 — IMEI history, warranty status, dead stock, purchase history.

Covers: server-derived warranty state, the per-device timeline built from
real records, the enriched product detail, the ?stock=dead product filter,
per-product purchase filtering, and tenant isolation of the new endpoints.

All data is synthetic test data (never production data).
"""
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import UserProfile
from businesses.models import Business
from customers.models import Customer
from inventory.models import MobileDevice
from products.models import Category, Product
from purchases.models import Purchase, PurchaseItem
from sales.models import Sale, SaleItem
from suppliers.models import Supplier


class Phase11TestBase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='p11_owner@dukaanflow.com',
            email='p11_owner@dukaanflow.com',
            password='Password123!', first_name='Ashok')
        self.business = Business.objects.create(
            owner=self.user, name='Ashok_cells', owner_name='Ashok',
            phone='9822003344', email='p11_owner@dukaanflow.com',
            address='Shop 3, MG Road', city='Nashik',
            state='Maharashtra', pincode='422001',
            invoice_prefix='ASH-', next_invoice_number=2001)
        UserProfile.objects.create(
            user=self.user, business=self.business,
            phone='9822003344', role='OWNER')
        self._login('p11_owner@dukaanflow.com', 'Password123!')
        self._seed()

    def _login(self, email, password):
        res = self.client.post('/api/auth/login/', {'email': email, 'password': password},
                               format='json')
        self.assertEqual(res.status_code, 200, res.data)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {res.data['tokens']['access']}")

    def _other_shop(self, suffix='X'):
        user = User.objects.create_user(
            username=f'p11_other{suffix}@dukaanflow.com',
            email=f'p11_other{suffix}@dukaanflow.com',
            password='Password123!')
        business = Business.objects.create(
            owner=user, name=f'Other Shop {suffix}', owner_name='Other',
            phone='9000000000', invoice_prefix=f'OTH{suffix}-',
            next_invoice_number=1)
        UserProfile.objects.create(user=user, business=business,
                                   phone='9000000000', role='OWNER')
        return user, business

    def _seed(self):
        b = self.business
        self.category = Category.objects.create(business=b, name='Feature Phones')
        self.supplier = Supplier.objects.create(
            business=b, name='Nitin', company_name='Nitin Telecom',
            phone='9333445566')
        self.customer = Customer.objects.create(
            business=b, name='Vijay Rao', phone='9876504321')
        # IMEI-tracked product with a 12-month warranty.
        self.product = Product.objects.create(
            business=b, category=self.category, name='Galaxy A15',
            brand='Samsung', sku='GA15-128', stock_quantity=1,
            min_stock=2, purchase_price=Decimal('11000.00'),
            selling_price=Decimal('13000.00'), warranty_months=12,
            is_imei_tracked=True)
        self.device = MobileDevice.objects.create(
            business=b, product=self.product, imei_1='356789012345601',
            model_name='A15 Blue', purchase_price=Decimal('11000.00'),
            selling_price=Decimal('13000.00'), status='IN_STOCK')
        # A second product, never sold, with stock -> dead stock.
        self.dead_product = Product.objects.create(
            business=b, category=self.category, name='Old Charger Pack',
            brand='Universal', sku='CHG-OLD', stock_quantity=8,
            min_stock=2, purchase_price=Decimal('150.00'),
            selling_price=Decimal('250.00'))
        # A fast-moving product that sells today -> never dead stock.
        self.live_product = Product.objects.create(
            business=b, category=self.category, name='Screen Guard X',
            brand='ClearPro', sku='SGX-1', stock_quantity=20,
            min_stock=2, purchase_price=Decimal('40.00'),
            selling_price=Decimal('99.00'))

    def _checkout(self, product_id, device_id=None, paid=13000, qty=1,
                  unit_price=13000):
        return self.client.post('/api/pos/checkout/', {
            'customer_id': self.customer.id,
            'payment_method': 'CASH',
            'discount': 0, 'tax': 0, 'paid_amount': paid,
            'items': [{'product_id': product_id, 'quantity': qty,
                       'unit_price': unit_price, 'discount': 0,
                       'device_id': device_id}],
        }, format='json')


class WarrantyStatusTest(Phase11TestBase):
    def test_active_warranty(self):
        dev = self.device
        dev.warranty_expiry_date = timezone.now().date() + timedelta(days=200)
        dev.save()
        res = self.client.get(f'/api/inventory/imei/{dev.pk}/history/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['device']['warranty_status'], 'ACTIVE')
        self.assertEqual(
            res.data['device']['warranty_days_remaining'], 200)

    def test_expired_warranty_is_never_reported_active(self):
        dev = self.device
        dev.warranty_expiry_date = timezone.now().date() - timedelta(days=5)
        dev.save()
        res = self.client.get(f'/api/inventory/imei/{dev.pk}/history/')
        self.assertEqual(res.data['device']['warranty_status'], 'EXPIRED')
        self.assertEqual(res.data['device']['warranty_days_remaining'], -5)

    def test_no_warranty_when_no_expiry(self):
        res = self.client.get(f'/api/inventory/imei/{self.device.pk}/history/')
        self.assertEqual(res.data['device']['warranty_status'], 'NO_WARRANTY')
        self.assertIsNone(res.data['device']['warranty_days_remaining'])

    def test_checkout_sets_warranty_expiry_and_history_reports_it(self):
        res = self._checkout(self.product.id, self.device.id)
        self.assertEqual(res.status_code, 201, res.data)
        self.device.refresh_from_db()
        self.assertIsNotNone(self.device.warranty_expiry_date)
        hist = self.client.get(
            f'/api/inventory/imei/{self.device.pk}/history/')
        self.assertEqual(hist.data['device']['warranty_status'], 'ACTIVE')
        self.assertEqual(hist.data['device']['status'], 'SOLD')


class ImeiHistoryTest(Phase11TestBase):
    def test_timeline_contains_registration_and_sale_with_invoice(self):
        res = self._checkout(self.product.id, self.device.id)
        self.assertEqual(res.status_code, 201, res.data)
        invoice = res.data['sale']['invoice_number']

        hist = self.client.get(
            f'/api/inventory/imei/{self.device.pk}/history/')
        self.assertEqual(hist.status_code, 200)
        types = [e['type'] for e in hist.data['timeline']]
        # Registration + the registration movement + the POS sale.
        self.assertIn('REGISTERED', types)
        self.assertIn('SALE', types)
        sale_entry = next(e for e in hist.data['timeline'] if e['type'] == 'SALE')
        self.assertEqual(sale_entry['reference'], invoice)
        self.assertIn('Vijay Rao', sale_entry['note'])
        # Exactly one SALE entry — the derived sale must not double up.
        self.assertEqual(types.count('SALE'), 1)
        # Timeline is newest-first.
        dates = [e['date'] for e in hist.data['timeline'] if e['date']]
        self.assertEqual(dates, sorted(dates, reverse=True))

    def test_sale_without_movement_link_still_shows_in_timeline(self):
        """Devices sold before device-linked movements existed (legacy rows)
        still get their sale derived from the stored sale_item — but only
        once, and only from what the record actually says."""
        product = Product.objects.create(
            business=self.business, category=self.category,
            name='Legacy Bolt', brand='Samsung', sku='LGT-1',
            stock_quantity=1, min_stock=1,
            purchase_price=Decimal('5000.00'),
            selling_price=Decimal('6000.00'))
        device = MobileDevice.objects.create(
            business=self.business, product=product, imei_1='356789012345699',
            status='IN_STOCK')
        # simulate a legacy sale: set the links directly, no movement row.
        sale = Sale.objects.create(
            business=self.business, customer=self.customer,
            invoice_number='ASH-LEGACY-1', subtotal=Decimal('6000.00'),
            total_amount=Decimal('6000.00'), paid_amount=Decimal('6000.00'),
            payment_method='CASH')
        sale_item = SaleItem.objects.create(
            sale=sale, product=product, quantity=1,
            unit_price=Decimal('6000.00'), total_price=Decimal('6000.00'))
        device.status = 'SOLD'
        device.customer = self.customer
        device.sale_item = sale_item
        device.sale_date = timezone.now()
        device.save()

        hist = self.client.get(f'/api/inventory/imei/{device.pk}/history/')
        self.assertEqual(hist.status_code, 200)
        sales = [e for e in hist.data['timeline'] if e['type'] == 'SALE']
        self.assertEqual(len(sales), 1)
        self.assertEqual(sales[0]['reference'], sale.invoice_number)

    def test_history_is_tenant_isolated(self):
        _, other = self._other_shop()
        other_device = MobileDevice.objects.create(
            business=other, product=self.product, imei_1='356999999999999')
        res = self.client.get(f'/api/inventory/imei/{other_device.pk}/history/')
        self.assertEqual(res.status_code, 404)

    def test_unknown_device_is_404(self):
        self.assertEqual(
            self.client.get('/api/inventory/imei/99999/history/').status_code,
            404)

    def test_staff_can_read_their_own_shops_history(self):
        staff_user = User.objects.create_user(
            username='p11_staff@dukaanflow.com',
            email='p11_staff@dukaanflow.com', password='Password123!')
        UserProfile.objects.create(
            user=staff_user, business=self.business, role='STAFF',
            permissions=['inventory', 'products'])
        staff_client = APIClient()
        res = staff_client.post('/api/auth/login/',
                                {'email': 'p11_staff@dukaanflow.com',
                                 'password': 'Password123!'}, format='json')
        staff_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {res.data['tokens']['access']}")
        res = staff_client.get(f'/api/inventory/imei/{self.device.pk}/history/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['device']['imei_1'], '356789012345601')


class ProductDetailHistoryTest(Phase11TestBase):
    def _purchase(self, product, qty, unit_cost, invoice='PO-11-1'):
        purchase = Purchase.objects.create(
            business=self.business, supplier=self.supplier,
            invoice_number=invoice, total_amount=Decimal(qty) * unit_cost,
            paid_amount=Decimal(qty) * unit_cost, payment_method='CASH')
        PurchaseItem.objects.create(
            purchase=purchase, product=product, quantity=qty,
            unit_cost=unit_cost, total_cost=Decimal(qty) * unit_cost)
        return purchase

    def test_detail_returns_movements_purchase_history_and_devices(self):
        self._purchase(self.product, 5, Decimal('11000.00'))
        res = self.client.post('/api/inventory/adjust/', {
            'product_id': self.product.pk,
            'action': 'INCREASE', 'quantity': 2,
            'reason': 'Audit Correction',
        }, format='json')
        self.assertEqual(res.status_code, 200, res.data)
        res = self.client.get(f'/api/products/{self.product.pk}/')
        self.assertEqual(res.status_code, 200)

        self.assertTrue(len(res.data['movements']) >= 1)
        self.assertEqual(res.data['movements'][0]['product_name'],
                         'Galaxy A15')
        self.assertEqual(len(res.data['purchase_history']), 1)
        self.assertEqual(res.data['purchase_history'][0]['invoice_number'],
                         'PO-11-1')
        self.assertEqual(res.data['purchase_history'][0]['quantity'], 5)
        self.assertEqual(res.data['purchase_history'][0]['supplier_name'],
                         'Nitin Telecom')
        # IMEI-tracked product exposes its registered units.
        self.assertEqual(len(res.data['devices']), 1)
        self.assertEqual(res.data['devices'][0]['imei_1'], '356789012345601')

    def test_purchase_history_amounts_come_from_the_server(self):
        """The client never computes money: totals are the DB values."""
        self._purchase(self.product, 3, Decimal('11000.00'))
        res = self.client.get(f'/api/products/{self.product.pk}/')
        self.assertEqual(res.data['purchase_history'][0]['unit_cost'], 11000.0)
        self.assertEqual(res.data['purchase_history'][0]['total_cost'], 33000.0)

    def test_non_tracked_product_has_no_devices_section_rows(self):
        res = self.client.get(f'/api/products/{self.dead_product.pk}/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['devices'], [])

    def test_dead_stock_verdict_matches_report(self):
        # A bill today is what makes the difference between "live" and "dead".
        res = self._checkout(self.live_product.id, device_id=None,
                             paid=99, unit_price=99)
        self.assertEqual(res.status_code, 201, res.data)
        report = self.client.get('/api/reports/stock/')
        self.assertEqual(report.status_code, 200)
        dead_names = [d['name'] for d in report.data['dead_stock']]
        self.assertIn('Old Charger Pack', dead_names)
        self.assertNotIn('Screen Guard X', dead_names)

        for product, expected in ((self.dead_product, True),
                                  (self.live_product, False)):
            res = self.client.get(f'/api/products/{product.pk}/')
            self.assertEqual(res.data['is_dead_stock'], expected,
                             f'{product.name} verdict mismatch')

    def test_recent_sale_clears_dead_stock_flag(self):
        res = self._checkout(self.live_product.id, device_id=None,
                             paid=99, unit_price=99)
        self.assertEqual(res.status_code, 201, res.data)
        res = self.client.get(f'/api/products/{self.live_product.pk}/')
        self.assertFalse(res.data['is_dead_stock'])
        self.assertIsNotNone(res.data['last_sale_date'])


class DeadStockFilterTest(Phase11TestBase):
    def test_stock_dead_filter_and_sale_removes_product(self):
        res = self.client.get('/api/products/?stock=dead')
        self.assertEqual(res.status_code, 200)
        rows = res.data.get('results', res.data)
        names = [p['name'] for p in rows]
        # In stock and never sold -> dead.
        self.assertIn('Old Charger Pack', names)
        self.assertIn('Screen Guard X', names)

        # A bill today is exactly what lifts a product out of dead stock.
        res = self._checkout(self.live_product.id, device_id=None,
                             paid=99, unit_price=99)
        self.assertEqual(res.status_code, 201, res.data)
        res = self.client.get('/api/products/?stock=dead')
        rows = res.data.get('results', res.data)
        names = [p['name'] for p in rows]
        self.assertIn('Old Charger Pack', names)
        self.assertNotIn('Screen Guard X', names)


class PurchaseHistoryFilterTest(Phase11TestBase):
    def test_product_filter_returns_only_that_products_purchases(self):
        purchase_a = Purchase.objects.create(
            business=self.business, supplier=self.supplier,
            invoice_number='PO-A', total_amount=Decimal('33000.00'),
            paid_amount=Decimal('33000.00'), payment_method='CASH')
        PurchaseItem.objects.create(
            purchase=purchase_a, product=self.product, quantity=3,
            unit_cost=Decimal('11000.00'), total_cost=Decimal('33000.00'))
        purchase_b = Purchase.objects.create(
            business=self.business, supplier=self.supplier,
            invoice_number='PO-B', total_amount=Decimal('800.00'),
            paid_amount=Decimal('800.00'), payment_method='CASH')
        PurchaseItem.objects.create(
            purchase=purchase_b, product=self.dead_product, quantity=4,
            unit_cost=Decimal('200.00'), total_cost=Decimal('800.00'))

        res = self.client.get(f'/api/purchases/?product={self.product.pk}')
        self.assertEqual(res.status_code, 200)
        rows = res.data.get('results', res.data)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['invoice_number'], 'PO-A')

        # Unfiltered list keeps both.
        res = self.client.get('/api/purchases/')
        rows = res.data.get('results', res.data)
        self.assertEqual(len(rows), 2)

    def test_purchase_filter_is_tenant_scoped(self):
        _, other = self._other_shop()
        other_purchase = Purchase.objects.create(
            business=other, supplier=self.supplier,
            invoice_number='PO-LEAK', total_amount=Decimal('1.00'),
            paid_amount=Decimal('1.00'), payment_method='CASH')
        PurchaseItem.objects.create(
            purchase=other_purchase, product=self.product, quantity=1,
            unit_cost=Decimal('1.00'), total_cost=Decimal('1.00'))
        res = self.client.get(f'/api/purchases/?product={self.product.pk}')
        rows = res.data.get('results', res.data)
        self.assertEqual(len(rows), 0)


class DeviceListProductFilterTest(Phase11TestBase):
    def test_product_filter_on_device_list(self):
        res = self.client.get(f'/api/inventory/imei/?product={self.product.pk}')
        self.assertEqual(res.status_code, 200)
        rows = res.data.get('results', res.data)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['imei_1'], '356789012345601')

        other_product = Product.objects.create(
            business=self.business, category=self.category,
            name='Other Phone', brand='Samsung', sku='OTH-P',
            stock_quantity=1, min_stock=1, is_imei_tracked=True)
        MobileDevice.objects.create(
            business=self.business, product=other_product,
            imei_1='356789012345677', status='IN_STOCK')
        res = self.client.get(
            f'/api/inventory/imei/?product={other_product.pk}')
        rows = res.data.get('results', res.data)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['imei_1'], '356789012345677')
