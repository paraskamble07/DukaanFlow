"""Tests for the Payment Reminders feature (Phase 4)."""
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import UserProfile
from businesses.models import Business
from customers.models import Customer
from payments.models import Payment
from sales.models import Sale, SaleItem
from products.models import Product
from reminders.models import ReminderLog, ReminderSetting


def _owner(email='owner@remind.test'):
    user = User.objects.create_user(email=email, username=email, password='Test@12345')
    UserProfile.objects.create(user=user, role='OWNER', phone='9999900000')
    return user


def _login(client, email, password='Test@12345'):
    res = client.post('/api/auth/login/', {'email': email, 'password': password}, format='json')
    assert res.status_code == 200, res.data
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {res.data['tokens']['access']}")


def _business(owner, name, phone='9000000001'):
    return Business.objects.create(
        owner=owner, name=name, owner_name=owner.email.split('@')[0].title(),
        phone=phone, email=f'{name}@shop.test', city='Pune', state='Maharashtra',
        address='Shop 12, Market Road', pincode='411001',
    )


class ReminderFlowTest(APITestCase):
    def setUp(self):
        self.owner = _owner()
        self.business = _business(self.owner, 'Reminder Shop')
        self.other_owner = _owner('other@remind.test')
        self.other_business = _business(self.other_owner, 'Other Shop', phone='9000000002')
        _login(self.client, self.owner.email)

        self.customer = Customer.objects.create(
            business=self.business, name='Ramesh Kumar', phone='9876543210')
        self.product = Product.objects.create(
            business=self.business, name='Sim Tray', selling_price=Decimal('100.00'),
            purchase_price=Decimal('60.00'), stock_quantity=50,
        )

    def _credit_sale(self, customer, total, days_ago=0, paid=Decimal('0.00')):
        sale = Sale.objects.create(
            business=self.business, customer=customer,
            invoice_number=f'INV-{customer.id}-{Sale.objects.count()+1}',
            total_amount=total, paid_amount=paid,
            sale_date=timezone.now() - timedelta(days=days_ago),
        )
        SaleItem.objects.create(
            sale=sale, product=self.product, quantity=1,
            unit_price=total, total_price=total,
        )
        return sale

    def _pay(self, customer, amount):
        Payment.objects.create(
            business=self.business, customer=customer,
            payment_type='CUSTOMER_PAYMENT', amount=amount,
        )

    # ---------- due list ----------

    def test_due_list_shows_outstanding_with_shop_details_in_url(self):
        self._credit_sale(self.customer, Decimal('5000.00'), days_ago=45)
        res = self.client.get(reverse('api:reminder_due_list'))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['results']), 1)
        row = res.data['results'][0]
        self.assertEqual(row['customer_id'], self.customer.id)
        self.assertEqual(Decimal(row['outstanding']), Decimal('5000.00'))
        self.assertEqual(row['status'], 'OVERDUE')
        # Shop details must be baked into the composer message.
        self.assertIn('Reminder%20Shop', row['whatsapp_url'])
        self.assertIn('9876543210', row['whatsapp_url'])
        self.assertIn('Shop%2012', row['whatsapp_url'])
        # Due date is derived from credit days (default 30) + sale date.
        self.assertIsNotNone(row['due_date'])
        self.assertIn('5000', row['sms_body'].replace(',', ''))

    def test_settled_balances_excluded_from_due_list(self):
        self._credit_sale(self.customer, Decimal('3000.00'), days_ago=10)
        self._pay(self.customer, Decimal('3000.00'))
        res = self.client.get(reverse('api:reminder_due_list'))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['results'], [])

    def test_status_due_soon_when_within_window(self):
        self._credit_sale(self.customer, Decimal('1000.00'), days_ago=25)
        res = self.client.get(reverse('api:reminder_due_list'))
        self.assertEqual(res.data['results'][0]['status'], 'DUE_SOON')

    def test_credit_days_setting_changes_due_date(self):
        ReminderSetting.objects.create(business=self.business, credit_days=60, due_soon_days=7)
        self._credit_sale(self.customer, Decimal('1000.00'), days_ago=25)
        res = self.client.get(reverse('api:reminder_due_list'))
        self.assertEqual(res.data['results'][0]['status'], 'DUE')

    # ---------- logging ----------

    def test_log_reminder_and_history(self):
        sale = self._credit_sale(self.customer, Decimal('5000.00'), days_ago=45)
        res = self.client.post(reverse('api:reminder_log_create'), {
            'customer_id': self.customer.id, 'channel': 'WHATSAPP',
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED, res.data)
        self.assertEqual(Decimal(res.data['amount']), Decimal('5000.00'))
        self.assertEqual(ReminderLog.objects.count(), 1)
        log = ReminderLog.objects.first()
        self.assertEqual(log.sale, sale)
        self.assertEqual(log.business, self.business)
        self.assertEqual(log.sent_by, self.owner)

        res = self.client.get(reverse('api:reminder_history'))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['count'], 1)
        self.assertEqual(res.data['results'][0]['customer'], 'Ramesh Kumar')

    def test_log_rejects_settled_balance(self):
        self._credit_sale(self.customer, Decimal('2000.00'), days_ago=1)
        self._pay(self.customer, Decimal('2000.00'))
        res = self.client.post(reverse('api:reminder_log_create'), {
            'customer_id': self.customer.id, 'channel': 'SMS',
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(ReminderLog.objects.count(), 0)

    def test_log_rejects_duplicate_within_cooldown(self):
        self._credit_sale(self.customer, Decimal('2000.00'), days_ago=40)
        res1 = self.client.post(reverse('api:reminder_log_create'), {
            'customer_id': self.customer.id, 'channel': 'WHATSAPP',
        })
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)
        res2 = self.client.post(reverse('api:reminder_log_create'), {
            'customer_id': self.customer.id, 'channel': 'WHATSAPP',
        })
        self.assertEqual(res2.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(ReminderLog.objects.count(), 1)

    def test_log_recomputes_balance_after_partial_payment(self):
        self._credit_sale(self.customer, Decimal('5000.00'), days_ago=40)
        self._pay(self.customer, Decimal('3000.00'))
        res = self.client.post(reverse('api:reminder_log_create'), {
            'customer_id': self.customer.id, 'channel': 'SMS',
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Decimal(res.data['amount']), Decimal('2000.00'))

    def test_log_rejects_other_business_customer(self):
        other_customer = Customer.objects.create(
            business=self.other_business, name='Secret Client', phone='9111111111')
        res = self.client.post(reverse('api:reminder_log_create'), {
            'customer_id': other_customer.id, 'channel': 'WHATSAPP',
        })
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_log_rejects_invalid_channel(self):
        res = self.client.post(reverse('api:reminder_log_create'), {
            'customer_id': self.customer.id, 'channel': 'EMAIL',
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_due_list_tenant_isolation(self):
        other_customer = Customer.objects.create(
            business=self.other_business, name='Secret Client', phone='9111111111')
        other_product = Product.objects.create(
            business=self.other_business, name='Case', selling_price=Decimal('50.00'),
            purchase_price=Decimal('30.00'), stock_quantity=10,
        )
        other_sale = Sale.objects.create(
            business=self.other_business, customer=other_customer,
            invoice_number='INV-OTHER-1', total_amount=Decimal('700.00'),
        )
        SaleItem.objects.create(
            sale=other_sale, product=other_product, quantity=1,
            unit_price=Decimal('700.00'), total_price=Decimal('700.00'),
        )
        other_owner_login = self.client_class()
        _login(other_owner_login, self.other_owner.email)
        res = other_owner_login.get(reverse('api:reminder_due_list'))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual([r['name'] for r in res.data['results']], ['Secret Client'])
        # The first shop's reminder list must not leak the other customer.
        own = self.client.get(reverse('api:reminder_due_list'))
        self.assertNotIn('Secret Client', [r['name'] for r in own.data['results']])

    def test_anonymous_denied(self):
        anon = self.client_class()
        res = anon.get(reverse('api:reminder_due_list'))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        res = anon.post(reverse('api:reminder_log_create'), {'customer_id': 1, 'channel': 'SMS'})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
