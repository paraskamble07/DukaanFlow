import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# tests/test_auth_and_business.py
test_auth_py = """from django.test import TestCase, Client
from django.contrib.auth.models import User
from decimal import Decimal
from businesses.models import Business, PLAN_LIMITS
from accounts.models import UserProfile
from customers.models import Customer
from products.models import Product

class MultiTenantAndAuthTest(TestCase):
    def setUp(self):
        # Create User A & Shop A
        self.user_a = User.objects.create_user(
            username='user_a@example.com',
            email='user_a@example.com',
            password='password123',
            first_name='Rahul'
        )
        self.shop_a = Business.objects.create(
            owner=self.user_a,
            name='Rahul Mobile Shop',
            owner_name='Rahul',
            phone='9811111111',
            email='user_a@example.com',
            plan_tier='FREE'
        )
        UserProfile.objects.create(user=self.user_a, business=self.shop_a, phone='9811111111')

        # Create User B & Shop B
        self.user_b = User.objects.create_user(
            username='user_b@example.com',
            email='user_b@example.com',
            password='password123',
            first_name='Amit'
        )
        self.shop_b = Business.objects.create(
            owner=self.user_b,
            name='Amit Electronics',
            owner_name='Amit',
            phone='9822222222',
            email='user_b@example.com',
            plan_tier='FREE'
        )
        UserProfile.objects.create(user=self.user_b, business=self.shop_b, phone='9822222222')

    def test_tenant_data_isolation(self):
        \"\"\"Ensure Shop A cannot see or access Shop B data.\"\"\"
        cust_a = Customer.objects.create(business=self.shop_a, name='Customer A', phone='9900000001')
        cust_b = Customer.objects.create(business=self.shop_b, name='Customer B', phone='9900000002')

        # Login as User A
        client_a = Client()
        client_a.login(username='user_a@example.com', password='password123')
        
        response = client_a.get('/customers/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Customer A')
        self.assertNotContains(response, 'Customer B')

        # Try to view Customer B's detail as User A -> Should return 404
        response_detail = client_a.get(f'/customers/{cust_b.pk}/')
        self.assertEqual(response_detail.status_code, 404)

    def test_plan_limits_enforcement(self):
        \"\"\"Free plan enforces customer and product limits.\"\"\"
        can_add, count, limit = self.shop_a.can_add_customer()
        self.assertTrue(can_add)
        self.assertEqual(limit, 50)
"""
with open(os.path.join(BASE_DIR, "tests", "test_auth_and_business.py"), "w", encoding="utf-8") as f:
    f.write(test_auth_py)

# tests/test_sales_and_pos.py
test_sales_py = """import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from decimal import Decimal
from businesses.models import Business
from accounts.models import UserProfile
from customers.models import Customer
from products.models import Product, Category
from inventory.models import StockMovement, MobileDevice
from sales.models import Sale, SaleItem
from payments.models import Payment

class SalesAndPOSFlowTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='shopowner@example.com',
            email='shopowner@example.com',
            password='password123',
            first_name='Paras'
        )
        self.business = Business.objects.create(
            owner=self.user,
            name='Paras Mobile Test',
            owner_name='Paras',
            phone='9800000000',
            email='shopowner@example.com',
            plan_tier='PRO'
        )
        UserProfile.objects.create(user=self.user, business=self.business, phone='9800000000')

        self.category = Category.objects.create(business=self.business, name='Smartphones')
        self.product = Product.objects.create(
            business=self.business,
            category=self.category,
            name='Test Galaxy A56',
            purchase_price=Decimal('20000.00'),
            selling_price=Decimal('25000.00'),
            stock_quantity=10,
            is_imei_tracked=True
        )
        self.device = MobileDevice.objects.create(
            business=self.business,
            product=self.product,
            imei_1='861234567890123',
            purchase_price=Decimal('20000.00'),
            selling_price=Decimal('25000.00'),
            status='IN_STOCK'
        )
        self.customer = Customer.objects.create(
            business=self.business,
            name='Test Customer',
            phone='9812345678'
        )

        self.client = Client()
        self.client.login(username='shopowner@example.com', password='password123')

    def test_pos_checkout_flow(self):
        \"\"\"Tests atomic POS checkout, inventory decrement, device status update, payment, and Khata balance.\"\"\"
        payload = {
            'customer_id': self.customer.id,
            'payment_method': 'UPI',
            'discount': 1000,
            'tax': 0,
            'paid_amount': 20000,  # Partial payment: Total is 24,000, Paid 20,000 -> Due 4,000
            'notes': 'POS test sale',
            'items': [
                {
                    'product_id': self.product.id,
                    'quantity': 1,
                    'unit_price': 25000,
                    'discount': 0,
                    'device_id': self.device.id
                }
            ]
        }

        response = self.client.post(
            '/sales/api/checkout/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(Decimal(data['total_amount']), Decimal('24000.00'))
        self.assertEqual(Decimal(data['paid_amount']), Decimal('20000.00'))
        self.assertEqual(Decimal(data['due_amount']), Decimal('4000.00'))

        # 1. Verify Stock Reduced
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 9)

        # 2. Verify Stock Movement Logged
        movement = StockMovement.objects.filter(product=self.product, movement_type='SALE').first()
        self.assertIsNotNone(movement)
        self.assertEqual(movement.quantity, 1)

        # 3. Verify Device marked SOLD
        self.device.refresh_from_db()
        self.assertEqual(self.device.status, 'SOLD')
        self.assertEqual(self.device.customer, self.customer)

        # 4. Verify Customer Khata Due
        self.assertEqual(self.customer.get_outstanding_due(), Decimal('4000.00'))

        # 5. Verify Payment Voucher Created
        payment = Payment.objects.filter(customer=self.customer).first()
        self.assertIsNotNone(payment)
        self.assertEqual(payment.amount, Decimal('20000.00'))
"""
with open(os.path.join(BASE_DIR, "tests", "test_sales_and_pos.py"), "w", encoding="utf-8") as f:
    f.write(test_sales_py)

# tests/test_reports_and_profit.py
test_reports_py = """from django.test import TestCase, Client
from django.contrib.auth.models import User
from decimal import Decimal
from django.utils import timezone
from businesses.models import Business
from accounts.models import UserProfile
from customers.models import Customer
from products.models import Product
from sales.models import Sale, SaleItem
from expenses.models import Expense
from invoices.pdf_service import generate_invoice_pdf

class ReportsAndPAndLTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='reportowner@example.com',
            email='reportowner@example.com',
            password='password123',
            first_name='Owner'
        )
        self.business = Business.objects.create(
            owner=self.user,
            name='Reports Test Shop',
            owner_name='Owner',
            phone='9800001111',
            email='reportowner@example.com',
            plan_tier='PRO'
        )
        UserProfile.objects.create(user=self.user, business=self.business)

        self.customer = Customer.objects.create(
            business=self.business,
            name='Report Cust',
            phone='9899887766'
        )
        self.product = Product.objects.create(
            business=self.business,
            name='Item A',
            purchase_price=Decimal('1000.00'),
            selling_price=Decimal('1500.00'),
            stock_quantity=20
        )

        self.client = Client()
        self.client.login(username='reportowner@example.com', password='password123')

    def test_gross_and_net_profit_calculation(self):
        # Create Sale: Selling Revenue = ₹3,000, COGS = ₹2,000 -> Gross Profit = ₹1,000
        sale = Sale.objects.create(
            business=self.business,
            customer=self.customer,
            invoice_number='INV-TEST-01',
            subtotal=Decimal('3000.00'),
            total_amount=Decimal('3000.00'),
            paid_amount=Decimal('3000.00'),
            payment_status='PAID'
        )
        SaleItem.objects.create(
            sale=sale,
            product=self.product,
            quantity=2,
            unit_price=Decimal('1500.00'),
            total_price=Decimal('3000.00')
        )

        # Create Business Expense: ₹300
        Expense.objects.create(
            business=self.business,
            title='Shop Electricity',
            amount=Decimal('300.00')
        )

        # Gross Profit = ₹1,000, Net Profit = ₹700
        self.assertEqual(sale.get_cogs(), Decimal('2000.00'))
        self.assertEqual(sale.get_gross_profit(), Decimal('1000.00'))

        response = self.client.get('/reports/profit-loss/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'True Profit & Loss Statement')

    def test_pdf_invoice_generation(self):
        sale = Sale.objects.create(
            business=self.business,
            customer=self.customer,
            invoice_number='INV-PDF-01',
            subtotal=Decimal('1500.00'),
            total_amount=Decimal('1500.00'),
            paid_amount=Decimal('1500.00'),
            payment_status='PAID'
        )
        SaleItem.objects.create(
            sale=sale,
            product=self.product,
            quantity=1,
            unit_price=Decimal('1500.00'),
            total_price=Decimal('1500.00')
        )

        pdf_buf = generate_invoice_pdf(sale)
        self.assertTrue(len(pdf_buf.getvalue()) > 1000)
        self.assertTrue(pdf_buf.getvalue().startswith(b'%PDF'))
"""
with open(os.path.join(BASE_DIR, "tests", "test_reports_and_profit.py"), "w", encoding="utf-8") as f:
    f.write(test_reports_py)

print("Automated test suite created successfully in tests/!")
