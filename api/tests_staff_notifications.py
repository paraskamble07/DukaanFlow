"""Staff management + notifications endpoint tests.

Covers the pieces that make staff login real (the RBAC layer itself is
already covered by api/tests_security.py):

  * the owner can list, create, re-grant and deactivate staff;
  * unknown module names are rejected (grants can never escape the RBAC map);
  * staff/staff-of-other-shop/anonymous callers are refused;
  * a deactivated staff login can no longer authenticate;
  * notifications are derived from the live books, not stored state.
"""
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import UserProfile
from businesses.models import Business
from customers.models import Customer
from products.models import Category, Product


class StaffAndNotificationsTestBase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='staff_owner@dukaanflow.com',
            email='staff_owner@dukaanflow.com',
            password='Password123!', first_name='Vikas')
        self.business = Business.objects.create(
            owner=self.user, name='Vikas Mobile Hub', owner_name='Vikas',
            phone='9811223344', email='staff_owner@dukaanflow.com',
            next_invoice_number=1)
        UserProfile.objects.create(
            user=self.user, business=self.business,
            phone='9811223344', role='OWNER')
        self._login('staff_owner@dukaanflow.com', 'Password123!')

    def _login(self, email, password):
        res = self.client.post('/api/auth/login/',
                               {'email': email, 'password': password},
                               format='json')
        self.assertEqual(res.status_code, 200, res.data)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {res.data['tokens']['access']}")

    def _other_shop(self):
        user = User.objects.create_user(
            username='other_shop@dukaanflow.com',
            email='other_shop@dukaanflow.com', password='Password123!')
        business = Business.objects.create(
            owner=user, name='Other Shop', owner_name='Other',
            phone='9999999999', next_invoice_number=1)
        UserProfile.objects.create(user=user, business=business, role='OWNER')
        return business

    def _add_staff(self, email='jitender@dukaanflow.com', password='Staff12345!',
                   permissions=('sales', 'customers')):
        return self.client.post('/api/staff/', {
            'email': email, 'password': password,
            'first_name': 'Jitender', 'phone': '9876554321',
            'permissions': list(permissions),
        }, format='json')


class StaffManagementTest(StaffAndNotificationsTestBase):
    def test_owner_can_list_staff_with_allowed_modules(self):
        res = self.client.get('/api/staff/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['results'], [])
        self.assertIn('customers', res.data['allowed_modules'])
        self.assertIn('sales', res.data['allowed_modules'])

    def test_owner_can_add_staff_with_module_grants(self):
        res = self._add_staff()
        self.assertEqual(res.status_code, 201, res.data)
        self.assertEqual(res.data['email'], 'jitender@dukaanflow.com')
        self.assertEqual(res.data['permissions'], ['customers', 'sales'])
        self.assertTrue(res.data['is_active'])

        profile = UserProfile.objects.get(user__email='jitender@dukaanflow.com')
        self.assertEqual(profile.role, 'STAFF')
        self.assertEqual(profile.business, self.business)

    def test_added_staff_can_log_in(self):
        self._add_staff()
        res = self.client.post('/api/auth/login/', {
            'email': 'jitender@dukaanflow.com', 'password': 'Staff12345!',
        }, format='json')
        self.assertEqual(res.status_code, 200, res.data)
        self.assertEqual(res.data['user']['profile']['role'], 'STAFF')

        # And immediately gets the owner's business attached.
        self.assertEqual(res.data['business']['name'], 'Vikas Mobile Hub')

    def test_staff_with_grants_can_use_granted_module_only(self):
        self._add_staff()
        self._login('jitender@dukaanflow.com', 'Staff12345!')
        # Granted: customers.
        res = self.client.get('/api/customers/')
        self.assertEqual(res.status_code, 200, res.data)
        # Not granted: expenses -> 403 from the RBAC layer.
        res = self.client.get('/api/expenses/')
        self.assertEqual(res.status_code, 403)

    def test_staff_cannot_create_staff(self):
        self._add_staff()
        self._login('jitender@dukaanflow.com', 'Staff12345!')
        res = self.client.post('/api/staff/', {
            'email': 'intruder@dukaanflow.com', 'password': 'Pass12345!',
            'permissions': ['sales'],
        }, format='json')
        self.assertEqual(res.status_code, 403)
        self.assertFalse(User.objects.filter(email='intruder@dukaanflow.com').exists())

    def test_unknown_module_is_rejected(self):
        res = self._add_staff(permissions=('sales', 'root', 'superuser'))
        self.assertEqual(res.status_code, 400, res.data)
        self.assertFalse(User.objects.filter(email='jitender@dukaanflow.com').exists())

    def test_duplicate_email_is_rejected(self):
        self._add_staff()
        res = self._add_staff()
        self.assertEqual(res.status_code, 409, res.data)
        self.assertEqual(res.data['code'], 'DUPLICATE_EMAIL')

    def test_short_password_is_rejected(self):
        res = self._add_staff(password='123')
        self.assertEqual(res.status_code, 400, res.data)

    def test_owner_can_update_grants(self):
        self._add_staff()
        profile = UserProfile.objects.get(user__email='jitender@dukaanflow.com')
        res = self.client.patch(f'/api/staff/{profile.id}/', {
            'permissions': ['sales', 'customers', 'payments'],
            'phone': '9876500000',
        }, format='json')
        self.assertEqual(res.status_code, 200, res.data)
        profile.refresh_from_db()
        self.assertEqual(profile.permissions, ['customers', 'payments', 'sales'])
        self.assertEqual(profile.phone, '9876500000')

    def test_owner_can_deactivate_staff_and_login_then_fails(self):
        self._add_staff()
        profile = UserProfile.objects.get(user__email='jitender@dukaanflow.com')
        res = self.client.delete(f'/api/staff/{profile.id}/')
        self.assertEqual(res.status_code, 200, res.data)

        profile.refresh_from_db()
        self.assertFalse(profile.user.is_active)  # account kept, login disabled
        profile.user.refresh_from_db()
        self.assertFalse(profile.user.is_active)

        login_res = self.client.post('/api/auth/login/', {
            'email': 'jitender@dukaanflow.com', 'password': 'Staff12345!',
        }, format='json')
        self.assertEqual(login_res.status_code, 401)

        # And the owner can reactivate.
        res = self.client.patch(f'/api/staff/{profile.id}/', {'reactivate': True},
                                format='json')
        self.assertEqual(res.status_code, 200, res.data)
        self.assertTrue(res.data['is_active'])

    def test_owner_of_shop_a_cannot_touch_shop_b_staff(self):
        other = self._other_shop()
        other_staff = UserProfile.objects.create(
            user=User.objects.create_user(
                username='b_staff@dukaanflow.com', password='Staff12345!'),
            business=other, role='STAFF', permissions=['sales'])
        res = self.client.delete(f'/api/staff/{other_staff.pk}/')
        self.assertEqual(res.status_code, 404)
        self.assertTrue(User.objects.get(username='b_staff@dukaanflow.com').is_active)

    def test_anonymous_caller_refused(self):
        self.client.credentials()  # drop the token
        res = self.client.get('/api/staff/')
        self.assertEqual(res.status_code, 401)


class NotificationsTest(StaffAndNotificationsTestBase):
    def setUp(self):
        super().setUp()
        category = Category.objects.create(business=self.business, name='Accessories')
        Product.objects.create(
            business=self.business, category=category, name='USB-C Cable',
            purchase_price=Decimal('60.00'), selling_price=Decimal('150.00'),
            stock_quantity=0, min_stock=2)  # out of stock
        Product.objects.create(
            business=self.business, category=category, name='Screen Guard',
            purchase_price=Decimal('20.00'), selling_price=Decimal('80.00'),
            stock_quantity=1, min_stock=2)  # low
        self.customer = Customer.objects.create(
            business=self.business, name='Mahesh', phone='9899001122')

    def test_notifications_reflect_live_books(self):
        res = self.client.get('/api/notifications/')
        self.assertEqual(res.status_code, 200, res.data)
        types = {n['type'] for n in res.data['results']}
        self.assertIn('LOW_STOCK', types)

        low = next(n for n in res.data['results'] if n['type'] == 'LOW_STOCK')
        self.assertEqual(low['count'], 2)
        self.assertEqual(len(low['items']), 2)

    def test_khata_due_notification_only_when_owed(self):
        # No sales -> no dues -> no KHATA_DUE notification.
        res = self.client.get('/api/notifications/')
        self.assertNotIn('KHATA_DUE', {n['type'] for n in res.data['results']})

        from sales.models import Sale
        Sale.objects.create(
            business=self.business, customer=self.customer,
            invoice_number='INV-1', total_amount=Decimal('500.00'),
            paid_amount=Decimal('0.00'))
        res = self.client.get('/api/notifications/')
        due = next(n for n in res.data['results'] if n['type'] == 'KHATA_DUE')
        self.assertEqual(due['count'], 1)
        self.assertEqual(due['total'], 500.0)
        self.assertEqual(due['items'][0]['name'], 'Mahesh')

    def test_notifications_recompute_on_payment(self):
        from sales.models import Sale
        sale = Sale.objects.create(
            business=self.business, customer=self.customer,
            invoice_number='INV-1', total_amount=Decimal('500.00'),
            paid_amount=Decimal('0.00'))
        res = self.client.post('/api/payments/customer/', {
            'customer_id': self.customer.id, 'amount': '500.00',
            'payment_method': 'CASH',
        }, format='json')
        self.assertEqual(res.status_code, 201, res.data)

        res = self.client.get('/api/notifications/')
        self.assertNotIn('KHATA_DUE',
                         {n['type'] for n in res.data['results']})
