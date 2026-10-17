"""Clear-Khata workflow regression test (owner-reported scenario).

Locks down the exact shop workflow reported by the owner:

    Khata bill ₹1,000 → receive ₹300 → balance ₹700
                       → receive ₹700 → balance ₹0, customer shows "Cleared"

Every step is driven through the public API surface the Flutter app uses
(POST /api/customers/, GET /api/customers/?due=yes|cleared,
POST /api/payments/customer/, GET /api/customers/<id>/ledger/), so the test
verifies the behavior the shop owner actually experiences, not just model
math. The financial-integrity guard (no overpayment, exact-amount entry) is
asserted too, because silently flooring an overpayment at zero is what used
to make ledgers drift.
"""
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import UserProfile
from businesses.models import Business
from customers.models import Customer
from sales.models import Sale


class ClearKhataFlowTestBase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='khataflow_owner@dukaanflow.com',
            email='khataflow_owner@dukaanflow.com',
            password='Password123!', first_name='Ramesh')
        self.business = Business.objects.create(
            owner=self.user, name='Ramesh Kirana', owner_name='Ramesh',
            phone='9876511111', email='khataflow_owner@dukaanflow.com',
            invoice_prefix='RK-', next_invoice_number=2001)
        UserProfile.objects.create(
            user=self.user, business=self.business,
            phone='9876511111', role='OWNER')
        res = self.client.post('/api/auth/login/',
                               {'email': 'khataflow_owner@dukaanflow.com',
                                'password': 'Password123!'},
                               format='json')
        self.assertEqual(res.status_code, 200, res.data)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {res.data['tokens']['access']}")

    def _create_customer(self, name='Kisan Patil', phone='9876543200'):
        res = self.client.post('/api/customers/',
                               {'name': name, 'phone': phone},
                               format='json')
        self.assertEqual(res.status_code, 201, res.data)
        return Customer.objects.get(pk=res.data['id'])

    def _bill(self, customer, total):
        """Create a Khata bill directly (no stock side effects)."""
        return Sale.objects.create(
            business=self.business, customer=customer,
            invoice_number=f'RK-{Sale.objects.count() + 1}',
            subtotal=total, discount=Decimal('0.00'),
            tax_amount=Decimal('0.00'), total_amount=total,
            paid_amount=Decimal('0.00'))

    def _receive(self, customer, amount):
        return self.client.post('/api/payments/customer/', {
            'customer_id': customer.id, 'amount': str(amount),
            'payment_method': 'CASH',
        }, format='json')

    def _customer_data(self, customer):
        res = self.client.get(f'/api/customers/{customer.id}/')
        self.assertEqual(res.status_code, 200, res.data)
        return res.data


class ClearKhataFlowTest(ClearKhataFlowTestBase):

    def test_1000_bill_then_300_then_700_then_cleared(self):
        customer = self._create_customer(name='Kisan Patil', phone='9876543209')
        self._bill(customer, Decimal('1000.00'))

        # ₹1,000 billed, nothing paid: the customer must show as having dues.
        data = self._customer_data(customer)
        self.assertEqual(Decimal(str(data['outstanding_due'])),
                         Decimal('1000.00'))
        self.assertEqual(Decimal(str(data['total_paid'])), Decimal('0.00'))
        res = self.client.get('/api/customers/?due=yes')
        self.assertIn(customer.id, [c['id'] for c in res.data['results']])

        # Receive ₹300 → outstanding must be exactly ₹700.
        res = self._receive(customer, Decimal('300.00'))
        self.assertEqual(res.status_code, 201, res.data)
        self.assertEqual(Decimal(str(res.data['remaining_due'])),
                         Decimal('700.00'))
        data = self._customer_data(customer)
        self.assertEqual(Decimal(str(data['outstanding_due'])),
                         Decimal('700.00'))
        self.assertEqual(Decimal(str(data['total_paid'])), Decimal('300.00'))

        # Receive the remaining ₹700 → outstanding ₹0, "Cleared".
        res = self._receive(customer, Decimal('700.00'))
        self.assertEqual(res.status_code, 201, res.data)
        self.assertEqual(Decimal(str(res.data['remaining_due'])),
                         Decimal('0.00'))
        data = self._customer_data(customer)
        self.assertEqual(Decimal(str(data['outstanding_due'])),
                         Decimal('0.00'))
        self.assertEqual(Decimal(str(data['total_paid'])), Decimal('1000.00'))

        # The "Cleared" filter must now find them, and the dues filter must not.
        res = self.client.get('/api/customers/?due=cleared')
        self.assertIn(customer.id, [c['id'] for c in res.data['results']])
        res = self.client.get('/api/customers/?due=yes')
        self.assertNotIn(customer.id, [c['id'] for c in res.data['results']])

    def test_partial_payments_settle_the_oldest_bills_first(self):
        customer = self._create_customer(name='Sita Devi', phone='9876543210')
        first = self._bill(customer, Decimal('400.00'))
        second = self._bill(customer, Decimal('600.00'))

        res = self._receive(customer, Decimal('400.00'))
        self.assertEqual(res.status_code, 201, res.data)
        first.refresh_from_db()
        second.refresh_from_db()
        # The ₹400 payment must settle the oldest bill completely and leave
        # the second one untouched — never split arbitrarily across both.
        self.assertEqual(first.paid_amount, Decimal('400.00'))
        self.assertEqual(second.paid_amount, Decimal('0.00'))

    def test_overpayment_is_rejected_and_books_stay_exact(self):
        customer = self._create_customer(name='Rahul More', phone='9876543211')
        self._bill(customer, Decimal('1000.00'))

        # A ₹1,200 payment against a ₹1,000 due must be rejected: the extra
        # ₹200 would otherwise be silently floored at zero and vanish.
        res = self._receive(customer, Decimal('1200.00'))
        self.assertEqual(res.status_code, 400, res.data)
        self.assertIn('exceeds', res.data['error'])

        data = self._customer_data(customer)
        self.assertEqual(Decimal(str(data['outstanding_due'])),
                         Decimal('1000.00'))
        self.assertEqual(Decimal(str(data['total_paid'])), Decimal('0.00'))

    def test_ledger_shows_bill_and_both_payments(self):
        customer = self._create_customer(name='Anita Rao', phone='9876543212')
        self._bill(customer, Decimal('1000.00'))
        self._receive(customer, Decimal('300.00'))
        self._receive(customer, Decimal('700.00'))

        res = self.client.get(f'/api/customers/{customer.id}/ledger/')
        self.assertEqual(res.status_code, 200, res.data)
        self.assertEqual(len(res.data['sales']), 1)
        self.assertEqual(len(res.data['payments']), 2)
        self.assertEqual(Decimal(str(res.data['summary']['outstanding_due'])),
                         Decimal('0.00'))
        self.assertEqual(Decimal(str(res.data['summary']['total_paid'])),
                         Decimal('1000.00'))

    def test_zero_or_negative_payment_is_rejected(self):
        customer = self._create_customer(name='Vijay Shah', phone='9876543213')
        self._bill(customer, Decimal('1000.00'))

        res = self._receive(customer, Decimal('0.00'))
        self.assertEqual(res.status_code, 400, res.data)

        res = self._receive(customer, Decimal('-500.00'))
        self.assertEqual(res.status_code, 400, res.data)

        data = self._customer_data(customer)
        self.assertEqual(Decimal(str(data['outstanding_due'])),
                         Decimal('1000.00'))
