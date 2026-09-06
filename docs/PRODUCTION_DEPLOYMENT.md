# ShopZen Production Deployment Guide (Render)

The existing DukaanFlow website (https://dukaanflow.onrender.com) and the ShopZen mobile app share **one** Django backend and **one** database. Deploying the API means redeploying the same Django project — nothing is duplicated.

---

## 1. What is already configured

| Concern | Status |
|---|---|
| `ALLOWED_HOSTS` | Env-driven (`ALLOWED_HOSTS`); defaults permissive for Render |
| CORS | `django-cors-headers`, `CORS_ALLOW_ALL_ORIGINS=True` (mobile JWT clients are not browser-CSRF-exposed) |
| JWT | `rest_framework_simplejwt`, access 30d / refresh 90d with rotation |
| Database | `dj_database_url` reads `DATABASE_URL` (PostgreSQL on Render) |
| Static files | WhiteNoise manifest storage |
| Media | `MEDIA_ROOT` on disk; use a persistent disk or S3 when volume grows |
| CSRF | Session-auth views still protected; JWT API routes are token-authenticated |

## 2. Environment variables (Render → Environment)

```
SECRET_KEY=<long random string>            # REQUIRED in production
DEBUG=False
ALLOWED_HOSTS=dukaanflow.onrender.com,localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=https://dukaanflow.onrender.com
DATABASE_URL=<render internal postgres url>
```
Never commit `.env`; it is already excluded from VCS.

## 3. Deploy steps

```bash
# locally verify first
./venv/Scripts/python.exe manage.py check
./venv/Scripts/python.exe manage.py makemigrations --check --dry-run
./venv/Scripts/python.exe manage.py test

git add -A && git commit -m "ShopZen mobile + REST API"
git push origin main         # Render auto-deploys the web service
```
On Render (first deploy after adding a new migration):
```bash
python manage.py migrate --noinput
python manage.py collectstatic --noinput
```
(The existing `Procfile`/`build.sh` already handle this; migrations are additive — **no destructive operations, no data reset**.)

## 4. Post-deploy verification checklist

```bash
BASE=https://dukaanflow.onrender.com
curl -s -X POST $BASE/api/auth/login/ -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"…"}'          # → 200 tokens
curl -s $BASE/api/dashboard/ -H "Authorization: Bearer <access>"   # → 200 JSON
curl -s $BASE/api/subscription/status/ -H "Authorization: Bearer <access>"
```
Then on the phone: set `baseUrl` to the production URL, login, make one test sale.

- Website still works: visit https://dukaanflow.onrender.com/ (landing + login)
- Mobile API works: dashboard, POS checkout, reports
- Multi-device login: same account on two phones shows identical data

## 5. Release APK for users

```bash
cd mobile_app
flutter build apk --release
# distribute build/app/outputs/flutter-apk/app-release.apk
```

## 6. Rollback

Render keeps deploys in the dashboard — "Rollback" to the previous commit restores the previous code; the additive migrations do not need to be reverted (new columns are nullable/defaulted and old code ignores them).
