"""Tests for UPI collect-QR + manual payment confirmation (Phase 6).

The core rule under test: **scanning a QR is never a payment.** The QR
endpoint only issues a collect request; money moves in the books solely
through the authorized, server-validated manual payment endpoint.
"""
import base64
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
from payments.upi_service import build_upi_uri, parse_money


def _owner(email, role='OWNER'):
    user = User.objects.create_user(email=email, username=email, password='Test@12345')
    UserProfile.objects.create(user=user, role=role, phone='9999900000')
    return user


def _business(owner, name, phone, upi_id=None):
    return Business.objects.create(
        owner=owner, name=name, owner_name=owner.email.split('@')[0].title(),
        phone=phone, email=f'{name}@shop.test', city='Pune', state='Maharashtra',
        address='Shop 12, Market Road', pincode='411001', upi_id=upi_id,
    )


class UpiQrTest(TestCase):
    def setUp(self):
        self.owner = _owner('upi@qr.test')
        self.business = _business(self.owner, 'QR Shop', '9000000031', upi_id='qrshop@okaxis')
        self.other_owner = _owner('other@qr.test')
        self.other_business = _business(self.other_owner, 'Other Shop', '9000000032')

        self.client = APIClient()
        res = self.client.post('/api/auth/login/', {
            'email': 'upi@qr.test', 'password': 'Test@12345'}, format='json')
        self.assertEqual(res.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {res.data['tokens']['access']}")

        self.customer = Customer.objects.create(
            business=self.business, name='Suresh Patil', phone='9822000011')
        self.product = Product.objects.create(
            business=self.business, name='Screen Guard', selling_price=Decimal('300.00'),
            purchase_price=Decimal('120.00'), stock_quantity=20,
        )

    def _sale(self, total, days_ago=0):
        sale = Sale.objects.create(
            business=self.business, customer=self.customer,
            invoice_number=f'UPI-{Sale.objects.count() + 1}',
            payment_status='UNPAID', payment_method='CASH',
            total_amount=total, paid_amount=Decimal('0.00'),
            sale_date=timezone.now() - timedelta(days=days_ago),
        )
        SaleItem.objects.create(
            sale=sale, product=self.product, quantity=1,
            unit_price=total, total_price=total,
        )
        return sale

    # ---------- UPI URI / QR building ----------

    def test_parse_money_rejects_garbage_and_non_positive(self):
        self.assertIsNone(parse_money('abc'))
        self.assertIsNone(parse_money('0'))
        self.assertIsNone(parse_money('-10'))
        self.assertIsNone(parse_money(None))
        self.assertEqual(parse_money(' 1499.5 '), Decimal('1499.50'))

    def test_build_upi_uri_format(self):
        uri = build_upi_uri('shop@okaxis', 'QR Shop', Decimal('1200'), 'Khata')
        self.assertTrue(uri.startswith('upi://pay?pa=shop%40okaxis&pn=QR%20Shop'))
        self.assertIn('&am=1200.00&cu=INR', uri)
        self.assertIn('&tn=Khata', uri)

    def test_build_upi_uri_without_amount(self):
        uri = build_upi_uri('shop@okaxis', 'QR Shop')
        self.assertNotIn('&am=', uri)
        self.assertNotIn('&cu=', uri)

    # ---------- Endpoint ----------

    def test_qr_returns_outstanding_amount_and_png(self):
        self._sale(Decimal('1499.00'))
        res = self.client.get(f'/api/customers/{self.customer.id}/upi-qr/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertEqual(res.data['upi_id'], 'qrshop@okaxis')
        self.assertEqual(res.data['payee_name'], 'QR Shop')
        self.assertEqual(res.data['amount'], '1499.00')
        self.assertEqual(res.data['amount_source'], 'outstanding')
        self.assertEqual(res.data['currency'], 'INR')
        self.assertIn('upi://pay?pa=qrshop%40okaxis', res.data['upi_uri'])
        self.assertIn('Suresh Patil', res.data['note'])
        # A scan is never a confirmation
        self.assertIs(res.data['confirmed'], False)

        png = base64.b64decode(res.data['qr_png_base64'])
        self.assertTrue(png.startswith(b'\x89PNG'))

    def test_qr_amount_defaults_to_recomputed_outstanding(self):
        """Amount must be recomputed server-side, not taken on faith."""
        self._sale(Decimal('1000.00'))
        Payment.objects.create(
            business=self.business, customer=self.customer,
            payment_type='CUSTOMER_PAYMENT', amount=Decimal('400.00'),
        )
        res = self.client.get(f'/api/customers/{self.customer.id}/upi-qr/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['amount'], '600.00')

    def test_qr_custom_amount_override(self):
        self._sale(Decimal('1000.00'))
        res = self.client.get(f'/api/customers/{self.customer.id}/upi-qr/?amount=250')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['amount'], '250.00')
        self.assertEqual(res.data['amount_source'], 'custom')

    def test_qr_invalid_custom_amount_400(self):
        self._sale(Decimal('1000.00'))
        for bad in ('abc', '0', '-5'):
            res = self.client.get(f'/api/customers/{self.customer.id}/upi-qr/?amount={bad}')
            self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST, bad)

    def test_qr_without_configured_upi_id_400(self):
        self._sale(Decimal('500.00'))
        self.business.upi_id = None
        self.business.save(update_fields=['upi_id'])
        res = self.client.get(f'/api/customers/{self.customer.id}/upi-qr/')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('upi_id', res.data['error'].lower())
        self.assertNotIn(res.data['error'], '')  # actionable guidance present

    def test_qr_tenant_isolation_404(self):
        other_customer = Customer.objects.create(
            business=self.other_business, name='Rival Client', phone='9333300000')
        res = self.client.get(f'/api/customers/{other_customer.id}/upi-qr/')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_qr_unauthenticated_rejected(self):
        self.client.credentials()
        res = self.client.get(f'/api/customers/{self.customer.id}/upi-qr/')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_qr_available_to_authorized_employee(self):
        """Staff granted customers+payments may show the QR (collect only)."""
        employee = User.objects.create_user(
            email='emp@qr.test', username='emp@qr.test', password='Test@12345')
        UserProfile.objects.create(user=employee, role='STAFF',
                                   business=self.business, phone='9001112233',
                                   permissions=['customers', 'payments'])
        self.client.credentials()
        res = self.client.post('/api/auth/login/', {
            'email': 'emp@qr.test', 'password': 'Test@12345'}, format='json')
        self.assertEqual(res.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {res.data['tokens']['access']}")
        self._sale(Decimal('300.00'))
        res = self.client.get(f'/api/customers/{self.customer.id}/upi-qr/')
        self.assertEqual(res.status_code, 200)

    # ---------- Manual confirmation ----------

    def test_manual_payment_records_and_updates_due(self):
        self._sale(Decimal('800.00'))
        res = self.client.post('/api/payments/customer/', {
            'customer_id': self.customer.id,
            'amount': '500.00',
            'payment_method': 'UPI',
            'reference_number': 'UTR1234',
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['remaining_due'], 300.0)
        self.assertEqual(
            Payment.objects.get(customer=self.customer).reference_number, 'UTR1234')

    def test_overpayment_rejected_with_outstanding_in_message(self):
        """The books must never silently swallow money above the due."""
        self._sale(Decimal('800.00'))
        res = self.client.post('/api/payments/customer/', {
            'customer_id': self.customer.id,
            'amount': '801.00',
            'payment_method': 'UPI',
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('outstanding', res.data['error'].lower())
        self.assertEqual(Payment.objects.filter(customer=self.customer).count(), 0)
        self.assertEqual(self.customer.get_outstanding_due(), Decimal('800.00'))

    def test_payment_on_settled_account_rejected(self):
        self._sale(Decimal('800.00'))
        res1 = self.client.post('/api/payments/customer/', {
            'customer_id': self.customer.id, 'amount': '800.00',
            'payment_method': 'CASH',
        }, format='json')
        self.assertEqual(res1.status_code, 201)
        res2 = self.client.post('/api/payments/customer/', {
            'customer_id': self.customer.id, 'amount': '1.00',
            'payment_method': 'UPI',
        }, format='json')
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Payment.objects.filter(customer=self.customer).count(), 1)

    def test_payment_for_other_shops_customer_rejected(self):
        other_customer = Customer.objects.create(
            business=self.other_business, name='Rival Client', phone='9333300000')
        res = self.client.post('/api/payments/customer/', {
            'customer_id': other_customer.id, 'amount': '10.00',
            'payment_method': 'CASH',
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
