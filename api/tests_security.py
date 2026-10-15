"""Security and permission test suite.

Covers (per the ShopZen PRD):
  * Employee role restrictions — a STAFF user must NOT receive purchase
    price, supplier cost, profit/margin, expenses or owner financial
    reports through the API (not merely hidden in Flutter).
  * Tenant isolation / IDOR — Shop B must not read, modify or delete
    Shop A's records by manipulating IDs.
  * Password reset — secure token, expiry, single use, session
    invalidation, and no email-enumeration hint.
  * Owner-Locked endpoints — shop settings stay accessible to the owner
    while employees are denied.

These tests call the REST API directly with JWT bearer tokens.
"""

from decimal import Decimal
from datetime import timedelta

from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APIClient

from businesses.models import Business
from accounts.models import UserProfile
from products.models import Product, Category
from customers.models import Customer
from sales.models import Sale, SaleItem
from suppliers.models import Supplier
from expenses.models import Expense, ExpenseCategory


def login_client(client, email, password):
    """Login and attach the JWT bearer token to `client`."""
    res = client.post('/api/auth/login/',
                      {'email': email, 'password': password},
                      format='json')
    assert res.status_code == 200, f'login failed for {email}: {res.status_code}'
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {res.data['tokens']['access']}")
    return res.data['tokens']['access']


def make_shop(suffix, owner_name, plan='PRO'):
    """Create an owner + business + profile and return (user, business)."""
    email = f'{suffix}@shopzen.test'
    user = User.objects.create_user(
        username=email, email=email, password='Password123!',
        first_name=owner_name)
    business = Business.objects.create(
        owner=user, name=f'{owner_name} Store', owner_name=owner_name,
        phone='9876500000', email=email, plan_tier=plan)
    UserProfile.objects.create(user=user, business=business,
                               phone='9876500000', role='OWNER')
    return user, business


def refresh_user(user):
    """reload the cached userprofile so fields written by the API
    (e.g. the reset token) are visible to the test."""
    user.refresh_from_db()


def add_staff(business, name, permissions):
    """Create a STAFF account on `business` with explicit module grants."""
    email = f'staff.{business.id}.{name}@shopzen.test'
    user = User.objects.create_user(
        username=email, email=email, password='Password123!',
        first_name=name)
    UserProfile.objects.create(user=user, business=business,
                               phone='9876500001', role='STAFF',
                               permissions=permissions)
    return user


# ---------------------------------------------------------------------------
# 1. Employee permission restrictions (PRD §5, §11, §17, §72)
# ---------------------------------------------------------------------------
class EmployeePermissionTest(TestCase):
    """A STAFF user with only POS/customer access must not see owner
    financial data — the API itself must withhold it."""

    def setUp(self):
        self.client = APIClient()
        self.owner, self.business = make_shop('emp', 'Ravi')

        self.cat = Category.objects.create(business=self.business, name='Mobiles')
        self.product = Product.objects.create(
            business=self.business, category=self.cat, name='Vivo V29',
            purchase_price=Decimal('22000.00'),
            selling_price=Decimal('26500.00'),
            stock_quantity=15, min_stock=5)
        self.supplier = Supplier.objects.create(
            business=self.business, company_name='Vivo Distributor',
            name='Vivek', phone='9810000000', email='v@vivo.test',
            address='Mumbai', gstin='27AAAAA0000A1Z5')

        # Employee granted sales + customers + products only — the typical
        # counter-staff configuration from the PRD.
        self.staff = add_staff(self.business, 'Amit',
                               ['sales', 'customers', 'products'])
        self.staff_client = APIClient()
        login_client(self.staff_client, self.staff.username, 'Password123!')

        self.owner_client = APIClient()
        login_client(self.owner_client, self.owner.username, 'Password123!')

    def test_employee_cannot_see_purchase_price(self):
        """PRD §11: purchase_price must be withheld by the backend."""
        res = self.staff_client.get('/api/products/')
        self.assertEqual(res.status_code, 200)
        rows = res.data.get('results', res.data)
        for row in rows:
            self.assertIsNone(row.get('purchase_price'),
                              'purchase_price leaked to employee in list')
            self.assertIsNone(row.get('profit_margin'),
                              'profit_margin leaked to employee in list')

    def test_employee_cannot_see_purchase_price_in_detail(self):
        res = self.staff_client.get(f'/api/products/{self.product.id}/')
        self.assertEqual(res.status_code, 200)
        self.assertIsNone(res.data.get('purchase_price'))
        self.assertIsNone(res.data.get('profit_margin'))

    def test_owner_can_see_purchase_price(self):
        res = self.owner_client.get(f'/api/products/{self.product.id}/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data.get('purchase_price'), 22000.00)

    def test_employee_denied_expenses(self):
        cat = ExpenseCategory.objects.create(business=self.business, name='Rent')
        Expense.objects.create(business=self.business, category=cat,
                               title='Shop rent',
                               amount=Decimal('15000'),
                               payment_method='CASH',
                               expense_date=timezone.now().date())
        res = self.staff_client.get('/api/expenses/')
        self.assertEqual(res.status_code, 403,
                         'employee must not list expenses')

    def test_employee_denied_expense_reports(self):
        res = self.staff_client.get('/api/reports/expenses/')
        self.assertEqual(res.status_code, 403)

    def test_employee_denied_supplier_module(self):
        res = self.staff_client.get('/api/suppliers/')
        self.assertEqual(res.status_code, 403,
                         'employee must not list suppliers (cost data)')

    def test_employee_denied_supplier_payments(self):
        res = self.staff_client.post('/api/payments/supplier/', {
            'supplier_id': self.supplier.id, 'amount': '1000',
            'payment_method': 'CASH'}, format='json')
        self.assertIn(res.status_code, (403, 400))

    def test_employee_denied_business_settings(self):
        """Shop settings (GST/UPI/invoice prefs) are owner-only."""
        res = self.staff_client.get('/api/business/settings/')
        self.assertEqual(res.status_code, 403)

    def test_employee_denied_profit_and_loss_report(self):
        res = self.staff_client.get('/api/reports/profit-loss/')
        self.assertEqual(res.status_code, 403)

    def test_employee_with_grant_can_access_granted_module(self):
        """A staff member granted 'customers' CAN use the customer API —
        least-privilege must not accidentally lock out valid access."""
        Customer.objects.create(business=self.business, name='Suresh',
                                phone='9811112222')
        res = self.staff_client.get('/api/customers/')
        self.assertEqual(res.status_code, 200)

    def test_employee_without_grant_denied_customer_module(self):
        """Zero-grant staff default to no modules (least privilege)."""
        bare = add_staff(self.business, 'Zero', [])
        c = APIClient()
        login_client(c, bare.username, 'Password123!')
        res = c.get('/api/customers/')
        self.assertEqual(res.status_code, 403)

    def test_employee_cannot_change_own_permissions(self):
        """The permissions JSONField is not exposed as an editable field —
        only the owner (or Django admin) may change grants."""
        res = self.staff_client.put('/api/auth/profile/', {
            'permissions': ['expenses', 'reports', 'settings']},
            format='json')
        self.staff.refresh_from_db()
        self.assertEqual(self.staff.userprofile.permissions,
                         ['sales', 'customers', 'products'])


# ---------------------------------------------------------------------------
# 2. Tenant isolation / IDOR (PRD §6, §73)
# ---------------------------------------------------------------------------
class TenantIsolationTest(TestCase):
    def setUp(self):
        self.shop_a_user, self.shop_a = make_shop('shopa', 'Kiran')
        self.shop_b_user, self.shop_b = make_shop('shopb', 'Megha')

        self.cat = Category.objects.create(business=self.shop_a, name='Audio')
        self.product_a = Product.objects.create(
            business=self.shop_a, category=self.cat, name='Boat Rockerz',
            purchase_price=Decimal('1200'), selling_price=Decimal('1999'),
            stock_quantity=20)
        self.customer_a = Customer.objects.create(
            business=self.shop_a, name='Rahul', phone='9811112222')
        self.supplier_a = Supplier.objects.create(
            business=self.shop_a, company_name='Audio Wholesale',
            name='Ashok', phone='9833334444', email='a@audio.test',
            address='Pune', gstin='27BBBBB1111B1Z2')

        # Shop B is fully authenticated and has its own valid records.
        self.client_b = APIClient()
        login_client(self.client_b, self.shop_b_user.username, 'Password123!')
        self.client_a = APIClient()
        login_client(self.client_a, self.shop_a_user.username, 'Password123!')

    def test_shop_b_cannot_read_shop_a_product(self):
        res = self.client_b.get(f'/api/products/{self.product_a.id}/')
        self.assertEqual(res.status_code, 404)

    def test_shop_b_cannot_list_shop_a_products(self):
        res = self.client_b.get('/api/products/')
        self.assertEqual(res.status_code, 200)
        rows = res.data.get('results', res.data)
        for row in rows:
            self.assertNotEqual(row['id'], self.product_a.id)

    def test_shop_b_cannot_modify_shop_a_product(self):
        res = self.client_b.patch(f'/api/products/{self.product_a.id}/',
                                  {'selling_price': '1'}, format='json')
        self.assertIn(res.status_code, (403, 404))
        self.product_a.refresh_from_db()
        self.assertEqual(self.product_a.selling_price, Decimal('1999'))

    def test_shop_b_cannot_delete_shop_a_product(self):
        res = self.client_b.delete(f'/api/products/{self.product_a.id}/')
        self.assertIn(res.status_code, (403, 404))
        self.assertTrue(Product.objects.filter(id=self.product_a.id).exists())

    def test_shop_b_cannot_read_or_edit_shop_a_customer(self):
        url = f'/api/customers/{self.customer_a.id}/'
        self.assertEqual(self.client_b.get(url).status_code, 404)
        res = self.client_b.patch(url, {'name': 'Hacker'}, format='json')
        self.assertIn(res.status_code, (403, 404))
        self.customer_a.refresh_from_db()
        self.assertEqual(self.customer_a.name, 'Rahul')
        self.assertEqual(self.client_b.delete(url).status_code, 404)
        self.assertTrue(Customer.objects.filter(id=self.customer_a.id).exists())

    def test_shop_b_cannot_view_shop_a_customer_ledger(self):
        res = self.client_b.get(
            f'/api/customers/{self.customer_a.id}/ledger/')
        self.assertIn(res.status_code, (403, 404))

    def test_shop_b_cannot_create_sale_for_shop_a_customer(self):
        """Nested-object leakage: POS checkout must reject a foreign
        customer ID even when the payload is otherwise well-formed."""
        res = self.client_b.post('/api/pos/checkout/', {
            'customer_id': self.customer_a.id,
            'items': [{'product_id': self.product_a.id, 'quantity': 1}],
            'paid_amount': '1999', 'payment_method': 'CASH'}, format='json')
        self.assertNotEqual(res.status_code, 201)

    def test_shop_b_cannot_view_shop_a_supplier(self):
        res = self.client_b.get(f'/api/suppliers/{self.supplier_a.id}/')
        self.assertEqual(res.status_code, 404)

    def test_shop_b_reports_do_not_include_shop_a_data(self):
        for endpoint in ('/api/reports/sales/', '/api/reports/stock/',
                         '/api/reports/khata/', '/api/reports/top-products/'):
            res = self.client_b.get(endpoint)
            self.assertEqual(res.status_code, 200)
            body = str(res.data)
            self.assertNotIn('Boat Rockerz', body)
            self.assertNotIn('Rahul', body)


# ---------------------------------------------------------------------------
# 3. Password reset security (PRD §7 / Phase 3)
# ---------------------------------------------------------------------------
class PasswordResetFlowTest(TestCase):
    def setUp(self):
        self.user, self.business = make_shop('reset', 'Deepak')
        self.client = APIClient()

    def _issued_token(self):
        # user.userprofile is cached from setUp; reload to see the token
        # the API actually wrote.
        self.user.refresh_from_db()
        return self.user.userprofile.reset_password_token

    def test_forgot_password_does_not_reveal_unregistered_email(self):
        res = self.client.post('/api/auth/forgot-password/',
                               {'email': 'nobody@nowhere.test'}, format='json')
        self.assertEqual(res.status_code, 200)
        self.assertNotIn('not registered', str(res.data).lower())
        self.assertNotIn('no account', str(res.data).lower())

    def test_forgot_password_issues_token_for_registered_email(self):
        res = self.client.post('/api/auth/forgot-password/',
                               {'email': self.user.email}, format='json')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(self._issued_token())

    def test_reset_with_valid_token_changes_password(self):
        self.client.post('/api/auth/forgot-password/',
                         {'email': self.user.email}, format='json')
        token = self._issued_token()
        res = self.client.post('/api/auth/reset-password/', {
            'token': token, 'new_password': 'NewSecret456!'}, format='json')
        self.assertEqual(res.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewSecret456!'))

    def test_reset_token_is_single_use(self):
        self.client.post('/api/auth/forgot-password/',
                         {'email': self.user.email}, format='json')
        token = self._issued_token()
        self.client.post('/api/auth/reset-password/',
                         {'token': token, 'new_password': 'NewSecret456!'},
                         format='json')
        res = self.client.post('/api/auth/reset-password/',
                               {'token': token, 'new_password': 'Another789!'},
                               format='json')
        self.assertEqual(res.status_code, 400)

    def test_expired_token_is_rejected(self):
        self.user.userprofile.reset_password_token = 'expired-token'
        self.user.userprofile.reset_password_expires = (
            timezone.now() - timedelta(hours=1))
        self.user.userprofile.save()
        res = self.client.post('/api/auth/reset-password/',
                               {'token': 'expired-token',
                                'new_password': 'NewSecret456!'},
                               format='json')
        self.assertEqual(res.status_code, 400)

    def test_short_password_rejected(self):
        self.user.userprofile.reset_password_token = 'tok'
        self.user.userprofile.reset_password_expires = (
            timezone.now() + timedelta(hours=1))
        self.user.userprofile.save()
        res = self.client.post('/api/auth/reset-password/',
                               {'token': 'tok', 'new_password': 'short'},
                               format='json')
        self.assertEqual(res.status_code, 400)

    def test_password_reset_logins_with_old_password_fail(self):
        self.client.post('/api/auth/forgot-password/',
                         {'email': self.user.email}, format='json')
        token = self._issued_token()
        self.client.post('/api/auth/reset-password/',
                         {'token': token, 'new_password': 'NewSecret456!'},
                         format='json')
        res = self.client.post('/api/auth/login/', {
            'email': self.user.email, 'password': 'Password123!'},
            format='json')
        self.assertEqual(res.status_code, 401)


# ---------------------------------------------------------------------------
# 4. Critical khata ledger scenario (PRD §71)
# ---------------------------------------------------------------------------
class KhataLedgerScenarioTest(TestCase):
    """Purchase 10 → stock 10 → sell 2 → stock 8 → pay 4000 → outstanding
    6000 → pay 6000 → outstanding 0 → full history preserved."""

    def setUp(self):
        self.client = APIClient()
        self.owner, self.business = make_shop('khata', 'Sanjay')
        login_client(self.client, self.owner.username, 'Password123!')

        self.cat = Category.objects.create(business=self.business, name='Mobiles')
        self.product = Product.objects.create(
            business=self.business, category=self.cat, name='Realme C55',
            purchase_price=Decimal('8000'), selling_price=Decimal('10000'),
            stock_quantity=0, min_stock=2)
        self.supplier = Supplier.objects.create(
            business=self.business, company_name='Om Telecom',
            name='Om', phone='9812345678', email='om@telecom.test',
            address='Nashik', gstin='27CCCCC2222C1Z3')
        self.customer = Customer.objects.create(
            business=self.business, name='Rahul', phone='9811112222')

    def test_full_purchase_sell_settle_flow(self):
        # Purchase 10 units
        res = self.client.post('/api/purchases/', {
            'supplier_id': self.supplier.id,
            'items': [{'product_id': self.product.id, 'quantity': 10,
                       'unit_cost': '8000'}],
            'paid_amount': '80000', 'payment_method': 'CASH'},
            format='json')
        self.assertEqual(res.status_code, 201)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 10)

        # Record a credit sale of 2 units (₹10,000 each, full due)
        res = self.client.post('/api/pos/checkout/', {
            'customer_id': self.customer.id,
            'items': [{'product_id': self.product.id, 'quantity': 2,
                       'unit_price': '10000'}],
            'paid_amount': '0', 'payment_method': 'CREDIT'},
            format='json')
        self.assertEqual(res.status_code, 201)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 8)

        # Partial payment 4000 → outstanding 16000 - 4000 = 12000
        res = self.client.post('/api/payments/customer/', {
            'customer_id': self.customer.id, 'amount': '4000',
            'payment_method': 'CASH'}, format='json')
        self.assertEqual(res.status_code, 201)
        self.customer.refresh_from_db()
        self.assertEqual(Decimal(str(self.customer.get_outstanding_due())),
                         Decimal('16000'))

        # Final settlement of the remaining 16000 → outstanding 0
        res = self.client.post('/api/payments/customer/', {
            'customer_id': self.customer.id, 'amount': '16000',
            'payment_method': 'UPI'}, format='json')
        self.assertEqual(res.status_code, 201)
        self.customer.refresh_from_db()
        self.assertEqual(Decimal(str(self.customer.get_outstanding_due())),
                         Decimal('0'))

        # Ledger history must remain after balance reaches zero (PRD §18)
        res = self.client.get(f'/api/customers/{self.customer.id}/ledger/')
        self.assertEqual(res.status_code, 200)
        payments = res.data['payments']
        self.assertEqual(len(payments), 2,
                         'ledger history must survive full settlement')
        self.assertEqual(res.data['summary']['outstanding_due'], 0.0)
