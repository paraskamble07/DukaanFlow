"""Phase 8 — Backup & Restore tests.

Covers: owner-only access, tenant isolation of exports, round-trip
backup/restore into an empty shop, server-side financial recomputation,
overpayment rejection, idempotent re-restore, and dry-run behaviour.

All data is synthetic test data (never production data).
"""
import json
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import UserProfile
from businesses.models import Business
from customers.models import Customer
from expenses.models import Expense, ExpenseCategory
from inventory.models import MobileDevice, StockMovement
from payments.models import Payment
from products.models import Category, Product
from purchases.models import Purchase, PurchaseItem
from reminders.models import ReminderLog, ReminderSetting
from sales.models import Sale, SaleItem
from suppliers.models import Supplier


class BackupTestBase(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Source shop: owner + a fully populated shop.
        self.user = User.objects.create_user(
            username='backup_owner@dukaanflow.com',
            email='backup_owner@dukaanflow.com',
            password='Password123!',
            first_name='Vikas',
        )
        self.business = Business.objects.create(
            owner=self.user,
            name='Vikas Mobile Hub',
            owner_name='Vikas',
            phone='9811223344',
            email='backup_owner@dukaanflow.com',
            address='Shop 12, FC Road',
            city='Pune', state='Maharashtra', pincode='411002',
            gstin='27ABCDE1234F1Z5', upi_id='vikas@okhdfc',
            invoice_prefix='SZ-', next_invoice_number=1005,
        )
        self.profile = UserProfile.objects.create(
            user=self.user, business=self.business, phone='9811223344', role='OWNER')
        self._login('backup_owner@dukaanflow.com', 'Password123!')
        self._seed_source_shop()

    def _login(self, email, password):
        res = self.client.post('/api/auth/login/',
                               {'email': email, 'password': password}, format='json')
        self.assertEqual(res.status_code, 200, res.data)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {res.data['tokens']['access']}")

    def _seed_source_shop(self):
        b = self.business
        self.category = Category.objects.create(business=b, name='Smartphones')
        self.expense_category = ExpenseCategory.objects.create(
            business=b, name='Shop Rent')
        self.supplier = Supplier.objects.create(
            business=b, name='Ravi', company_name='Ravi Distributors',
            phone='9123456780', gstin='27XYZW5678K1Z2')
        self.customer = Customer.objects.create(
            business=b, name='Sneha Patil', phone='9876543210',
            credit_limit=Decimal('5000.00'))
        self.product = Product.objects.create(
            business=b, category=self.category, name='Redmi Note 13 Pro',
            brand='Xiaomi', sku='RN13PRO-128', barcode='8901234567890',
            purchase_price=Decimal('18000.00'), selling_price=Decimal('22000.00'),
            stock_quantity=5, min_stock=2, warranty_months=12,
            is_imei_tracked=True)
        self.product2 = Product.objects.create(
            business=b, category=self.category, name='USB-C Charger',
            sku='CHG-65W', purchase_price=Decimal('400.00'),
            selling_price=Decimal('699.00'), stock_quantity=20)

        self.purchase = Purchase.objects.create(
            business=b, supplier=self.supplier, invoice_number='PO-1001',
            purchase_date='2026-09-02', total_amount=Decimal('18400.00'),
            paid_amount=Decimal('18400.00'), payment_method='BANK')
        PurchaseItem.objects.create(
            purchase=self.purchase, product=self.product, quantity=1,
            unit_cost=Decimal('18000.00'))
        PurchaseItem.objects.create(
            purchase=self.purchase, product=self.product2, quantity=1,
            unit_cost=Decimal('400.00'))

        # Sale: 1 phone + 1 charger, shop-level discount, paid partially.
        self.sale = Sale.objects.create(
            business=b, customer=self.customer, invoice_number='SZ-1001',
            subtotal=Decimal('22699.00'), discount=Decimal('500.00'),
            tax_amount=Decimal('0.00'), total_amount=Decimal('22199.00'),
            paid_amount=Decimal('20000.00'), payment_method='UPI',
            sale_date='2026-09-05T10:30:00+00:00')
        SaleItem.objects.create(
            sale=self.sale, product=self.product, quantity=1,
            unit_price=Decimal('22000.00'), discount=Decimal('0.00'))
        SaleItem.objects.create(
            sale=self.sale, product=self.product2, quantity=1,
            unit_price=Decimal('699.00'), discount=Decimal('0.00'))
        Payment.objects.create(
            business=b, payment_type='CUSTOMER_PAYMENT', customer=self.customer,
            sale=self.sale, amount=Decimal('20000.00'), payment_method='UPI',
            payment_date='2026-09-05', reference_number='UTR887766')

        self.expense = Expense.objects.create(
            business=b, category=self.expense_category, title='October Rent',
            amount=Decimal('25000.00'), payment_method='BANK',
            expense_date='2026-10-01')

        self.device = MobileDevice.objects.create(
            business=b, product=self.product, imei_1='869911223344556',
            imei_2='869911223344557', model_name='Note 13 Pro 128GB',
            purchase_price=Decimal('18000.00'), selling_price=Decimal('22000.00'),
            status='IN_STOCK')

        StockMovement.objects.create(
            business=b, product=self.product2, movement_type='ADJUSTMENT',
            quantity=-1, previous_stock=21, new_stock=20,
            notes='Audit correction')

        self.reminder_settings = ReminderSetting.objects.create(
            business=b, credit_days=45, due_soon_days=10)
        ReminderLog.objects.create(
            business=b, customer=self.customer, sale=self.sale,
            amount=Decimal('2199.00'), channel='WHATSAPP',
            reminder_status='OVERDUE', sent_by=self.user)

    def _export(self):
        res = self.client.get('/api/backup/')
        self.assertEqual(res.status_code, 200, res.data)
        return res

    def _fresh_target_shop(self, suffix=''):
        """A second, EMPTY shop owned by a different user (restore target)."""
        target_user = User.objects.create_user(
            username=f'restore_owner{suffix}@dukaanflow.com',
            email=f'restore_owner{suffix}@dukaanflow.com',
            password='Password123!', first_name='Neha')
        target = Business.objects.create(
            owner=target_user, name='Neha Connect',
            owner_name='Neha', phone='9110002200',
            email=f'restore_owner{suffix}@dukaanflow.com')
        UserProfile.objects.create(
            user=target_user, business=target, phone='9110002200', role='OWNER')
        return target_user, target


class BackupExportTest(BackupTestBase):
    def test_export_contains_every_section(self):
        payload = self._export().data
        for section in (
                'business', 'categories', 'expense_categories', 'suppliers',
                'customers', 'products', 'purchases', 'sales', 'expenses',
                'payments', 'mobile_devices', 'stock_movements', 'reminder_logs',
                'reminder_settings'):
            self.assertIn(section, payload, f'Missing section {section}')
        self.assertEqual(payload['business']['name'], 'Vikas Mobile Hub')
        self.assertEqual(payload['business']['upi_id'], 'vikas@okhdfc')
        self.assertEqual(payload['business']['next_invoice_number'], 1005)
        self.assertEqual(len(payload['categories']), 1)
        self.assertEqual(len(payload['suppliers']), 1)
        self.assertEqual(len(payload['customers']), 1)
        self.assertEqual(len(payload['products']), 2)
        self.assertEqual(len(payload['purchases']), 1)
        self.assertEqual(len(payload['purchases'][0]['items']), 2)
        self.assertEqual(len(payload['sales']), 1)
        self.assertEqual(len(payload['sales'][0]['items']), 2)
        self.assertEqual(len(payload['expenses']), 1)
        self.assertEqual(len(payload['payments']), 1)
        self.assertEqual(len(payload['mobile_devices']), 1)
        self.assertEqual(len(payload['stock_movements']), 1)
        self.assertEqual(len(payload['reminder_logs']), 1)
        self.assertEqual(payload['reminder_settings']['credit_days'], 45)

    def test_export_has_download_filename_and_version(self):
        res = self._export()
        self.assertEqual(res['Content-Type'], 'application/json')
        disposition = res['Content-Disposition']
        self.assertIn('attachment', disposition)
        self.assertIn('.json', disposition)
        self.assertEqual(res.data['meta']['backup_version'], 1)
        self.assertEqual(res.data['meta']['app'], 'ShopZen')

    def test_export_never_contains_credentials_or_server_state(self):
        raw = json.dumps(self._export().data).lower()
        self.assertNotIn('password', raw)
        self.assertNotIn('token', raw)
        self.assertNotIn('secret', raw)
        # Plan/subscription lifecycle is server-managed: never exported.
        self.assertNotIn('plan_tier', raw)
        self.assertNotIn('subscription_status', raw)

    def test_export_is_owner_only(self):
        staff_user = User.objects.create_user(
            username='staff_backup@dukaanflow.com',
            email='staff_backup@dukaanflow.com', password='Password123!')
        UserProfile.objects.create(
            user=staff_user, business=self.business, role='STAFF',
            permissions=['sales'])
        staff_client = APIClient()
        res = staff_client.post('/api/auth/login/',
                                {'email': 'staff_backup@dukaanflow.com',
                                 'password': 'Password123!'}, format='json')
        staff_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {res.data['tokens']['access']}")
        res = staff_client.get('/api/backup/')
        self.assertEqual(res.status_code, 403)

        anonymous = APIClient()
        self.assertEqual(anonymous.get('/api/backup/').status_code, 401)

    def test_export_is_tenant_isolated(self):
        """A second shop's rows must never leak into this shop's export."""
        _, other_business = self._fresh_target_shop('_other')
        Supplier.objects.create(
            business=other_business, name='Other', company_name='Other Traders',
            phone='9000000000')
        payload = self._export().data
        for sup in payload['suppliers']:
            self.assertNotEqual(sup['company_name'], 'Other Traders')
        self.assertNotIn('Other Traders', json.dumps(payload))


class BackupRestoreTest(BackupTestBase):
    def _restore(self, payload, **kwargs):
        data = dict(payload)
        data.update(kwargs)
        return self.client.post('/api/backup/restore/', data, format='json')

    def test_round_trip_restores_every_record(self):
        export = self._export().data
        target_user, target = self._fresh_target_shop()
        self._login('restore_owner@dukaanflow.com', 'Password123!')

        res = self._restore(export)
        self.assertEqual(res.status_code, 200, res.data)
        imported = res.data['imported']
        self.assertEqual(imported['categories'], 1)
        self.assertEqual(imported['expense_categories'], 1)
        self.assertEqual(imported['suppliers'], 1)
        self.assertEqual(imported['customers'], 1)
        self.assertEqual(imported['products'], 2)
        self.assertEqual(imported['purchases'], 1)
        self.assertEqual(imported['sales'], 1)
        self.assertEqual(imported['expenses'], 1)
        self.assertEqual(imported['payments'], 1)
        self.assertEqual(imported['mobile_devices'], 1)
        self.assertEqual(imported['stock_movements'], 1)
        self.assertEqual(imported['reminder_logs'], 1)
        self.assertEqual(imported['reminder_settings'], 1)
        self.assertGreaterEqual(imported['business_settings'], 1)

        # Everything landed in the TARGET business, never the source.
        self.assertEqual(Customer.objects.filter(business=target).count(), 1)
        self.assertEqual(Product.objects.filter(business=target).count(), 2)
        self.assertEqual(Sale.objects.filter(business=target).count(), 1)
        self.assertEqual(Supplier.objects.filter(business=target).count(), 1)
        self.assertEqual(Purchase.objects.filter(business=target).count(), 1)
        self.assertEqual(Payment.objects.filter(business=target).count(), 1)
        self.assertEqual(Customer.objects.filter(business=self.business).count(), 1)
        self.assertEqual(Sale.objects.filter(business=self.business).count(), 1)

        restored_sale = Sale.objects.get(business=target, invoice_number='SZ-1001')
        # Financial values recomputed server-side from the line items.
        self.assertEqual(restored_sale.subtotal, Decimal('22699.00'))
        self.assertEqual(restored_sale.total_amount, Decimal('22199.00'))
        self.assertEqual(restored_sale.due_amount, Decimal('2199.00'))
        self.assertEqual(restored_sale.payment_status, 'PARTIAL')
        self.assertEqual(restored_sale.items.count(), 2)
        # Payment linked back to the restored sale.
        self.assertEqual(Payment.objects.get(business=target).sale,
                         restored_sale)

        restored_purchase = Purchase.objects.get(
            business=target, invoice_number='PO-1001')
        self.assertEqual(restored_purchase.total_amount, Decimal('18400.00'))
        self.assertEqual(restored_purchase.due_amount, Decimal('0.00'))
        self.assertEqual(restored_purchase.items.count(), 2)

        # Business settings carried over...
        target.refresh_from_db()
        self.assertEqual(target.name, 'Vikas Mobile Hub')
        self.assertEqual(target.upi_id, 'vikas@okhdfc')
        self.assertEqual(target.gstin, '27ABCDE1234F1Z5')
        self.assertEqual(target.next_invoice_number, 1005)
        # ...but the owner, plan and subscription lifecycle are untouched.
        self.assertEqual(target.owner, target_user)
        self.assertEqual(target.subscription_status, 'ACTIVE')

        self.assertEqual(
            MobileDevice.objects.get(business=target).imei_1,
            '869911223344556')
        self.assertEqual(
            ReminderSetting.objects.get(business=target).credit_days, 45)
        self.assertEqual(ReminderLog.objects.filter(business=target).count(), 1)

    def test_restore_is_idempotent(self):
        export = self._export().data
        _, target = self._fresh_target_shop()
        self._login('restore_owner@dukaanflow.com', 'Password123!')
        first = self._restore(export)
        self.assertEqual(first.status_code, 200, first.data)
        second = self._restore(export)
        self.assertEqual(second.status_code, 200, second.data)
        self.assertEqual(second.data['imported'], {})
        self.assertEqual(second.data['skipped']['sales'], 1)
        self.assertEqual(second.data['skipped']['products'], 2)
        self.assertEqual(second.data['skipped']['customers'], 1)
        # Exactly one copy of every row: the source shop's, plus the target's.
        self.assertEqual(Sale.objects.count(), 2)
        self.assertEqual(Product.objects.count(), 4)
        self.assertEqual(Customer.objects.count(), 2)
        self.assertEqual(Payment.objects.count(), 2)
        self.assertEqual(SaleItem.objects.count(), 4)
        self.assertEqual(Sale.objects.filter(business=target).count(), 1)
        self.assertEqual(SaleItem.objects.filter(
            sale__business=target).count(), 2)

    def test_dry_run_writes_nothing(self):
        export = self._export().data
        self._fresh_target_shop()
        self._login('restore_owner@dukaanflow.com', 'Password123!')
        res = self._restore(export, dry_run=True)
        self.assertEqual(res.status_code, 200, res.data)
        self.assertTrue(res.data['dry_run'])
        self.assertEqual(res.data['imported']['sales'], 1)  # previewed...
        # ...but nothing was written to the target shop.
        self.assertEqual(Sale.objects.exclude(business=self.business).count(), 0)
        self.assertEqual(Product.objects.exclude(business=self.business).count(), 0)
        self.assertEqual(Customer.objects.exclude(business=self.business).count(), 0)

    def test_rejects_overpayment(self):
        """paid > recomputed total must reject the whole backup."""
        export = self._export().data
        export['sales'][0]['paid_amount'] = '999999.00'  # > 22199.00
        self._fresh_target_shop()
        self._login('restore_owner@dukaanflow.com', 'Password123!')
        res = self._restore(export)
        self.assertEqual(res.status_code, 400)
        self.assertIn('overpayment', str(res.data).lower())
        # Nothing was written.
        self.assertEqual(Sale.objects.exclude(business=self.business).count(), 0)
        self.assertEqual(Customer.objects.count(), 1)

    def test_recomputes_totals_from_items(self):
        """A tampered file total must never be used unchanged."""
        export = self._export().data
        export['sales'][0]['total_amount'] = '5.00'  # tampered
        self._fresh_target_shop()
        self._login('restore_owner@dukaanflow.com', 'Password123!')
        res = self._restore(export)
        self.assertEqual(res.status_code, 200, res.data)
        self.assertEqual(res.data['adjusted']['sales'], 1)
        restored = Sale.objects.exclude(business=self.business).get()
        self.assertEqual(restored.total_amount, Decimal('22199.00'))
        self.assertEqual(restored.due_amount, Decimal('2199.00'))

    def test_rejects_unknown_backup_version(self):
        export = self._export().data
        export['meta']['backup_version'] = 999
        res = self._restore(export)
        self.assertEqual(res.status_code, 400)
        self.assertIn('version', str(res.data).lower())

    def test_restore_never_touches_other_shops(self):
        """Restoring into shop A must never touch another shop's rows."""
        export = self._export().data
        _, target = self._fresh_target_shop()
        _, third = self._fresh_target_shop('_third')
        self._login('restore_owner@dukaanflow.com', 'Password123!')
        res = self._restore(export)
        self.assertEqual(res.status_code, 200, res.data)
        self.assertEqual(Sale.objects.filter(business=third).count(), 0)
        self.assertEqual(Customer.objects.filter(business=third).count(), 0)
        self.assertEqual(Sale.objects.filter(business=target).count(), 1)

    def test_restore_requires_owner(self):
        export = self._export().data
        staff_user = User.objects.create_user(
            username='staff_restore@dukaanflow.com',
            email='staff_restore@dukaanflow.com', password='Password123!')
        UserProfile.objects.create(
            user=staff_user, business=self.business, role='STAFF',
            permissions=['settings'])
        staff_client = APIClient()
        res = staff_client.post('/api/auth/login/',
                                {'email': 'staff_restore@dukaanflow.com',
                                 'password': 'Password123!'}, format='json')
        staff_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {res.data['tokens']['access']}")
        res = staff_client.post('/api/backup/restore/', export, format='json')
        self.assertEqual(res.status_code, 403)

    def test_restore_missing_customer_is_reported_not_silent(self):
        export = self._export().data
        # Orphan both the sale's and the payment's customer references.
        export['sales'][0]['customer_phone'] = '0000000000'
        export['sales'][0]['customer_name'] = 'Nobody'
        export['payments'][0]['customer_phone'] = '0000000000'
        export['payments'][0]['customer_name'] = 'Nobody'
        self._fresh_target_shop()
        self._login('restore_owner@dukaanflow.com', 'Password123!')
        res = self._restore(export)
        self.assertEqual(res.status_code, 200, res.data)
        # Neither the unattributed sale nor the unattributed payment is faked.
        self.assertEqual(res.data['skipped']['sales'], 1)
        self.assertEqual(res.data['skipped']['payments'], 1)
        self.assertTrue(any('customer' in w.lower() for w in res.data['warnings']))
        self.assertEqual(Sale.objects.exclude(business=self.business).count(), 0)
        self.assertEqual(Payment.objects.exclude(business=self.business).count(), 0)
