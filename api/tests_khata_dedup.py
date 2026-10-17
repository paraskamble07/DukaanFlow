"""Khata repayment settlement + customer dedup regression tests.

Two production bugs these lock down:

1. A manual Khata repayment used to record only a Payment row; every bill of
   that customer kept showing its original "Due" and "Partially Paid" state
   forever. Live data showed customers fully settled in the books whose
   invoices still claimed the full bill as due. Recording a payment must now
   settle the bills (oldest first), and the per-invoice state must always be
   reproducible from the payment history.
2. Nothing stopped the same mobile number from being registered twice — the
   shop then carried two parallel ledgers for one person. Duplicate creation
   must be rejected with a pointer to the existing record.
"""
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import UserProfile
from businesses.models import Business
from customers.models import Customer
from payments.models import Payment
from sales.models import Sale, SaleItem


class KhataSettlementTestBase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='khata_owner@dukaanflow.com',
            email='khata_owner@dukaanflow.com',
            password='Password123!', first_name='Suresh')
        self.business = Business.objects.create(
            owner=self.user, name='Suresh Mobiles', owner_name='Suresh',
            phone='9876500000', email='khata_owner@dukaanflow.com',
            invoice_prefix='SM-', next_invoice_number=1001)
        UserProfile.objects.create(
            user=self.user, business=self.business,
            phone='9876500000', role='OWNER')
        self._login()

    def _login(self, email='khata_owner@dukaanflow.com',
               password='Password123!'):
        res = self.client.post('/api/auth/login/',
                               {'email': email, 'password': password},
                               format='json')
        self.assertEqual(res.status_code, 200, res.data)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {res.data['tokens']['access']}")

    def _bill(self, customer, total, paid=Decimal('0.00')):
        """Create a settled-looking bill directly (no stock side effects)."""
        sale = Sale.objects.create(
            business=self.business, customer=customer,
            invoice_number=f'INV-{Sale.objects.count() + 1}',
            subtotal=total, discount=Decimal('0.00'),
            tax_amount=Decimal('0.00'), total_amount=total,
            paid_amount=Decimal('0.00'))
        if paid > 0:
            Payment.objects.create(
                business=self.business, payment_type='CUSTOMER_PAYMENT',
                customer=customer, sale=sale, amount=paid,
                payment_method='CASH',
                reference_number=f'INV-PAY-{sale.invoice_number}')
            sale.paid_amount = paid
            sale.save()
        return sale

    def _receive(self, customer, amount):
        return self.client.post('/api/payments/customer/', {
            'customer_id': customer.id, 'amount': amount,
            'payment_method': 'CASH',
        }, format='json')


class KhataRepaymentSettlementTest(KhataSettlementTestBase):
    def setUp(self):
        super().setUp()
        self.customer = Customer.objects.create(
            business=self.business, name='Rahul Khata', phone='9876543210')

    def test_repayment_settles_the_bill_rows(self):
        """The reported bug: fully settled customer, bills still showing due."""
        self._bill(self.customer, Decimal('1000.00'))

        res = self._receive(self.customer, Decimal('1000.00'))
        self.assertEqual(res.status_code, 201, res.data)
        self.assertEqual(res.data['remaining_due'], 0.0)

        sale = Sale.objects.get(customer=self.customer)
        self.assertEqual(sale.paid_amount, Decimal('1000.00'))
        self.assertEqual(sale.due_amount, Decimal('0.00'))
        self.assertEqual(sale.payment_status, 'PAID')
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.get_outstanding_due(), Decimal('0.00'))

    def test_partial_repayment_settles_oldest_bill_first(self):
        """FIFO: the repayment closes the oldest bill before touching newer ones."""
        first = self._bill(self.customer, Decimal('500.00'))
        second = self._bill(self.customer, Decimal('700.00'))

        res = self._receive(self.customer, Decimal('800.00'))
        self.assertEqual(res.status_code, 201, res.data)

        first.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual(first.paid_amount, Decimal('500.00'))
        self.assertEqual(first.payment_status, 'PAID')
        self.assertEqual(second.paid_amount, Decimal('300.00'))
        self.assertEqual(second.due_amount, Decimal('400.00'))
        self.assertEqual(second.payment_status, 'PARTIAL')
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.get_outstanding_due(), Decimal('400.00'))

    def test_counter_payment_stays_capped_and_excess_rolls_over(self):
        """A linked checkout payment settles its own bill (capped at the
        total); a manual repayment then settles remaining room of the oldest
        bill first and rolls any excess onto the next one."""
        a = self._bill(self.customer, Decimal('1000.00'), Decimal('700.00'))
        b = self._bill(self.customer, Decimal('600.00'))

        res = self._receive(self.customer, Decimal('600.00'))
        self.assertEqual(res.status_code, 201, res.data)

        a.refresh_from_db()
        b.refresh_from_db()
        # a is filled to exactly its total — never past it — and b takes
        # the remaining 300.
        self.assertEqual(a.paid_amount, Decimal('1000.00'))
        self.assertEqual(a.due_amount, Decimal('0.00'))
        self.assertEqual(a.payment_status, 'PAID')
        self.assertEqual(b.paid_amount, Decimal('300.00'))
        self.assertEqual(b.due_amount, Decimal('300.00'))
        self.assertEqual(b.payment_status, 'PARTIAL')
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.get_outstanding_due(), Decimal('300.00'))

    def test_fractional_repayment_is_accepted_at_exact_value(self):
        """Overpayment guard must not trip on legitimate paise amounts."""
        self._bill(self.customer, Decimal('1200.55'))

        res = self._receive(self.customer, '1200.55')
        self.assertEqual(res.status_code, 201, res.data)
        self.assertEqual(res.data['remaining_due'], 0.0)

    def test_overpayment_still_rejected(self):
        self._bill(self.customer, Decimal('1000.00'))
        res = self._receive(self.customer, Decimal('1000.01'))
        self.assertEqual(res.status_code, 400, res.data)
        self.assertIn('exceeds', res.data['error'])
        self.assertEqual(Payment.objects.count(), 0)

    def test_response_reports_which_invoices_were_settled(self):
        self._bill(self.customer, Decimal('300.00'))
        res = self._receive(self.customer, Decimal('300.00'))
        self.assertEqual(res.status_code, 201)
        settlements = res.data['settled_invoices']
        self.assertTrue(any(
            s['status'] == 'PAID' and Decimal(s['settled']) == Decimal('300.00')
            for s in settlements), settlements)

    def test_repairing_legacy_drift(self):
        """Bills that drifted before the fix settle correctly afterwards."""
        sale = self._bill(self.customer, Decimal('1000.00'))
        # Legacy manual payment recorded WITHOUT settling the bill
        # (exactly what the old code path did).
        Payment.objects.create(
            business=self.business, payment_type='CUSTOMER_PAYMENT',
            customer=self.customer, amount=Decimal('250.00'),
            payment_method='CASH')

        res = self._receive(self.customer, Decimal('250.00'))
        self.assertEqual(res.status_code, 201, res.data)

        sale.refresh_from_db()
        self.assertEqual(sale.paid_amount, Decimal('500.00'))
        self.assertEqual(sale.due_amount, Decimal('500.00'))
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.get_outstanding_due(), Decimal('500.00'))


class CustomerDuplicatePreventionTest(KhataSettlementTestBase):
    def setUp(self):
        super().setUp()
        self.customer = Customer.objects.create(
            business=self.business, name='Ramesh Khata Test',
            phone='9876500011')

    def _create(self, phone, name='Another Person'):
        return self.client.post('/api/customers/', {
            'name': name, 'phone': phone,
        }, format='json')

    def test_same_number_is_rejected_with_existing_record(self):
        res = self._create('9876500011')
        self.assertEqual(res.status_code, 409, res.data)
        self.assertEqual(res.data['code'], 'DUPLICATE_CUSTOMER')
        self.assertEqual(res.data['existing_customer']['id'], self.customer.id)
        self.assertEqual(Customer.objects.count(), 1)

    def test_number_formatting_variants_are_the_same_customer(self):
        for variant in ['+91 98765 00011', '09876500011', '98765-00011']:
            res = self._create(variant)
            self.assertEqual(res.status_code, 409, f'{variant}: {res.data}')
        self.assertEqual(Customer.objects.count(), 1)

    def test_placeholder_numbers_are_not_deduplicated(self):
        # Users type all-zero numbers for walk-ins: several such customers
        # must stay separable.
        for _ in range(2):
            res = self._create('0000000000')
            self.assertEqual(res.status_code, 201, res.data)
        self.assertEqual(Customer.objects.count(), 3)

    def test_new_distinct_number_is_accepted(self):
        res = self._create('9876599999')
        self.assertEqual(res.status_code, 201, res.data)
        self.assertEqual(Customer.objects.count(), 2)

    def test_same_number_in_another_shop_is_allowed(self):
        user = User.objects.create_user(
            username='other_owner@dukaanflow.com',
            email='other_owner@dukaanflow.com', password='Password123!')
        business = Business.objects.create(
            owner=user, name='Other Shop', owner_name='Other',
            phone='9876555555', invoice_prefix='OS-', next_invoice_number=1)
        self.assertEqual(
            Customer.objects.create(
                business=business, name='Same Number', phone='9876500011').phone,
            '9876500011')
        # And the API of the first shop still refuses it for itself.
        res = self._create('9876500011')
        self.assertEqual(res.status_code, 409)
        self.assertEqual(Customer.objects.filter(business=self.business).count(), 1)

    def test_customer_can_keep_their_own_number(self):
        res = self.client.put(f'/api/customers/{self.customer.id}/', {
            'name': 'Ramesh Renamed', 'phone': '9876500011',
        }, format='json')
        self.assertEqual(res.status_code, 200, res.data)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.name, 'Ramesh Renamed')

    def test_update_to_another_customers_number_is_rejected(self):
        other = Customer.objects.create(
            business=self.business, name='Second Person', phone='9876588888')
        res = self.client.put(f'/api/customers/{other.id}/', {
            'name': 'Second Person', 'phone': '9876500011',
        }, format='json')
        self.assertEqual(res.status_code, 409, res.data)
        self.assertEqual(res.data['code'], 'DUPLICATE_CUSTOMER')

    def test_phone_is_normalized_on_save(self):
        res = self._create('  +91-98765 77777 ')
        self.assertEqual(res.status_code, 201, res.data)
        self.assertEqual(res.data['phone'], '9876577777')
