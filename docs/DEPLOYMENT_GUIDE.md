# ShopZen — Deployment Guide

**Target:** Render web service + managed PostgreSQL.
**Production URL:** https://dukaanflow-1.onrender.com
**Repo branch for releases:** `main`

---

## Current production status (2026-10-15, verified)

The live service is running a **stale build**: after pushing `cb2ec9c` the
API still served the legacy URL table and `/api/app-updates/check/`
returned 404, and a debug 404 page exposed `DEBUG = True`. The Render
service was evidently created **manually** (not from the `render.yaml`
blueprint), so its Deploy settings are not managed by this repository —
they must be checked in the Render dashboard.

## Owner action to deploy the current code

In the Render dashboard, open the **dukaanflow** web service → **Settings**:

| Setting | Required value | Why |
|---|---|---|
| Repository / Branch | `paraskamble07/DukaanFlow` / `main` | Deploy from the verified branch |
| **Auto-Deploy** | **Yes** | So every push deploys, as this repo assumes |
| Build Command | `bash build.sh` | Installs deps **and runs `manage.py migrate`** and `collectstatic` |
| Start Command | `gunicorn config.wsgi --workers 2 --threads 4 --log-file -` | Production server |
| Health Check Path | `/api/health/` | Verified liveness probe |

Environment (Environment tab):

| Variable | Value |
|---|---|
| `DEBUG` | `False` (also the code default now) |
| `SECRET_KEY` | a long random string (startup **refuses** to run without it when `DEBUG=False`) |
| `ALLOWED_HOSTS` | `dukaanflow-1.onrender.com,.onrender.com` |
| `DATABASE_URL` | from the PostgreSQL database's **Connection Info** (Render injects it if linked) |

Then press **Manual Deploy → Deploy latest commit** and watch **Events** /
**Logs** for:

1. `Build completed successfully.` (from `build.sh`) — proves migrations ran.
2. Service goes **Live** (health check on `/api/health/`).

## Post-deploy verification checklist (honest, run these)

```bash
BASE=https://dukaanflow-1.onrender.com

# 1. Health reports PostgreSQL (not a silent SQLite fallback)
curl -s $BASE/api/health/               # must show "db_engine":"postgresql"

# 2. App-update manifest exists (it 404s on the stale build)
curl -s "$BASE/api/app-updates/check/?platform=android&version_code=1"

# 3. Password-reset endpoints exist (also 404 on the stale build)
curl -s -X POST $BASE/api/auth/forgot-password/ -H 'Content-Type: application/json' \
     -d '{"email":"nobody@example.com"}'

# 4. Auth still works (owner account)
curl -s -X POST $BASE/api/auth/login/ -H 'Content-Type: application/json' \
     -d '{"email":"<your-email>","password":"<password>"}'

# 5. Reminder endpoints are protected
curl -s -o /dev/null -w '%{http_code}' $BASE/api/reminders/due-list/   # expect 401
```

All five pass ⇒ the deploy is current. Any 404 ⇒ still stale (repeat the
Manual Deploy step). **Do not declare the deploy successful without running
these checks.**

## Database migrations (non-destructive)

Deploys run `manage.py migrate` via `build.sh`. Pending migrations in this
branch:

- `accounts.0003` — `UserProfile.permissions` (staff module grants)
- `accounts.0004` — reset-password token + expiry columns
- `updates.0001`, `updates.0002` — AppRelease model + v1.0.0 seed
- `reminders.0001` — ReminderLog + ReminderSetting

All are purely additive (new tables / new nullable columns). No production
data is modified or deleted; a backup before deploying is still good
practice — see `docs/BACKUP_AND_RECOVERY.md`.

## Using the blueprint (alternative, resets Render-managed config)

Applying `render.yaml` as a Render Blueprint recreates the service with
the correct build/start commands, env wiring and the `dukaanflow-db`
PostgreSQL, plus auto-deploy enabled. Only do this if you are replacing
the manually-created service — it is not needed for the steps above.

## Rollback

Render keeps every successful deploy: **Manual Deploy → Deploy a specific
commit** (or the previous release in the deploys list) rolls back code.
Database migrations are forward-only by design — the pending ones here are
additive, so a code rollback after these migrations remains safe.
