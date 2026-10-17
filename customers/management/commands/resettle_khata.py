"""Repair stale per-invoice Khata settlements.

Before the settlement fix, a manual repayment recorded only a Payment row and
left the bills untouched, so fully-settled customers still had invoices
showing "Due". This command replays every customer's payment history through
the same deterministic recompute the API uses now:

    python manage.py resettle_khata            # every shop
    python manage.py resettle_khata --business 3    # one shop only

It is idempotent — safe to run repeatedly — and prints what changed.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from businesses.models import Business
from customers.models import Customer
from payments.services import resettle_customer
from sales.models import Sale


class Command(BaseCommand):
    help = 'Recompute per-invoice paid/due/status from each customer\'s payment history.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--business', type=int, default=None,
            help='Limit the repair to a single business id.')

    def handle(self, *args, **options):
        business_id = options['business']
        customers = Customer.objects.all()
        if business_id is not None:
            customers = customers.filter(business_id=business_id)
            if not customers.exists():
                raise CommandError(f'No customers found for business id {business_id}.')

        repaired, touched_bills = 0, 0
        for customer in customers.iterator():
            with transaction.atomic():
                before = {
                    s.id: (s.paid_amount, s.due_amount, s.payment_status)
                    for s in Sale.objects.filter(customer=customer)
                }
                resettle_customer(customer)
                after = {
                    s.id: (s.paid_amount, s.due_amount, s.payment_status)
                    for s in Sale.objects.filter(customer=customer)
                }
            changed = [sid for sid in before
                       if before[sid] != after.get(sid)]
            if changed:
                repaired += 1
                touched_bills += len(changed)
                self.stdout.write(self.style.WARNING(
                    f'  customer {customer.id} ({customer.name}): '
                    f'{len(changed)} bill(s) re-settled'))

        if repaired:
            self.stdout.write(self.style.SUCCESS(
                f'\nRe-settled {touched_bills} bill(s) across {repaired} '
                f'customer record(s). Books were not touched — only the '
                f'per-invoice paid/due/status columns.'))
        else:
            self.stdout.write(self.style.SUCCESS(
                '\nEvery customer is already settled consistently. Nothing changed.'))
