"""Payment-reminder tests — fully offline (no SMS/WhatsApp provider exists).

ShopZen reminders are **composer-driven by design**: the backend computes the
message and the outstanding balance, and hands the app a prefilled WhatsApp
link or SMS body; the owner's own phone (WhatsApp app / SMS app) sends it.
The backend never talks to an SMS gateway, so:

* there are NO provider credentials to configure (a common question), and
* delivery can never be faked — the server logs only a user-confirmed
  "reminder initiated", never "delivered".

These tests lock down the whole pipeline without the network: the pure
message/URL builders, the due-list computation, and the log endpoint's
integrity guards (settled customers, cooldown, invalid channel).
"""
from datetime import timedelta
from decimal import Decimal
from urllib.parse import parse_qs, urlparse

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import UserProfile
from businesses.models import Business
from core.utils import build_whatsapp_url
from customers.models import Customer
from payments.models import Payment
from reminders.models import ReminderLog
from reminders.views import reminder_message, sms_body
from sales.models import Sale


class ReminderTestBase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='remind_owner@dukaanflow.com',
            email='remind_owner@dukaanflow.com',
            password='Password123!', first_name='Deepak')
        self.business = Business.objects.create(
            owner=self.user, name='Deepak Stores', owner_name='Deepak',
            phone='9876522222', email='remind_owner@dukaanflow.com',
            invoice_prefix='DS-', next_invoice_number=3001)
        UserProfile.objects.create(
            user=self.user, business=self.business,
            phone='9876522222', role='OWNER')
        res = self.client.post('/api/auth/login/',
                               {'email': 'remind_owner@dukaanflow.com',
                                'password': 'Password123!'},
                               format='json')
        self.assertEqual(res.status_code, 200, res.data)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {res.data['tokens']['access']}")

    def _customer(self, name, phone):
        return Customer.objects.create(
            business=self.business, name=name, phone=phone)

    def _credit_bill(self, customer, total, days_ago=0):
        return Sale.objects.create(
            business=self.business, customer=customer,
            invoice_number=f'DS-{Sale.objects.count() + 1}',
            subtotal=total, discount=Decimal('0.00'),
            tax_amount=Decimal('0.00'), total_amount=total,
            paid_amount=Decimal('0.00'),
            sale_date=timezone.now() - timedelta(days=days_ago))


class MessageBuilderTest(TestCase):
    """Pure functions — no network, no provider, deterministic output."""

    def test_whatsapp_url_normalizes_a_10_digit_number_to_91(self):
        url = build_whatsapp_url('9876543210', 'Namaste!')
        parsed = urlparse(url)
        self.assertEqual(parsed.netloc, 'wa.me')
        self.assertEqual(parsed.path, '/919876543210')
        self.assertEqual(parse_qs(parsed.query)['text'], ['Namaste!'])

    def test_whatsapp_url_passes_through_a_12_digit_number(self):
        url = build_whatsapp_url('+91 98765 43210', 'Balance 500')
        self.assertIn('/919876543210', url)

    def test_whatsapp_url_is_empty_without_a_phone(self):
        self.assertEqual(build_whatsapp_url('', 'hi'), '')
        self.assertEqual(build_whatsapp_url(None, 'hi'), '')

    def test_reminder_message_names_shop_customer_and_amount(self):
        business = Business(name='Deepak Stores', phone='9876500000')
        customer = Customer(name='Kisan Patil', phone='9876543210')
        msg = reminder_message(customer, business, Decimal('700.00'), None)
        self.assertIn('Kisan Patil', msg)
        self.assertIn('Deepak Stores', msg)
        self.assertIn('700', msg)
        self.assertNotIn('%', msg)  # nothing left unformatted

    def test_sms_body_is_compact_and_has_no_whitespace_markup(self):
        business = Business(name='Deepak Stores', phone='9876500000')
        customer = Customer(name='Kisan Patil', phone='9876543210')
        body = sms_body(customer, business, Decimal('700.00'), None)
        self.assertIn('Kisan Patil', body)
        self.assertIn('700', body)
        self.assertIn('9876500000', body)
        # SMS is plain text: no WhatsApp-style bold markup.
        self.assertNotIn('*', body)


class DueListTest(ReminderTestBase):

    def test_due_list_includes_debtor_with_message_bodies(self):
        customer = self._customer('Kisan Patil', '9876543219')
        self._credit_bill(customer, Decimal('700.00'))
        res = self.client.get('/api/reminders/due-list/')
        self.assertEqual(res.status_code, 200, res.data)
        rows = res.data['results']
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row['customer_id'], customer.id)
        self.assertEqual(Decimal(row['outstanding']), Decimal('700.00'))
        self.assertEqual(row['status'], 'DUE')
        # The composer payloads the app hands to WhatsApp/SMS:
        self.assertTrue(row['whatsapp_url'].startswith('https://wa.me/919876543219'))
        self.assertIn('Kisan Patil', row['sms_body'])

    def test_due_list_marks_overdue_before_a_45_day_old_bill(self):
        customer = self._customer('Old Debtor', '9876543218')
        self._credit_bill(customer, Decimal('500.00'), days_ago=45)
        res = self.client.get('/api/reminders/due-list/')
        self.assertEqual(res.data['results'][0]['status'], 'OVERDUE')

    def test_settled_customer_is_never_remindable(self):
        customer = self._customer('Clean Customer', '9876543217')
        sale = self._credit_bill(customer, Decimal('500.00'))
        Payment.objects.create(
            business=self.business, payment_type='CUSTOMER_PAYMENT',
            customer=customer, sale=sale, amount=Decimal('500.00'),
            payment_method='CASH')
        res = self.client.get('/api/reminders/due-list/')
        self.assertEqual(res.data['results'], [])

    def test_due_list_is_tenant_isolated(self):
        """Another shop's debtors must never leak into this shop's list."""
        customer = self._customer('Kisan Patil', '9876543219')
        self._credit_bill(customer, Decimal('700.00'))
        other = User.objects.create_user(
            username='other_owner@dukaanflow.com',
            email='other_owner@dukaanflow.com', password='Password123!')
        other_business = Business.objects.create(
            owner=other, name='Other Shop', owner_name='Other',
            phone='9876509999', email='other_owner@dukaanflow.com',
            invoice_prefix='OS-', next_invoice_number=1)
        other_customer = Customer.objects.create(
            business=other_business, name='Stranger', phone='9876508888')
        Sale.objects.create(
            business=other_business, customer=other_customer,
            invoice_number='OS-1', subtotal=Decimal('100.00'),
            discount=Decimal('0.00'), tax_amount=Decimal('0.00'),
            total_amount=Decimal('100.00'), paid_amount=Decimal('0.00'))
        res = self.client.get('/api/reminders/due-list/')
        names = [r['name'] for r in res.data['results']]
        self.assertEqual(names, ['Kisan Patil'])


class ReminderLogTest(ReminderTestBase):

    def _log(self, customer, channel='WHATSAPP'):
        return self.client.post('/api/reminders/log/', {
            'customer_id': customer.id, 'channel': channel,
        }, format='json')

    def test_user_confirmed_reminder_is_logged_with_fresh_balance(self):
        customer = self._customer('Kisan Patil', '9876543219')
        self._credit_bill(customer, Decimal('700.00'))
        res = self._log(customer)
        self.assertEqual(res.status_code, 201, res.data)
        self.assertEqual(Decimal(res.data['amount']), Decimal('700.00'))
        log = ReminderLog.objects.get()
        self.assertEqual(log.channel, 'WHATSAPP')
        self.assertEqual(log.sent_by, self.user)
        # The response never claims delivery:
        self.assertIn('never sends messages silently', res.data['message'])

    def test_settled_customer_cannot_be_reminded(self):
        customer = self._customer('Clean Customer', '9876543217')
        sale = self._credit_bill(customer, Decimal('500.00'))
        Payment.objects.create(
            business=self.business, payment_type='CUSTOMER_PAYMENT',
            customer=customer, sale=sale, amount=Decimal('500.00'),
            payment_method='CASH')
        res = self._log(customer)
        self.assertEqual(res.status_code, 400, res.data)
        self.assertIn('no outstanding', res.data['error'])
        self.assertEqual(ReminderLog.objects.count(), 0)

    def test_duplicate_reminder_within_cooldown_is_rejected(self):
        customer = self._customer('Kisan Patil', '9876543219')
        self._credit_bill(customer, Decimal('700.00'))
        self.assertEqual(self._log(customer).status_code, 201)
        res = self._log(customer)
        self.assertEqual(res.status_code, 409, res.data)
        self.assertIn('recently', res.data['error'])
        self.assertEqual(ReminderLog.objects.count(), 1)

    def test_different_channels_log_independently(self):
        customer = self._customer('Kisan Patil', '9876543219')
        self._credit_bill(customer, Decimal('700.00'))
        self.assertEqual(self._log(customer, 'WHATSAPP').status_code, 201)
        self.assertEqual(self._log(customer, 'SMS').status_code, 201)
        self.assertEqual(ReminderLog.objects.count(), 2)

    def test_invalid_channel_is_rejected(self):
        customer = self._customer('Kisan Patil', '9876543219')
        self._credit_bill(customer, Decimal('700.00'))
        res = self.client.post('/api/reminders/log/', {
            'customer_id': customer.id, 'channel': 'EMAIL_BLAST',
        }, format='json')
        self.assertEqual(res.status_code, 400, res.data)
        self.assertEqual(ReminderLog.objects.count(), 0)

    def test_history_lists_the_shop_logs_only(self):
        customer = self._customer('Kisan Patil', '9876543219')
        self._credit_bill(customer, Decimal('700.00'))
        self._log(customer, 'SMS')
        res = self.client.get('/api/reminders/history/')
        self.assertEqual(res.status_code, 200, res.data)
        self.assertEqual(res.data['count'], 1)
        row = res.data['results'][0]
        self.assertEqual(row['channel'], 'SMS')
        self.assertEqual(row['customer'], 'Kisan Patil')
