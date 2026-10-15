"""Tests for the App Update feature (Phase 21)."""
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import UserProfile
from updates.models import AppRelease


def _user(role, email):
    user = User.objects.create_user(email=email, username=email, password='Test@12345')
    UserProfile.objects.create(user=user, role=role, phone='9999900000')
    return user


class AppUpdateCheckTest(APITestCase):
    def setUp(self):
        super().setUp()
        # Migration 0002 seeds release v1.0.0 (build 1) in pristine
        # databases; tests must not depend on (nor collide with) that row.
        AppRelease.objects.all().delete()
        self.url = reverse('api:app_update_check')
        AppRelease.objects.create(
            platform='android', version_name='1.0.0', version_code=1,
            minimum_supported_code=1, release_notes='First release.',
            download_url='https://dukaanflow-1.onrender.com/apk/shopzen-1.0.0.apk',
        )

    def test_no_update_when_on_latest_build(self):
        res = self.client.get(self.url, {'platform': 'android', 'version_code': 1})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertFalse(res.data['update_available'])
        self.assertFalse(res.data['mandatory_update'])
        self.assertEqual(res.data['latest_version'], '1.0.0')
        self.assertEqual(res.data['latest_build_number'], 1)

    def test_update_available_when_server_build_is_newer(self):
        AppRelease.objects.create(
            platform='android', version_name='1.1.0', version_code=3,
            minimum_supported_code=1, release_notes='Faster billing + IMEI fixes.',
            download_url='https://dukaanflow-1.onrender.com/apk/shopzen-1.1.0.apk',
            checksum_sha256='a' * 64,
        )
        res = self.client.get(self.url, {'platform': 'android', 'version_code': 1})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['update_available'])
        self.assertFalse(res.data['mandatory_update'])
        self.assertEqual(res.data['latest_version'], '1.1.0')
        self.assertEqual(res.data['latest_build_number'], 3)
        self.assertEqual(res.data['checksum_sha256'], 'a' * 64)
        self.assertIn('Faster billing', res.data['release_notes'])
        self.assertIsNotNone(res.data['released_at'])
        self.assertEqual(res.data['minimum_supported_version'], '1.0.0')

    def test_mandatory_update_when_build_below_minimum(self):
        AppRelease.objects.create(
            platform='android', version_name='2.0.0', version_code=10,
            minimum_supported_code=5, minimum_supported_name='1.5.0',
            release_notes='Security update.',
            download_url='https://dukaanflow-1.onrender.com/apk/shopzen-2.0.0.apk',
        )
        res = self.client.get(self.url, {'platform': 'android', 'version_code': 2})
        self.assertTrue(res.data['update_available'])
        self.assertTrue(res.data['mandatory_update'])
        self.assertEqual(res.data['minimum_supported_version'], '1.5.0')

    def test_mandatory_flag_off_when_build_meets_minimum(self):
        AppRelease.objects.create(
            platform='android', version_name='2.0.0', version_code=10,
            minimum_supported_code=5,
            download_url='https://example.com/apk.apk',
        )
        res = self.client.get(self.url, {'platform': 'android', 'version_code': 7})
        self.assertTrue(res.data['update_available'])
        self.assertFalse(res.data['mandatory_update'])

    def test_inactive_releases_are_hidden(self):
        AppRelease.objects.create(
            platform='android', version_name='9.9.9', version_code=99,
            is_active=False, download_url='https://example.com/rollback.apk',
        )
        res = self.client.get(self.url, {'platform': 'android', 'version_code': 1})
        self.assertFalse(res.data['update_available'])
        self.assertEqual(res.data['latest_build_number'], 1)

    def test_missing_releases_returns_shape_without_update(self):
        AppRelease.objects.all().delete()
        res = self.client.get(self.url, {'platform': 'android', 'version_code': 5})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertFalse(res.data['update_available'])

    def test_invalid_version_code_rejected(self):
        res = self.client.get(self.url, {'platform': 'android', 'version_code': 'abc'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        res = self.client.get(self.url, {'platform': 'android', 'version_code': '-1'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_default_platform_is_android(self):
        res = self.client.get(self.url, {'version_code': 1})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertFalse(res.data['update_available'])


class AppReleaseAdminTest(APITestCase):
    def setUp(self):
        super().setUp()
        # Clear the seeded v1.0.0 row so publish tests start from empty.
        AppRelease.objects.all().delete()
        self.admin = _user('SHOPZEN_ADMIN', 'admin@shopzen.app')
        self.owner = _user('OWNER', 'owner@example.com')
        self.list_url = reverse('api:admin_app_release_list_create')

    def _login(self, user):
        res = self.client.post(reverse('api:login'), {'email': user.email, 'password': 'Test@12345'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + res.data['tokens']['access'])

    def test_admin_can_publish_release(self):
        self._login(self.admin)
        res = self.client.post(self.list_url, {
            'platform': 'android', 'version_name': '1.2.0', 'version_code': 5,
            'minimum_supported_code': 2, 'minimum_supported_name': '1.0.0',
            'release_notes': 'GST report fixes.',
            'download_url': 'https://dukaanflow-1.onrender.com/apk/shopzen-1.2.0.apk',
            'checksum_sha256': 'b' * 64,
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED, res.data)
        self.assertEqual(AppRelease.objects.count(), 1)
        self.assertEqual(AppRelease.objects.get().created_by, self.admin)

    def test_admin_can_list_releases(self):
        AppRelease.objects.create(platform='android', version_name='1.0.0', version_code=1)
        self._login(self.admin)
        res = self.client.get(self.list_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['results']), 1)

    def test_owner_cannot_publish_release(self):
        self._login(self.owner)
        res = self.client.post(self.list_url, {
            'platform': 'android', 'version_name': '2.0.0', 'version_code': 9,
            'download_url': 'https://evil.example.com/apk.apk',
        })
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(AppRelease.objects.count(), 0)

    def test_anonymous_cannot_list_releases(self):
        res = self.client.get(self.list_url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_validation_rejects_minimum_above_release_build(self):
        self._login(self.admin)
        res = self.client.post(self.list_url, {
            'platform': 'android', 'version_name': '1.0.0', 'version_code': 3,
            'minimum_supported_code': 10,
            'download_url': 'https://example.com/apk.apk',
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('minimum_supported_code', res.data)
