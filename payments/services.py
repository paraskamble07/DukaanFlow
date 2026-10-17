"""Khata settlement services.

The customer-level balance is always derived: outstanding = total billed
less every recorded CUSTOMER_PAYMENT. That number is the source of truth
and is never written to a column.

The *per-invoice* state (Sale.paid_amount / due_amount / payment_status)
is derived too: it must reflect the money actually settled against that
bill. Historically a manual repayment recorded only a Payment row and left
the invoice rows untouched, so a customer could be fully settled while
their bills still showed "Due" — the ledger and the sales screen disagreed.
`resettle_customer` recomputes the invoice state from the payment history,
so bill rows can never drift from the books again.

Rules:
  * a Payment row linked to a Sale (created at checkout) settles that bill;
  * unlinked payments (manual Khata repayments) settle open bills FIFO
    (oldest bill first);
  * settlement is capped at each bill's total — overpayments are rejected
    upstream, so leftover money beyond all bills is not fabricated;
  * the whole recompute is deterministic and idempotent: calling it again
    with the same history changes nothing.
"""
from decimal import Decimal

from django.db import transaction

from payments.models import Payment
from sales.models import Sale

ZERO = Decimal('0.00')


def resettle_customer(customer):
    """Recompute every open-bill column of `customer` from its payments.

    Must run inside `transaction.atomic()` (uses select_for_update).
    Returns the list of (sale_id, invoice_number, settled) allocations so
    callers can report what a repayment closed.
    """
    sales = list(
        Sale.objects.select_for_update()
        .filter(customer=customer)
        .order_by('sale_date', 'id')
    )
    payments = list(
        Payment.objects.filter(customer=customer, payment_type='CUSTOMER_PAYMENT')
        .order_by('payment_date', 'id')
    )

    # Reset, then rebuild from scratch: this is what makes the operation
    # idempotent and able to repair pre-existing drift.
    for sale in sales:
        sale.paid_amount = ZERO

    # Pass 1 — honour explicit links (checkout-time partial payments stay
    # on the bill they were received for, capped at the bill total).
    linked_by_sale = {}
    unlinked_total = ZERO
    for payment in payments:
        if payment.sale_id is not None and any(s.id == payment.sale_id for s in sales):
            linked_by_sale[payment.sale_id] = \
                linked_by_sale.get(payment.sale_id, ZERO) + payment.amount
        else:
            unlinked_total += payment.amount

    for sale in sales:
        sale.paid_amount = min(linked_by_sale.get(sale.id, ZERO), sale.total_amount)

    # Pass 2 — manual repayments settle the oldest open bills first.
    remaining = unlinked_total
    for sale in sales:
        if remaining <= 0:
            break
        room = sale.total_amount - sale.paid_amount
        if room <= 0:
            continue
        applied = min(room, remaining)
        sale.paid_amount += applied
        remaining -= applied

    for sale in sales:
        # Sale.save() recomputes due_amount and payment_status from
        # paid_amount, so a single save keeps all three columns consistent.
        sale.save()

    return [
        {
            'sale_id': sale.id,
            'invoice_number': sale.invoice_number,
            'settled': str(sale.paid_amount.quantize(Decimal('0.01'))),
            'due': str(sale.due_amount.quantize(Decimal('0.01'))),
            'status': sale.payment_status,
        }
        for sale in sales
    ]


def settle_after_payment(customer):
    """Transaction wrapper used by every code path that records a payment."""
    with transaction.atomic():
        return resettle_customer(customer)
