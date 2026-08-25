import json
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
        """Tests atomic POS checkout, inventory decrement, device status update, payment, and Khata balance."""
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
