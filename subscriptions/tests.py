from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import UserProfile
from businesses.models import Business
from .models import SubscriptionPaymentRequest, AdminAuditLog


class SubscriptionPaymentFlowTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user('shopowner@test.com', 'shopowner@test.com', 'pass12345')
        self.business = Business.objects.create(
            owner=self.owner, name='Test Shop', owner_name='Test Owner', phone='9876500000',
        )
        UserProfile.objects.create(user=self.owner, business=self.business, role='OWNER')

        self.admin = User.objects.create_superuser('shopzen_admin', 'admin@shopzen.app', 'adminpass1')
        UserProfile.objects.create(user=self.admin, role='SHOPZEN_ADMIN')

        self.client = APIClient()
        self.login_owner = APIClient()
        self.login_admin = APIClient()

        r = self.login_owner.post('/api/auth/login/', {'email': 'shopowner@test.com', 'password': 'pass12345'})
        self.owner_token = r.json()['tokens']['access']
        r = self.login_admin.post('/api/auth/login/', {'email': 'shopzen_admin', 'password': 'adminpass1'})
        self.admin_token = r.json()['tokens']['access']
        self.login_owner.credentials(HTTP_AUTHORIZATION=f'Bearer {self.owner_token}')
        self.login_admin.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')

    def test_payment_config_requires_auth_and_hides_nothing_hardcoded(self):
        anon = APIClient().get('/api/subscription/payment-config/')
        self.assertEqual(anon.status_code, 401)
        res = self.login_owner.get('/api/subscription/payment-config/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['price'], 30)

    def test_submit_creates_pending_and_does_not_activate(self):
        res = self.login_owner.post('/api/subscription/payment-request/',
                                    {'amount': 30, 'upi_reference': 'UTR1'})
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()['status'], 'PENDING')
        req = SubscriptionPaymentRequest.objects.get(business=self.business)
        self.assertEqual(req.status, 'PENDING')
        # Premium NOT extended by submission alone
        status_res = self.login_owner.get('/api/subscription/status/')
        end = status_res.json()['end_date']
        self.assertEqual(SubscriptionPaymentRequest.objects.count(), 1)

    def test_duplicate_pending_submit_blocked(self):
        self.login_owner.post('/api/subscription/payment-request/', {'amount': 30})
        res = self.login_owner.post('/api/subscription/payment-request/', {'amount': 30})
        self.assertEqual(res.status_code, 400)
        self.assertEqual(SubscriptionPaymentRequest.objects.count(), 1)

    def test_normal_owner_cannot_access_admin_apis(self):
        self.assertEqual(self.login_owner.get('/api/admin/dashboard/').status_code, 403)
        self.assertEqual(self.login_owner.get('/api/admin/payment-requests/').status_code, 403)
        res = self.login_owner.post('/api/admin/payment-requests/1/review/', {'action': 'APPROVE'})
        self.assertIn(res.status_code, (403, 404))

    def test_admin_approve_activates_and_extends(self):
        self.login_owner.post('/api/subscription/payment-request/',
                              {'amount': 60, 'upi_reference': 'UTR2'})  # 2 months
        req = SubscriptionPaymentRequest.objects.get(business=self.business)
        before_end = self.business.subscription_end_date
        res = self.login_admin.post(f'/api/admin/payment-requests/{req.id}/review/', {'action': 'APPROVE'})
        self.assertEqual(res.status_code, 200)
        self.business.refresh_from_db()
        from datetime import timedelta
        # ₹60 = 2 months → +60 days stacked on the existing trial end date
        self.assertEqual(self.business.subscription_end_date,
                         max(before_end, self.business.subscription_start_date) + timedelta(days=60))
        req.refresh_from_db()
        self.assertEqual(req.status, 'APPROVED')
        self.assertEqual(req.reviewed_by, self.admin)
        self.assertTrue(AdminAuditLog.objects.filter(action='subscription_approve').exists())

    def test_double_approval_blocked(self):
        self.login_owner.post('/api/subscription/payment-request/', {'amount': 30})
        req = SubscriptionPaymentRequest.objects.get(business=self.business)
        first = self.login_admin.post(f'/api/admin/payment-requests/{req.id}/review/', {'action': 'APPROVE'})
        self.assertEqual(first.status_code, 200)
        second = self.login_admin.post(f'/api/admin/payment-requests/{req.id}/review/', {'action': 'APPROVE'})
        self.assertEqual(second.status_code, 404)
        self.business.refresh_from_db()
        # No accidental double extension: expiry unchanged after 2nd attempt
        end_after_first = self.business.subscription_end_date
        second = self.login_admin.post(f'/api/admin/payment-requests/{req.id}/review/', {'action': 'APPROVE'})
        self.business.refresh_from_db()
        self.assertEqual(self.business.subscription_end_date, end_after_first)

    def test_reject_keeps_inactive_and_audits(self):
        self.login_owner.post('/api/subscription/payment-request/', {'amount': 30})
        req = SubscriptionPaymentRequest.objects.get(business=self.business)
        res = self.login_admin.post(f'/api/admin/payment-requests/{req.id}/review/',
                                     {'action': 'REJECT', 'reason': 'not received'})
        self.assertEqual(res.status_code, 200)
        req.refresh_from_db()
        self.assertEqual(req.status, 'REJECTED')
        self.assertEqual(req.rejection_reason, 'not received')
        self.assertTrue(AdminAuditLog.objects.filter(action='subscription_reject', result='REJECTED').exists())
        # Owner can submit a fresh request after rejection
        res2 = self.login_owner.post('/api/subscription/payment-request/', {'amount': 30})
        self.assertEqual(res2.status_code, 201)

    def test_admin_dashboard_stats(self):
        self.login_owner.post('/api/subscription/payment-request/', {'amount': 30})
        res = self.login_admin.get('/api/admin/dashboard/')
        self.assertEqual(res.status_code, 200)
        d = res.json()
        self.assertEqual(d['total_shops'], 1)
        self.assertEqual(d['pending_payment_requests'], 1)
        self.assertEqual(d['total_subscription_revenue'], '0.00')

    def test_upi_reference_stored_and_searchable(self):
        self.login_owner.post('/api/subscription/payment-request/',
                              {'amount': 30, 'upi_reference': 'SPECIALUTR9'})
        res = self.login_admin.get('/api/admin/payment-requests/?q=SPECIALUTR9')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()['requests']), 1)
        self.assertEqual(res.json()['requests'][0]['upi_reference'], 'SPECIALUTR9')
