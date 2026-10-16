# Generated for Phase 11 — IMEI history: link stock movements to the
# specific IMEI-tracked unit they concern. Purely additive (nullable FK),
# no data is rewritten and existing rows stay valid.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='stockmovement',
            name='device',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='movements', to='inventory.mobiledevice'),
        ),
    ]
