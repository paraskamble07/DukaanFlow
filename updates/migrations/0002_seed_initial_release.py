from django.db import migrations


def seed_initial_release(apps, schema_editor):
    AppRelease = apps.get_model('updates', 'AppRelease')
    if AppRelease.objects.exists():
        return
    AppRelease.objects.create(
        platform='android',
        version_name='1.0.0',
        version_code=1,
        minimum_supported_code=1,
        minimum_supported_name='1.0.0',
        release_notes=(
            'ShopZen 1.0.0 — POS billing, inventory & IMEI tracking, khata '
            'ledger, GST & profit reports, multi-role staff permissions, '
            'offline sync and Hindi/Marathi support.'
        ),
        download_url='https://dukaanflow-1.onrender.com/static/apk/shopzen-1.0.0.apk',
    )


def remove_seed(apps, schema_editor):
    AppRelease = apps.get_model('updates', 'AppRelease')
    AppRelease.objects.filter(version_code=1, platform='android').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('updates', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_initial_release, remove_seed),
    ]
