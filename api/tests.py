import json
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from businesses.models import Business
from accounts.models import UserProfile
from products.models import Product, Category
from inventory.models import MobileDevice
from customers.models import Customer
from sales.models import Sale

class APILayerIntegrationTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        # 1. Register Shop Owner
        self.user = User.objects.create_user(
            username='api_test@dukaanflow.com',
            email='api_test@dukaanflow.com',
            password='Password123!',
            first_name='Vikas'
        )
        self.business = Business.objects.create(
            owner=self.user,
            name='Vikas Mobile Hub',
            owner_name='Vikas',
            phone='9811223344',
            email='api_test@dukaanflow.com',
            plan_tier='PRO'
        )
        UserProfile.objects.create(user=self.user, business=self.business, phone='9811223344')

        # 2. Login via API to get JWT Token
        login_res = self.client.post('/api/auth/login/', {
            'email': 'api_test@dukaanflow.com',
            'password': 'Password123!'
        }, format='json')
        self.assertEqual(login_res.status_code, 200)
        self.token = login_res.data['tokens']['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        # 3. Create sample category & product
        self.cat = Category.objects.create(business=self.business, name='Smartphones')
        self.product = Product.objects.create(
            business=self.business,
            category=self.cat,
            name='Redmi Note 13 Pro',
            purchase_price=Decimal('18000.00'),
            selling_price=Decimal('22000.00'),
            stock_quantity=5,
            is_imei_tracked=True
        )
        self.device = MobileDevice.objects.create(
            business=self.business,
            product=self.product,
            imei_1='869911223344556',
            purchase_price=Decimal('18000.00'),
            selling_price=Decimal('22000.00'),
            status='IN_STOCK'
        )
        self.customer = Customer.objects.create(
            business=self.business,
            name='Mahesh Sharma',
            phone='9899001122'
        )

    def test_dashboard_api(self):
        res = self.client.get('/api/dashboard/')
        self.assertEqual(res.status_code, 200)
        self.assertIn('today', res.data)
        self.assertIn('receivables', res.data)
        self.assertIn('charts', res.data)

    def test_products_api(self):
        res = self.client.get('/api/products/')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(len(res.data.get('results', res.data)) >= 1)

    def test_imei_lookup_api(self):
        res = self.client.get('/api/inventory/imei/lookup/?imei=869911223344556')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.data['found'])
        self.assertEqual(res.data['device']['imei_1'], '869911223344556')

    def test_pos_checkout_and_khata_api(self):
        payload = {
            'customer_id': self.customer.id,
            'payment_method': 'UPI',
            'discount': 0,
            'tax': 0,
            'paid_amount': 15000, # Bill is 22,000, Paid 15,000 -> Due 7,000
            'items': [
                {
                    'product_id': self.product.id,
                    'quantity': 1,
                    'unit_price': 22000,
                    'discount': 0,
                    'device_id': self.device.id
                }
            ]
        }
        res = self.client.post('/api/pos/checkout/', payload, format='json')
        self.assertEqual(res.status_code, 201)
        self.assertIn('sale', res.data)
        self.assertEqual(Decimal(str(res.data['sale']['due_amount'])), Decimal('7000.00'))

        # Verify Customer Ledger API
        ledger_res = self.client.get(f'/api/customers/{self.customer.id}/ledger/')
        self.assertEqual(ledger_res.status_code, 200)
        self.assertEqual(ledger_res.data['summary']['outstanding_due'], 7000.0)

    def test_profit_loss_report_api(self):
        res = self.client.get('/api/reports/profit-loss/')
        self.assertEqual(res.status_code, 200)
        self.assertIn('gross_profit', res.data)
        self.assertIn('net_profit', res.data)


class TenantIsolationTest(TestCase):
    """CRITICAL: Shop A data must NEVER be visible to Shop B (Requirement #72)."""

    def setUp(self):
        from expenses.models import Expense, ExpenseCategory
        from suppliers.models import Supplier

        self.client_a = APIClient()
        self.client_b = APIClient()

        # Shop A
        self.user_a = User.objects.create_user(
            username='shopa@test.com', email='shopa@test.com',
            password='Password123!', first_name='ShopA Owner'
        )
        self.business_a = Business.objects.create(
            owner=self.user_a, name='Shop A Electronics',
            owner_name='ShopA Owner', phone='9811111111', email='shopa@test.com'
        )
        UserProfile.objects.create(user=self.user_a, business=self.business_a, phone='9811111111')
        self.cat_a = Category.objects.create(business=self.business_a, name='Phones A')
        self.product_a = Product.objects.create(
            business=self.business_a, category=self.cat_a, name='iPhone A',
            purchase_price=Decimal('55000'), selling_price=Decimal('62000'),
            stock_quantity=3
        )
        self.customer_a = Customer.objects.create(
            business=self.business_a, name='Customer A', phone='9822000011'
        )
        self.supplier_a = Supplier.objects.create(
            business=self.business_a, company_name='Supplier A', phone='9833000011'
        )

        # Shop B
        self.user_b = User.objects.create_user(
            username='shopb@test.com', email='shopb@test.com',
            password='Password123!', first_name='ShopB Owner'
        )
        self.business_b = Business.objects.create(
            owner=self.user_b, name='Shop B Mobiles',
            owner_name='ShopB Owner', phone='9844444444', email='shopb@test.com'
        )
        UserProfile.objects.create(user=self.user_b, business=self.business_b, phone='9844444444')
        self.cat_b = Category.objects.create(business=self.business_b, name='Phones B')
        self.product_b = Product.objects.create(
            business=self.business_b, category=self.cat_b, name='Samsung B',
            purchase_price=Decimal('25000'), selling_price=Decimal('29000'),
            stock_quantity=2
        )
        self.customer_b = Customer.objects.create(
            business=self.business_b, name='Customer B', phone='9855000022'
        )

        # Login both shops
        res_a = self.client_a.post('/api/auth/login/', {
            'email': 'shopa@test.com', 'password': 'Password123!'
        }, format='json')
        self.client_a.credentials(HTTP_AUTHORIZATION=f"Bearer {res_a.data['tokens']['access']}")

        res_b = self.client_b.post('/api/auth/login/', {
            'email': 'shopb@test.com', 'password': 'Password123!'
        }, format='json')
        self.client_b.credentials(HTTP_AUTHORIZATION=f"Bearer {res_b.data['tokens']['access']}")

    def test_product_isolation(self):
        """Shop A must see only iPhone A, never Samsung B."""
        res = self.client_a.get('/api/products/')
        results = res.data.get('results', res.data)
        names = [p['name'] for p in results]
        self.assertIn('iPhone A', names)
        self.assertNotIn('Samsung B', names)

    def test_product_idor_blocked(self):
        """Shop A must not fetch Shop B's product by ID (IDOR)."""
        res = self.client_a.get(f'/api/products/{self.product_b.id}/')
        self.assertEqual(res.status_code, 404)

    def test_customer_isolation_and_idor(self):
        res = self.client_a.get('/api/customers/')
        results = res.data.get('results', res.data)
        names = [c['name'] for c in results]
        self.assertIn('Customer A', names)
        self.assertNotIn('Customer B', names)

        res = self.client_a.get(f'/api/customers/{self.customer_b.id}/')
        self.assertEqual(res.status_code, 404)

    def test_supplier_isolation_and_idor(self):
        res = self.client_a.get('/api/suppliers/')
        results = res.data.get('results', res.data)
        names = [s['company_name'] for s in results]
        self.assertIn('Supplier A', names)

        # Shop B supplier doesn't exist for shop A -> 404 via IDOR attempt
        from suppliers.models import Supplier
        supplier_b = Supplier.objects.create(
            business=self.business_b, company_name='Supplier B', phone='9866000033'
        )
        res = self.client_a.get(f'/api/suppliers/{supplier_b.id}/')
        self.assertEqual(res.status_code, 404)

    def test_pos_checkout_cannot_sell_other_shops_product(self):
        """Shop A must not be able to sell Shop B's product via POS."""
        payload = {
            'payment_method': 'CASH',
            'paid_amount': 29000,
            'items': [{'product_id': self.product_b.id, 'quantity': 1, 'unit_price': 29000}]
        }
        res = self.client_a.post('/api/pos/checkout/', payload, format='json')
        self.assertEqual(res.status_code, 400)
        # No sale must have been created for shop A
        from sales.models import Sale
        self.assertEqual(Sale.objects.filter(business=self.business_a).count(), 0)
        # Shop B stock untouched
        self.product_b.refresh_from_db()
        self.assertEqual(self.product_b.stock_quantity, 2)

    def test_dashboard_isolation(self):
        res = self.client_a.get('/api/dashboard/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['inventory']['total_products'], 1)

    def test_reports_isolation(self):
        for endpoint in ['/api/reports/profit-loss/', '/api/reports/sales/',
                         '/api/reports/stock/', '/api/reports/khata/',
                         '/api/reports/expenses/', '/api/reports/gst/']:
            res = self.client_a.get(endpoint)
            self.assertEqual(res.status_code, 200, f'{endpoint} failed')
            if endpoint == '/api/reports/stock/':
                self.assertEqual(res.data['total_products'], 1)

    def test_sale_idor_blocked(self):
        """Shop A creates a sale; Shop B cannot view it."""
        sale = Sale.objects.create(
            business=self.business_a, customer=self.customer_a,
            invoice_number='SZ-A-1001',
            subtotal=Decimal('62000'), total_amount=Decimal('62000'),
            paid_amount=Decimal('62000')
        )
        res = self.client_b.get(f'/api/sales/{sale.id}/')
        self.assertEqual(res.status_code, 404)

    def test_pos_insufficient_stock_rolls_back(self):
        """A failed checkout must leave zero partial writes behind."""
        from sales.models import Sale
        from customers.models import Customer as Cust
        cust, _ = Cust.objects.get_or_create(
            business=self.business_a, phone='0000000000',
            defaults={'name': 'Walk-in / Cash Customer'}
        )
        payload = {
            'customer_id': self.customer_a.id,
            'payment_method': 'CASH',
            'paid_amount': 100000,
            'items': [
                {'product_id': self.product_a.id, 'quantity': 2, 'unit_price': 62000},
                {'product_id': self.product_a.id, 'quantity': 5, 'unit_price': 62000},
            ]
        }
        # Requested 7 units total but only 3 in stock -> must fail cleanly
        res = self.client_a.post('/api/pos/checkout/', payload, format='json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(Sale.objects.filter(business=self.business_a).count(), 0)
        self.product_a.refresh_from_db()
        self.assertEqual(self.product_a.stock_quantity, 3)
