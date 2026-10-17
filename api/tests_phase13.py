"""Phases 13-15 — Financial integrity regression tests (all synthetic data).

Covers the money-ledger guarantees the product promises:

1. Stock-once: an IMEI unit can never be sold twice; a device of another
   product or another shop can never be attached to a bill.
2. Stock-can-not-go-negative and a rejected checkout leaves zero half-written
   rows (no sale, no line, no movement, no payment, stock untouched).
3. Server-side totals: the client's cart math is never trusted — subtotal,
   discount, tax, total, paid and due are recomputed server-side with Decimal
   precision, and a padded paid_amount is clamped to the bill total.
4. Ledger immutability: customer khata balances are always derived from the
   sale/payment history, overpayments are rejected (no silent floor at zero),
   and recording a payment never mutates the original bill rows.

Never production data; in-memory sqlite test DB only.
"""
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import UserProfile
from businesses.models import Business
from customers.models import Customer
from inventory.models import MobileDevice, StockMovement
from payments.models import Payment
from products.models import Category, Product
from sales.models import Sale, SaleItem


class Phase13TestBase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='p13_owner@dukaanflow.com',
            email='p13_owner@dukaanflow.com',
            password='Password123!', first_name='Ramesh')
        self.business = Business.objects.create(
            owner=self.user, name='Ramesh Mobiles', owner_name='Ramesh',
            phone='9822001122', email='p13_owner@dukaanflow.com',
            address='Shop 1, Main Bazar', city='Pune',
            state='Maharashtra', pincode='411001',
            invoice_prefix='RM-', next_invoice_number=5001)
        UserProfile.objects.create(
            user=self.user, business=self.business,
            phone='9822001122', role='OWNER')
        self._login('p13_owner@dukaanflow.com', 'Password123!')
        self._seed()

    def _login(self, email, password):
        res = self.client.post('/api/auth/login/', {'email': email, 'password': password},
                               format='json')
        self.assertEqual(res.status_code, 200, res.data)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {res.data['tokens']['access']}")

    def _other_shop(self, suffix='X'):
        user = User.objects.create_user(
            username=f'p13_other{suffix}@dukaanflow.com',
            email=f'p13_other{suffix}@dukaanflow.com',
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
        self.category = Category.objects.create(business=b, name='Smartphones')
        self.customer = Customer.objects.create(
            business=b, name='Suresh Patil', phone='9876512345')
        # IMEI-tracked product, one device in stock.
        self.imei_product = Product.objects.create(
            business=b, category=self.category, name='Galaxy A25',
            brand='Samsung', sku='GA25-128', stock_quantity=1,
            min_stock=1, purchase_price=Decimal('14000.00'),
            selling_price=Decimal('16500.00'), warranty_months=12,
            is_imei_tracked=True)
        self.device = MobileDevice.objects.create(
            business=b, product=self.imei_product, imei_1='490154203237518',
            model_name='A25 Black', purchase_price=Decimal('14000.00'),
            selling_price=Decimal('16500.00'), status='IN_STOCK')
        # Bulk product with several units in stock.
        self.bulk_product = Product.objects.create(
            business=b, category=self.category, name='USB-C Cable 1m',
            brand='Anik', sku='USBC-1M', stock_quantity=10,
            min_stock=2, purchase_price=Decimal('60.00'),
            selling_price=Decimal('150.00'))

    def _checkout(self, items, **overrides):
        payload = {
            'customer_id': overrides.pop('customer_id', self.customer.id),
            'payment_method': overrides.pop('payment_method', 'CASH'),
            'discount': overrides.pop('discount', 0),
            'tax': overrides.pop('tax', 0),
            'paid_amount': overrides.pop('paid_amount', None),
            'items': items,
        }
        if payload['paid_amount'] is None:
            payload['paid_amount'] = overrides.pop('default_paid', 0)
        payload.update(overrides)
        return self.client.post('/api/pos/checkout/', payload, format='json')

    def _imei_line(self, price=16500, **kw):
        line = {'product_id': self.imei_product.id, 'quantity': 1,
                'unit_price': price, 'discount': 0,
                'device_id': self.device.id}
        line.update(kw)
        return [line]

    def _bulk_lines(self, qty=2, price=150):
        return [{'product_id': self.bulk_product.id, 'quantity': qty,
                 'unit_price': price, 'discount': 0}]


class StockOnceTest(Phase13TestBase):
    def test_imei_unit_cannot_be_sold_twice(self):
        res = self._checkout(self._imei_line(), payment_method='CASH',
                             paid_amount=16500)
        self.assertEqual(res.status_code, 201, res.data)
        first_sale = Sale.objects.get()
        device = MobileDevice.objects.get(pk=self.device.id)
        self.assertEqual(device.status, 'SOLD')
        self.assertEqual(device.sale_item.sale_id, first_sale.id)

        # Restock the product (the unit stays SOLD) and try to bill the same
        # IMEI unit again on a separate bill.
        self.imei_product.stock_quantity = 1
        self.imei_product.save()
        res2 = self._checkout(self._imei_line(), payment_method='CASH',
                              paid_amount=16500)
        self.assertEqual(res2.status_code, 400, res2.data)
        self.assertIn('already sold', res2.data['error'])

        # Nothing was overwritten: the device still points at the first sale.
        device.refresh_from_db()
        self.assertEqual(Sale.objects.count(), 1)
        self.assertEqual(device.sale_item.sale_id, first_sale.id)
        self.assertEqual(device.customer_id, self.customer.id)

    def test_device_from_another_product_is_rejected(self):
        # Bill the bulk product's line but attach the Galaxy device to it.
        res = self.client.post('/api/pos/checkout/', {
            'customer_id': self.customer.id,
            'payment_method': 'CASH',
            'paid_amount': 300,
            'items': [{'product_id': self.bulk_product.id, 'quantity': 2,
                       'unit_price': 150, 'discount': 0,
                       'device_id': self.device.id}],
        }, format='json')
        self.assertEqual(res.status_code, 400, res.data)
        self.assertIn('does not belong', res.data['error'])
        # The device is untouched and the bill was never created.
        self.device.refresh_from_db()
        self.assertEqual(self.device.status, 'IN_STOCK')
        self.assertEqual(Sale.objects.count(), 0)

    def test_device_from_another_shop_is_rejected(self):
        _, other_biz = self._other_shop()
        other_cat = Category.objects.create(business=other_biz, name='Phones')
        other_product = Product.objects.create(
            business=other_biz, category=other_cat, name='Other Phone',
            stock_quantity=3, purchase_price=Decimal('1000.00'),
            selling_price=Decimal('1200.00'), is_imei_tracked=True)
        other_device = MobileDevice.objects.create(
            business=other_biz, product=other_product,
            imei_1='490154203237599', status='IN_STOCK')

        res = self.client.post('/api/pos/checkout/', {
            'customer_id': self.customer.id,
            'payment_method': 'CASH',
            'paid_amount': 1200,
            'items': [{'product_id': self.imei_product.id, 'quantity': 1,
                       'unit_price': 1200, 'discount': 0,
                       'device_id': other_device.id}],
        }, format='json')
        self.assertEqual(res.status_code, 400, res.data)
        self.assertIn('does not exist', res.data['error'])
        other_device.refresh_from_db()
        self.assertEqual(other_device.status, 'IN_STOCK')

    def test_nonexistent_device_id_is_rejected(self):
        res = self._checkout(
            self._imei_line(device_id=999999), paid_amount=16500,
            payment_method='CASH')
        self.assertEqual(res.status_code, 400, res.data)
        self.assertEqual(Sale.objects.count(), 0)

    def test_rejected_checkout_writes_nothing(self):
        before_movements = StockMovement.objects.count()
        res = self._checkout(
            [{'product_id': self.bulk_product.id, 'quantity': 99,
              'unit_price': 150, 'discount': 0}],
            paid_amount=999999, payment_method='CASH')
        self.assertEqual(res.status_code, 400, res.data)
        self.assertIn('Insufficient stock', res.data['error'])

        self.assertEqual(Sale.objects.count(), 0)
        self.assertEqual(SaleItem.objects.count(), 0)
        self.assertEqual(Payment.objects.count(), 0)
        self.assertEqual(StockMovement.objects.count(), before_movements)
        self.bulk_product.refresh_from_db()
        self.assertEqual(self.bulk_product.stock_quantity, 10)


class ServerTotalsTest(Phase13TestBase):
    def test_totals_are_recomputed_server_side_with_decimal_precision(self):
        # Client sends honest unit price 149.99 x3 with a 0.49 line discount
        # and a 10.00 bill discount + 18.05 tax — every total must come from
        # the server's Decimal arithmetic, not from client floats.
        res = self.client.post('/api/pos/checkout/', {
            'customer_id': self.customer.id,
            'payment_method': 'CASH',
            'discount': '10.00',
            'tax': '18.05',
            'paid_amount': 400,
            'items': [{'product_id': self.bulk_product.id, 'quantity': 3,
                       'unit_price': '149.99', 'discount': '0.49'}],
        }, format='json')
        self.assertEqual(res.status_code, 201, res.data)
        sale = Sale.objects.get()
        # 149.99 * 3 - 0.49 = 449.48 ; total = 449.48 - 10 + 18.05 = 457.53
        self.assertEqual(sale.subtotal, Decimal('449.48'))
        self.assertEqual(sale.discount, Decimal('10.00'))
        self.assertEqual(sale.tax_amount, Decimal('18.05'))
        self.assertEqual(sale.total_amount, Decimal('457.53'))
        self.assertEqual(sale.paid_amount, Decimal('400.00'))
        self.assertEqual(sale.due_amount, Decimal('57.53'))
        self.assertEqual(sale.items.get().total_price, Decimal('449.48'))

    def test_padded_paid_amount_is_clamped_to_bill_total(self):
        # Client claims to pay more than the bill is worth (or than it sent)
        # — the server must clamp, never record money that was not billed.
        res = self._checkout(
            [{'product_id': self.bulk_product.id, 'quantity': 1,
              'unit_price': 150, 'discount': 0}],
            paid_amount=Decimal('99999.00'), payment_method='CASH')
        self.assertEqual(res.status_code, 201, res.data)
        sale = Sale.objects.get()
        self.assertEqual(sale.total_amount, Decimal('150.00'))
        self.assertEqual(sale.paid_amount, Decimal('150.00'))
        self.assertEqual(sale.due_amount, Decimal('0.00'))
        # Exactly one payment row for the billed amount, not the padded one.
        self.assertEqual(Payment.objects.count(), 1)
        self.assertEqual(Payment.objects.get().amount, Decimal('150.00'))

    def test_negative_line_total_is_rejected(self):
        # A line discount larger than the line price must not create a
        # negative-priced bill through unsigned math.
        res = self._checkout(
            [{'product_id': self.bulk_product.id, 'quantity': 1,
              'unit_price': 100, 'discount': 500}],
            paid_amount=0, payment_method='CREDIT')
        self.assertEqual(res.status_code, 400, res.data)
        self.assertEqual(Sale.objects.count(), 0)


class LedgerImmutabilityTest(Phase13TestBase):
    def test_outstanding_due_is_derived_from_history(self):
        # 16,500 billed, 10,000 paid at checkout -> due 6,500.
        res = self._checkout(self._imei_line(), payment_method='UPI',
                             paid_amount=10000)
        self.assertEqual(res.status_code, 201, res.data)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.get_total_sales(), Decimal('16500.00'))
        self.assertEqual(self.customer.get_total_paid(), Decimal('10000.00'))
        self.assertEqual(self.customer.get_outstanding_due(), Decimal('6500.00'))

    def test_overpayment_is_rejected_and_books_do_not_drift(self):
        self._checkout(self._imei_line(), payment_method='UPI',
                       paid_amount=10000)
        res = self.client.post('/api/payments/customer/', {
            'customer_id': self.customer.id,
            'amount': 20000,   # more than the 6,500 outstanding
            'payment_method': 'CASH',
        }, format='json')
        self.assertEqual(res.status_code, 400, res.data)
        self.assertIn('exceeds', res.data['error'])
        self.assertEqual(Payment.objects.count(), 1)  # only the checkout row
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.get_outstanding_due(), Decimal('6500.00'))

    def test_payment_closes_due_and_settles_bill_rows(self):
        self._checkout(self._imei_line(), payment_method='UPI',
                       paid_amount=10000)
        sale = Sale.objects.get()
        res = self.client.post('/api/payments/customer/', {
            'customer_id': self.customer.id,
            'amount': 6500,
            'payment_method': 'CASH',
        }, format='json')
        self.assertEqual(res.status_code, 201, res.data)
        self.assertEqual(res.data['remaining_due'], 0.0)

        # The ledger balance closed AND the bill now reflects the settlement
        # (this was the reported bug: bills kept showing "due" on customers
        # who had paid in full). The audit trail stays in the Payment rows,
        # each checkout payment still tagged with its invoice reference.
        sale.refresh_from_db()
        self.assertEqual(sale.paid_amount, Decimal('16500.00'))
        self.assertEqual(sale.due_amount, Decimal('0.00'))
        self.assertEqual(sale.payment_status, 'PAID')
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.get_outstanding_due(), Decimal('0.00'))
        self.assertEqual(self.customer.get_total_paid(), Decimal('16500.00'))
        checkout_payment = Sale.objects.get().payments.get()
        self.assertEqual(
            checkout_payment.reference_number, f"INV-PAY-{sale.invoice_number}")

    def test_credit_sale_records_no_payment_row(self):
        res = self._checkout(self._imei_line(), payment_method='CREDIT',
                             paid_amount=0)
        self.assertEqual(res.status_code, 201, res.data)
        sale = Sale.objects.get()
        self.assertEqual(sale.paid_amount, Decimal('0.00'))
        self.assertEqual(sale.due_amount, Decimal('16500.00'))
        self.assertEqual(Payment.objects.count(), 0)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.get_outstanding_due(), Decimal('16500.00'))


class DecimalFieldStorageTest(Phase13TestBase):
    def test_money_columns_stay_exact_not_float_rounded(self):
        res = self._checkout(
            [{'product_id': self.bulk_product.id, 'quantity': 3,
              'unit_price': '149.99', 'discount': 0}],
            paid_amount=450, payment_method='CASH')
        self.assertEqual(res.status_code, 201, res.data)
        sale = Sale.objects.get()
        self.assertEqual(sale.subtotal, Decimal('449.97'))
        self.assertEqual(str(sale.subtotal), '449.97')
        # DRF serializes Decimal as an exact string, never a rounded float.
        self.assertEqual(res.data['sale']['subtotal'], '449.97')
        self.assertEqual(res.data['sale']['total_amount'], '449.97')
