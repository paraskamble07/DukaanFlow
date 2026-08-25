from django.test import TestCase, Client
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
