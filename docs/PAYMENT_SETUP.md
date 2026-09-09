# ShopZen — ₹30 Payment Setup (Owner/Admin)

How to configure the ShopZen Premium ₹30/month payment so real shop owners can pay you
and you can verify their payments. Full user-facing flow: [PAYMENT_SUBSCRIPTION_GUIDE.md](PAYMENT_SUBSCRIPTION_GUIDE.md).

## 1. Configure your payment details (one-time)

Your real UPI/QR details are **stored on the server only** — never hard-coded in the app
and never committed to the repo. Set them in the Django admin (or shell):

```bash
# On Render → Shell (or locally against production DB):
python manage.py shell
>>> from subscriptions.models import SubscriptionPaymentConfig
>>> SubscriptionPaymentConfig.objects.update_or_create(
...     pk=1,
...     defaults={
...         'upi_id': 'yourname@upi',           # ← YOUR real UPI ID
...         'payee_name': 'PARAS KAMBLE',        # ← name shown on the payment screen
...         'amount': 30,
...         'instructions': 'Pay ₹30 via any UPI app to the QR/UPI ID, then enter the UPI reference number below and tap I Have Paid.',
...     })
```

The app fetches these live from `/api/subscription/payment-config/` — change them any
time without releasing a new APK. There is a test
(`test_payment_config_requires_auth_and_hides_nothing_hardcoded`) that guarantees the
server serves config from the database, not from any hard-coded value.

## 2. What the shop owner sees

Premium screen (₹30/month): your payment instructions + UPI ID + amount → the owner pays
in their UPI app → enters the reference/UTR number + date → taps **I Have Paid**.

The request is created `PENDING`. **No client can ever activate a subscription itself** —
activation happens only through your admin approval.

## 3. Verifying a payment (your job)

1. Open ShopZen on your admin-account phone → **Admin** dashboard (visible only to
   `SHOPZEN_ADMIN` accounts — everyone else gets 403).
2. **Payments tab** → you see: shop, owner, amount, reference/UTR, date/time, status.
3. Cross-check the UTR/reference in your UPI app's transaction history.
4. **Approve** → subscription becomes `ACTIVE`, start date recorded, expiry = current
   expiry + 30 days (renewals extend). Audit row written automatically.
5. **Reject** (if the payment doesn't check out) → stays inactive, your `rejection_reason`
   is shown to the owner, and they can submit again.

The owner's app reflects `ACTIVE` Premium on the next sync — no reinstall needed.

## 4. Safety rules baked in

- One pending request at a time per shop (duplicates blocked, tested).
- Double-approval is blocked (tested).
- All money math server-side; the app never decides subscription state.
- UPI IDs/config come from the server DB — nothing financial is baked into the APK.
