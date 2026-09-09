# ShopZen — Deployment Guide

This is the deployment entry point. The complete, step-by-step guides are:

| Task | Full guide |
|---|---|
| **Deploy the backend to Render (permanent internet access)** | [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md) + [PRODUCTION_SETUP.md](PRODUCTION_SETUP.md) |
| Build the Android APK / AAB | [ANDROID_BUILD.md](ANDROID_BUILD.md) |
| The ₹30 payment setup (your UPI/QR) | [PAYMENT_SETUP.md](PAYMENT_SETUP.md) |
| Your admin account | [ADMIN_GUIDE.md](ADMIN_GUIDE.md) |

## Quick reference — deploy checklist

1. **Push to GitHub** — all code is already pushed (`github.com/paraskamble07/DukaanFlow`).
2. **Render → your service → Manual Deploy → Deploy latest commit.** ⚠️ Auto-deploy is
   currently OFF — pushes do NOT deploy by themselves. Turn Auto-Deploy ON after the
   manual deploy so future pushes deploy automatically.
3. Set env vars on Render: `SECRET_KEY` (random), `DEBUG=False`,
   `ALLOWED_HOSTS=dukaanflow.onrender.com`, `DATABASE_URL` (Render Postgres),
   `CSRF_TRUSTED_ORIGINS=https://dukaanflow.onrender.com`.
4. Verify: `curl https://dukaanflow.onrender.com/api/health/` → `{"status":"ok",...}`.
   If it 404s, the service is still running old code — repeat step 2.
5. Create your admin account and payment QR per [PRODUCTION_SETUP.md](PRODUCTION_SETUP.md).
6. Build the release APK/AAB per [ANDROID_BUILD.md](ANDROID_BUILD.md) — they default to
   the production URL, so they work for any shop owner with just a phone + internet.

## Development backend (your laptop only — never for real users)

```bash
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 127.0.0.1:8000     # http://127.0.0.1:8000/api/health/
```

Run the test suite before every deploy:

```bash
python manage.py test        # 24 tests: auth, POS atomicity, tenant isolation, subscription
```
