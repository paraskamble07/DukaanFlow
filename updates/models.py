from django.conf import settings
from django.db import models


class AppRelease(models.Model):
    """A published Android build of the ShopZen app.

    TheFlutter client calls /api/app-updates/check/ with its own
    version_code; the endpoint compares against the newest active
    release for the platform and reports whether an update exists and
    whether the installed build has fallen below the minimum supported
    version (a mandatory, blocking update).
    """

    PLATFORMS = [
        ('android', 'Android'),
        ('ios', 'iOS'),
    ]

    platform = models.CharField(max_length=10, choices=PLATFORMS, default='android')
    version_name = models.CharField(max_length=20, verbose_name='Version name', help_text='Human version, e.g. 1.0.1')
    version_code = models.PositiveIntegerField(unique=True, verbose_name='Version code (build number)')
    minimum_supported_code = models.PositiveIntegerField(
        default=1,
        verbose_name='Minimum supported build',
        help_text='Installed builds below this number are forced to update.',
    )
    minimum_supported_name = models.CharField(
        max_length=20, default='1.0.0',
        verbose_name='Minimum supported version',
        help_text='Human label of the oldest build that may keep running.',
    )
    release_notes = models.TextField(blank=True, default='')
    download_url = models.URLField(help_text='Trusted APK/AAB manifest download URL')
    checksum_sha256 = models.CharField(
        max_length=64, blank=True, default='',
        help_text='Optional SHA-256 of the downloadable artifact.',
    )
    is_active = models.BooleanField(default=True, help_text='Inactive releases are invisible to clients.')
    released_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='published_app_releases',
    )

    class Meta:
        ordering = ['-version_code']
        verbose_name = 'App release'
        verbose_name_plural = 'App releases'

    def __str__(self):
        return f'{self.platform} v{self.version_name} ({self.version_code})'
