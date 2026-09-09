# ShopZen — Production Setup Guide

How to go from this repository to a permanently-running production system:
`Shop Owner Phone → HTTPS → Django REST API → PostgreSQL` — with **no
laptop required** after setup.

## 1. What already exists in this repo

| Piece | Status |
|---|---|
| Django REST API (`/api/…`, JWT) | Done, 23 API tests + subscription tests pass |
| `render.yaml` blueprint | Done |
| `Procfile` (`web: gunicorn …`, `release: python manage.py migrate`) | Done |
| Pinned `requirements.txt` | Done |
| Health endpoint `/api/health/` | Done (public, no auth) |
| Static files via WhiteNoise | Done |
| ₹30 subscription, admin approval, audit trail | Done |

## 2. Deploy the backend (Render)

### One-time blueprint deploy
1. Push this repo to GitHub (already: `github.com/paraskamble07/DukaanFlow`).
2. In Render: **New → Blueprint**, pick the repo. The `render.yaml` creates
   the web service.
3. Create the free **PostgreSQL** instance in the same blueprint/region.

### Environment variables (Render dashboard)
| Variable | Value |
|---|---|
| `SECRET_KEY` | long random string (`python -c "import secrets; print(secrets.token_urlsafe(50))"`) |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `dukaanflow.onrender.com` |
| `DATABASE_URL` | Render's internal Postgres connection string |
| `CSRF_TRUSTED_ORIGINS` | `https://dukaanflow.onrender.com` |

No credentials are stored in this repo — `.env` is git-ignored and only
contains local dev values.

### Critical: auto-deploy
The **Render service must deploy the current commit**. GitHub pushes do NOT
trigger deploys when auto-deploy is OFF (verified: the GitHub deployments API
shows 0 deployments). After pushing, open Render → your service → **Manual
Deploy → Deploy latest commit**, and turn **Auto-Deploy: Yes** on so future
pushes deploy automatically.

### Verify the deploy
```bash
curl https://dukaanflow.onrender.com/api/health/
# {"status": "ok", "app": "ShopZen", "version": "1.0.0", "database": "up", ...}
```
If this 404s, the service is still running old code — do the Manual Deploy
above.

## 3. Create the ShopZen admin account

Only YOU (the ShopZen owner) should be admin. After deploy:

```bash
# Render → Shell (or local against production DB):
python manage.py createsuperuser        # your own email + strong password
python manage.py shell
>>> from django.contrib.auth.models import User
>>> u = User.objects.get(email='<your-email>')
>>> u.userprofile.role = 'SHOPZEN_ADMIN'   # unlocks admin APIs + dashboard tile
>>> u.save()
```

Normal shop owners get `role='OWNER'` by default and are rejected by all
`/api/admin/…` endpoints (server-side enforced, tested).

## 4. Configure the ₹30 subscription payment details

In Django admin (`/admin/`) or shell, set `SubscriptionPaymentConfig`:
- UPI ID / payee name (**use your real QR details — never commit these to the repo**)
- instructions text shown on the app's Premium screen

The app fetches these from `/api/subscription/payment-config/` — nothing is
hard-coded in the APK.

## 5. Payment verification workflow

1. User opens Premium screen → sees ₹30 + your payment details → pays via
   UPI → enters reference/UTR → taps **I Have Paid**.
2. Request is created `PENDING` — **no client can activate a subscription**.
3. You open the ShopZen admin dashboard in the app (admin accounts only) →
   Payments tab → verify the UTR in your UPI app → **Approve**.
4. Backend sets `ACTIVE`, records start date, extends expiry by 30 days per
   approval, writes an audit row. The user's app reflects Premium instantly
   on next sync.
5. Rejection writes `rejection_reason` (user sees it) and stays inactive.

See `docs/PAYMENT_SUBSCRIPTION_GUIDE.md` for the full flow.

## 6. Give the app to a shop owner

```bash
adb install -r release/app-release.apk      # or send the APK file directly
```
The release APK defaults to the production URL. The shop owner needs only:
**Android phone + internet + the app**. No Python, no laptop, no USB.
