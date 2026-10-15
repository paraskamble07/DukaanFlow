"""Tests for the customer ledger statement PDF (Phase 5).

Division of testing:
- `_ledger_rows` (the data layer) is tested numerically: Decimal paise,
  running balances, opening-balance carry-forward.
- The HTTP endpoint is tested for plumbing: valid PDF bytes, correct
  content type / filename, date validation, tenant isolation, and that
  the closing balance on the full statement equals the customer's
  current outstanding due (the financial-integrity invariant).
"""
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import UserProfile
from businesses.models import Business
from customers.models import Customer
from payments.models import Payment
from products.models import Product
from sales.models import Sale, SaleItem
from invoices.pdf_service import _ledger_rows


def _owner(email):
    user = User.objects.create_user(email=email, username=email, password='Test@12345')
    UserProfile.objects.create(user=user, role='OWNER', phone='9999900000')
    return user


def _business(owner, name, phone):
    return Business.objects.create(
        owner=owner, name=name, owner_name=owner.email.split('@')[0].title(),
        phone=phone, email=f'{name}@shop.test', city='Pune', state='Maharashtra',
        address='Shop 12, Market Road', pincode='411001',
    )


class LedgerPdfBase(TestCase):
    def setUp(self):
        self.owner = _owner('ledger@pdf.test')
        self.business = _business(self.owner, 'Ledger Shop', '9000000011')
        self.other_owner = _owner('other@pdf.test')
        self.other_business = _business(self.other_owner, 'Other Shop', '9000000022')

        self.client = APIClient()
        res = self.client.post('/api/auth/login/', {
            'email': 'ledger@pdf.test', 'password': 'Test@12345'}, format='json')
        self.assertEqual(res.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {res.data['tokens']['access']}")

        self.customer = Customer.objects.create(
            business=self.business, name='Ramesh Kumar', phone='9876543210',
            address='Lane 3, Kothrud', email='ramesh@example.com')
        self.product = Product.objects.create(
            business=self.business, name='Sim Tray', selling_price=Decimal('100.00'),
            purchase_price=Decimal('60.00'), stock_quantity=50,
        )
        self.invoice_counter = 0

    def _sale(self, customer, total, days_ago=0, method='CASH'):
        self.invoice_counter += 1
        sale = Sale.objects.create(
            business=self.business, customer=customer,
            invoice_number=f'LED-{self.invoice_counter}',
            payment_status='UNPAID',
            payment_method=method,
            total_amount=total, paid_amount=Decimal('0.00'),
            sale_date=timezone.now() - timedelta(days=days_ago),
        )
        SaleItem.objects.create(
            sale=sale, product=self.product, quantity=1,
            unit_price=total, total_price=total,
        )
        return sale

    def _pay(self, customer, amount, days_ago=0, method='CASH', ref=''):
        return Payment.objects.create(
            business=self.business, customer=customer,
            payment_type='CUSTOMER_PAYMENT', amount=amount,
            payment_method=method,
            payment_date=timezone.now() - timedelta(days=days_ago),
            reference_number=ref or None,
        )


class LedgerDataLayerTest(LedgerPdfBase):
    """Numeric correctness of the statement rows themselves."""

    def test_running_balance_and_decimal_paise(self):
        """Paise-level amounts must survive as Decimal end to end."""
        self._sale(self.customer, Decimal('22000.50'), days_ago=10)
        self._pay(self.customer, Decimal('325.75'), days_ago=5)
        self._sale(self.customer, Decimal('500.25'), days_ago=2)

        opening, rows = _ledger_rows(self.customer, None, None)
        self.assertEqual(opening, Decimal('0.00'))
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]['balance'], Decimal('22000.50'))
        self.assertEqual(rows[1]['balance'], Decimal('21674.75'))
        self.assertEqual(rows[2]['balance'], Decimal('22175.00'))

    def test_closing_equals_outstanding_due_without_filter(self):
        """No date filter: closing balance == customer.get_outstanding_due()."""
        self._sale(self.customer, Decimal('5000.00'), days_ago=30)
        self._sale(self.customer, Decimal('2500.00'), days_ago=15)
        self._pay(self.customer, Decimal('3000.00'), days_ago=10)
        self._pay(self.customer, Decimal('999.99'), days_ago=1)

        opening, rows = _ledger_rows(self.customer, None, None)
        debits = sum((r['debit'] for r in rows), opening)
        credits = sum((r['credit'] for r in rows), Decimal('0.00'))
        closing = debits - credits
        self.assertEqual(closing, self.customer.get_outstanding_due())
        self.assertEqual(closing, Decimal('3500.01'))

    def test_opening_balance_caries_forward(self):
        """Transactions before from_date collapse into the opening balance."""
        self._sale(self.customer, Decimal('4000.00'), days_ago=60)
        self._pay(self.customer, Decimal('1000.00'), days_ago=50)
        self._sale(self.customer, Decimal('600.00'), days_ago=5)

        today = timezone.now().date()
        from_date = today - timedelta(days=20)
        opening, rows = _ledger_rows(self.customer, from_date, None)

        self.assertEqual(opening, Decimal('3000.00'))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['debit'], Decimal('600.00'))
        self.assertEqual(rows[0]['balance'], Decimal('3600.00'))

    def test_to_date_excludes_later_transactions(self):
        self._sale(self.customer, Decimal('4000.00'), days_ago=60)
        self._sale(self.customer, Decimal('600.00'), days_ago=5)

        today = timezone.now().date()
        to_date = today - timedelta(days=20)
        opening, rows = _ledger_rows(self.customer, None, to_date)

        self.assertEqual(opening, Decimal('0.00'))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['debit'], Decimal('4000.00'))
        self.assertEqual(rows[0]['balance'], Decimal('4000.00'))

    def test_supplier_payments_excluded_from_customer_ledger(self):
        """Only CUSTOMER_PAYMENT rows belong in a customer's ledger."""
        self._sale(self.customer, Decimal('1000.00'))
        Payment.objects.create(
            business=self.business, payment_type='SUPPLIER_PAYMENT',
            amount=Decimal('999.00'), customer=self.customer,
        )
        _, rows = _ledger_rows(self.customer, None, None)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['credit'], Decimal('0.00'))


class LedgerPdfEndpointTest(LedgerPdfBase):
    """HTTP plumbing for /api/customers/<id>/ledger-pdf/."""

    def _get(self, customer_id=None, **params):
        url = f'/api/customers/{customer_id or self.customer.id}/ledger-pdf/'
        return self.client.get(url, params or None)

    def test_valid_pdf_is_returned(self):
        self._sale(self.customer, Decimal('22000.00'))
        self._pay(self.customer, Decimal('7000.00'))

        res = self._get()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res['Content-Type'], 'application/pdf')
        self.assertIn('Ledger_Ramesh_Kumar.pdf', res['Content-Disposition'])
        self.assertTrue(res.content.startswith(b'%PDF'))
        self.assertTrue(res.content.rstrip().endswith(b'%%EOF'))

    def test_settled_account_shows_zero_closing(self):
        self._sale(self.customer, Decimal('1500.00'))
        self._pay(self.customer, Decimal('1500.00'))

        res = self._get()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(self.customer.get_outstanding_due(), Decimal('0.00'))

        _, rows = _ledger_rows(self.customer, None, None)
        self.assertEqual(rows[-1]['balance'], Decimal('0.00'))

    def test_tenant_isolation_other_shops_customer(self):
        other_customer = Customer.objects.create(
            business=self.other_business, name='Secret Client', phone='9111111111')
        res = self._get(customer_id=other_customer.id)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_request_rejected(self):
        self.client.credentials()  # drop the bearer token
        res = self._get()
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_date_format_returns_400(self):
        res = self._get(from_date='15-10-2026')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('YYYY-MM-DD', res.data['error'])

        res = self._get(to_date='not-a-date')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reversed_range_returns_400(self):
        today = timezone.now().date()
        res = self._get(from_date=today.isoformat(), to_date=(today - timedelta(days=5)).isoformat())
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('cannot be after', res.data['error'])

    def test_date_filter_produces_valid_pdf_with_opening(self):
        self._sale(self.customer, Decimal('4000.00'), days_ago=60)
        self._pay(self.customer, Decimal('1000.00'), days_ago=50)
        self._sale(self.customer, Decimal('600.00'), days_ago=5)

        from_date = (timezone.now().date() - timedelta(days=20)).isoformat()
        res = self._get(from_date=from_date)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.content.startswith(b'%PDF'))
        self.assertTrue(res.content.rstrip().endswith(b'%%EOF'))
