from django.test import TestCase, Client
from django.contrib.auth.models import User
from decimal import Decimal
from businesses.models import Business, PLAN_LIMITS
from accounts.models import UserProfile
from customers.models import Customer
from products.models import Product

class MultiTenantAndAuthTest(TestCase):
    def setUp(self):
        # Create User A & Shop A
        self.user_a = User.objects.create_user(
            username='user_a@example.com',
            email='user_a@example.com',
            password='password123',
            first_name='Rahul'
        )
        self.shop_a = Business.objects.create(
            owner=self.user_a,
            name='Rahul Mobile Shop',
            owner_name='Rahul',
            phone='9811111111',
            email='user_a@example.com',
            plan_tier='FREE'
        )
        UserProfile.objects.create(user=self.user_a, business=self.shop_a, phone='9811111111')

        # Create User B & Shop B
        self.user_b = User.objects.create_user(
            username='user_b@example.com',
            email='user_b@example.com',
            password='password123',
            first_name='Amit'
        )
        self.shop_b = Business.objects.create(
            owner=self.user_b,
            name='Amit Electronics',
            owner_name='Amit',
            phone='9822222222',
            email='user_b@example.com',
            plan_tier='FREE'
        )
        UserProfile.objects.create(user=self.user_b, business=self.shop_b, phone='9822222222')

    def test_tenant_data_isolation(self):
        """Ensure Shop A cannot see or access Shop B data."""
        cust_a = Customer.objects.create(business=self.shop_a, name='Customer A', phone='9900000001')
        cust_b = Customer.objects.create(business=self.shop_b, name='Customer B', phone='9900000002')

        # Login as User A
        client_a = Client()
        client_a.login(username='user_a@example.com', password='password123')
        
        response = client_a.get('/customers/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Customer A')
        self.assertNotContains(response, 'Customer B')

        # Try to view Customer B's detail as User A -> Should return 404
        response_detail = client_a.get(f'/customers/{cust_b.pk}/')
        self.assertEqual(response_detail.status_code, 404)

    def test_plan_limits_enforcement(self):
        """Free plan enforces customer and product limits."""
        can_add, count, limit = self.shop_a.can_add_customer()
        self.assertTrue(can_add)
        self.assertEqual(limit, 50)
