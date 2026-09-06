# ShopZen Production Deployment Guide (Render)

The existing DukaanFlow website (https://dukaanflow.onrender.com) and the ShopZen mobile app share **one** Django backend and **one** database. Deploying the API means redeploying the same Django project — nothing is duplicated.

---

## 1. What is already configured

| Concern | Status |
|---|---|
| `ALLOWED_HOSTS` | Env-driven (`ALLOWED_HOSTS`); defaults permissive for Render |
| CORS | `django-cors-headers` (mobile JWT clients are not browser-CSRF-exposed) |
| JWT | `rest_framework_simplejwt`, access 30d / refresh 90d with rotation |
| Database | `dj_database_url` reads `DATABASE_URL` (PostgreSQL on Render) |
| Static files | WhiteNoise manifest storage, collected during build |
| Media | `MEDIA_ROOT` on disk; use a persistent disk or S3 when volume grows |
| Health check | **`GET /api/health/`** — public JSON `{status, app, version, database, time}` |
| Dependencies | **Pinned** in `requirements.txt` (exact tested versions; never `>=`) |
| Migrations | Run automatically by the **Procfile `release`** process on every deploy |

## 2. Environment variables (Render → Environment)

```
SECRET_KEY=<long random string>            # REQUIRED in production
DEBUG=False
ALLOWED_HOSTS=dukaanflow.onrender.com,localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=https://dukaanflow.onrender.com
DATABASE_URL=<render internal postgres url>
# Payment settings (optional overrides; defaults already safe)
SHOPZEN_UPI_ID=kambleparas220-1@okaxis
SHOPZEN_PAYEE_NAME=Paras Kamble
SHOPZEN_QR_IMAGE_URL=https://dukaanflow.onrender.com/static/images/shopzen_payment_qr.png
```
Never commit `.env`; it is already excluded from VCS.

## 3. Deploy steps

The repository now contains a **`render.yaml` blueprint** (web service + PostgreSQL + env vars + health check) and a **BOM-free `Procfile`** whose `release` process runs `python manage.py migrate` on every deploy.

### Option A — existing Render service (current situation)

1. Verify locally, then push:
   ```bash
   ./venv/Scripts/python.exe manage.py check
   ./venv/Scripts/python.exe manage.py makemigrations --check
   ./venv/Scripts/python.exe manage.py test api subscriptions
   git add -A && git commit -m "..." && git push origin main
   ```
2. **In the Render dashboard, open your service → Settings and check:**
   - **Build Command:** `pip install -r requirements.txt && python manage.py collectstatic --no-input`
   - **Start Command:** `gunicorn config.wsgi --workers 2 --log-file -`
   - **Health Check Path:** `/api/health/`
   - **Auto-Deploy: Yes** — *IMPORTANT: our investigation on 2026-09-06 proved auto-deploy is currently OFF (GitHub reports zero deployments/statuses after pushes), so a `git push` alone does NOT update production. Until you switch it on, use Manual Deploy.*
3. Click **Manual Deploy → Deploy latest commit**. Watch the Events/Logs tab: `pip install` → `collectstatic` → `release: migrate` → service live.

### Option B — fresh deploy from the blueprint (cleanest)

Render Dashboard → **New → Blueprint** → select this GitHub repo → Render reads `render.yaml` and creates everything (service + `dukaanflow-db` Postgres + env wiring + `/api/health/` health check). Set `DJANGO_SECRET_KEY` when prompted.

## 4. Post-deploy verification checklist

```bash
BASE=https://dukaanflow.onrender.com
curl -s $BASE/api/health/                                  # → {"status":"ok",...,"database":"up"}
curl -s -X POST $BASE/api/auth/login/ -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"…"}'          # → 200 tokens
curl -s $BASE/api/dashboard/ -H "Authorization: Bearer <access>"   # → 200 JSON
curl -s $BASE/api/subscription/payment-config/ -H "Authorization: Bearer <access>"
```
Then on the phone: **the release APK already points at the production URL by default** — install, login, make one test sale.

- Website still works: https://dukaanflow.onrender.com/ (landing + login)
- Mobile API works: dashboard, POS checkout, reports
- Multi-device login: same account on two phones shows identical data

## 5. Release APK for users

```bash
cd mobile_app
flutter clean && flutter pub get && flutter analyze && flutter test
flutter build apk --release
# → build/app/outputs/flutter-apk/app-release.apk  (default API URL = https://dukaanflow.onrender.com)
```
For a debug-against-laptop build only: `--dart-define=API_BASE_URL=http://127.0.0.1:8000` (plus `adb reverse`).

## 6. Rollback

Render keeps every deploy in the dashboard — "Rollback" to the previous one restores the previous code; the additive migrations do not need to be reverted (new columns are nullable/defaulted and old code ignores them).

## 7. Troubleshooting deploys

| Symptom | Cause | Fix |
|---|---|---|
| `/api/*` returns HTML 404 after push | Old build still running (auto-deploy off, see §3) | Manual Deploy → Deploy latest commit |
| Health returns `database: down` (503) | `DATABASE_URL` missing/wrong | Check env var; verify from Render Shell: `python manage.py dbshell` |
| Build log shows `STATICFILES_STORAGE removed` type errors | Dependencies drifted | `requirements.txt` is pinned — confirm nobody re-added `>=` ranges |
| Cold start slow (~30s) | Free plan spins down after inactivity | Expected on free tier; first request wakes it. Production plan keeps it warm |
