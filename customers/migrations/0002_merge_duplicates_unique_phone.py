"""Merge duplicate customers of a shop, then enforce one customer per phone.

Applies on every environment once. For each shop, customers sharing the same
real mobile number (see core.utils.customer_duplicate_key) are merged into a
single canonical record:

  * canonical = the one with the most bills+payments (activity), ties broken
    by the oldest record;
  * every Sale, Payment and MobileDevice row pointing at a duplicate is
    re-pointed at the canonical record *before* anything is deleted, so no
    ledger line is ever lost;
  * only then are the empty duplicate rows removed.

Placeholder numbers (see core.utils.PLACEHOLDER_PHONES) are exempt —
several walk-in / unknown-number customers of one shop must stay separable,
so the partial unique constraint below excludes them as well.
"""
from django.db import migrations, models

from core.utils import PLACEHOLDER_PHONES, customer_duplicate_key


def merge_duplicate_customers(apps, schema_editor):
    Customer = apps.get_model('customers', 'Customer')
    Sale = apps.get_model('sales', 'Sale')
    Payment = apps.get_model('payments', 'Payment')
    MobileDevice = apps.get_model('inventory', 'MobileDevice')

    for business_id in Customer.objects.values_list('business_id', flat=True).distinct():
        groups = {}
        for customer in Customer.objects.filter(business_id=business_id):
            key = customer_duplicate_key(customer.phone)
            if key:
                groups.setdefault(key, []).append(customer)

        for key, group in groups.items():
            if len(group) < 2:
                continue
            # Most activity first, then the oldest record wins ties.
            def activity(c):
                return (
                    Sale.objects.filter(customer=c).count()
                    + Payment.objects.filter(customer=c).count()
                )
            ordered = sorted(group, key=lambda c: (-activity(c), c.pk))
            canonical = ordered[0]
            for dup in ordered[1:]:
                Sale.objects.filter(customer=dup).update(customer=canonical)
                Payment.objects.filter(customer=dup).update(customer=canonical)
                MobileDevice.objects.filter(customer=dup).update(customer=canonical)
                dup.delete()


def revert_merge(apps, schema_editor):
    # Forward-only repair of a data bug: the duplicate rows it removed were
    # unconstitutional (two ledgers for one person) and cannot be recreated.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0001_initial'),
        ('sales', '0001_initial'),
        ('payments', '0001_initial'),
        ('inventory', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(merge_duplicate_customers, revert_merge),
        migrations.AddConstraint(
            model_name='customer',
            constraint=models.UniqueConstraint(
                fields=('business', 'phone'),
                name='unique_customer_phone_per_business',
                # One customer per real mobile number per shop — but never
                # for placeholder numbers a shop types when the real one is
                # unknown.
                condition=~models.Q(phone__in=PLACEHOLDER_PHONES),
            ),
        ),
    ]
