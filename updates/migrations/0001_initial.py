import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AppRelease',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('platform', models.CharField(choices=[('android', 'Android'), ('ios', 'iOS')], default='android', max_length=10)),
                ('version_name', models.CharField(help_text='Human version, e.g. 1.0.1', max_length=20, verbose_name='Version name')),
                ('version_code', models.PositiveIntegerField(unique=True, verbose_name='Version code (build number)')),
                ('minimum_supported_code', models.PositiveIntegerField(default=1, help_text='Installed builds below this number are forced to update.', verbose_name='Minimum supported build')),
                ('minimum_supported_name', models.CharField(default='1.0.0', help_text='Human label of the oldest build that may keep running.', max_length=20, verbose_name='Minimum supported version')),
                ('release_notes', models.TextField(blank=True, default='')),
                ('download_url', models.URLField(help_text='Trusted APK/AAB manifest download URL')),
                ('checksum_sha256', models.CharField(blank=True, default='', help_text='Optional SHA-256 of the downloadable artifact.', max_length=64)),
                ('is_active', models.BooleanField(default=True, help_text='Inactive releases are invisible to clients.')),
                ('released_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='published_app_releases', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'App release',
                'verbose_name_plural': 'App releases',
                'ordering': ['-version_code'],
            },
        ),
    ]
