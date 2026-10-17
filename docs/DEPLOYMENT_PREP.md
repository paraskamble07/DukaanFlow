# ShopZen — Production Deployment Guide (owner action required)

**Status: 2026-10-17 — NOT deployed.** This document explains exactly what is
missing on the live server, what a deployment involves, and the order to do it
in. Nothing here is executed without the owner's explicit approval.

---

## 1. What the live server is running today

- Production API: `https://dukaanflow-1.onrender.com` — **up and healthy**
  (`GET /api/health/` → 200, `status: ok`, `db_engine: sqlite`).
- Render deploys **automatically from the `main` branch on GitHub**
  (`render.yaml` → `autoDeploy: true`), and the release command
  `python manage.py migrate` runs migrations on every deploy.
- Local `main` is in sync with GitHub (`HEAD == origin/main`, commit
  `e4a0ab8`). **All work since that commit is uncommitted and therefore has
  never been deployed.**

## 2. What production is missing (verified by live probes, 2026-10-17)

| Endpoint / behavior on production | Status | Evidence |
|---|---|---|
| `GET /api/staff/` | **404** | the Staff & Logins screen shows the 404 on the owner's phone |
| `GET /api/notifications/` | **404** | the Notifications screen shows the 404 |
| Khata bill settlement (FIFO `settle_after_payment`) | absent | `payments/services.py` is untracked |
| Duplicate-customer prevention (409 + `find_duplicate_customer`) | absent | not in `api/views/customer_views.py` at `HEAD` |
| Migration `customers/0002` (unique phone per shop) | **never ran on production** | migration file is untracked |
| The 1.1.1 app's other backend dependencies | present | every other app endpoint returns 401/200 (route exists) |

Everything else the app calls — auth, dashboard, customers, products, POS,
sales, payments, reports, reminders, app updates, backup — **exists on
production today** (verified: 401 = route present, auth required).

## 3. Is a database migration required?

Yes, one: `customers/migrations/0002_merge_duplicates_unique_phone.py`.

- It is **data-safe by design**: before enforcing "one customer per phone per
  shop", it re-points every `Sale`, `Payment` and `MobileDevice` row to the
  canonical customer *before* deleting the duplicate. Its reverse is a no-op.
- It runs automatically on deploy (Render release command).
- **Recommendation before the first deploy**: export a backup using the app's
  own Backup & Restore screen (Settings → Backup), and/or snapshot the Render
  disk. The migration was verified against a dev database with live-shaped
  data (9 customers / 19 payments / 16 sales — all intact afterwards).

⚠️ **Important risk to check once (Render dashboard):** the health endpoint
reports `db_engine: sqlite`, i.e. production runs on a **SQLite file**, not
the PostgreSQL database `render.yaml` describes. If the Render web service
has **no persistent disk mounted**, that file is wiped on every redeploy and
all production data would be lost. Before deploying, confirm a disk is
attached (Settings → Disks) and take a backup. Migrating to the PostgreSQL
instance in `render.yaml` is a larger, separate decision — not required for
this release, but recommended for durability.

## 4. The deployment steps (nothing happens without approval)

```bash
# 1. Review what will go up (from the project root):
git status --short
git diff --stat

# 2. Stage and commit the verified working tree, e.g.:
git add api/ customers/ payments/ updates/ mobile_app/ docs/ release/
git commit -m "ShopZen 1.1.1: staff logins, notifications, khata FIFO settlement, duplicate-customer prevention, live AdMob IDs, UI fixes"

# 3. Push — Render auto-deploys from main and runs migrations:
git push origin main
```

What happens automatically after the push:

1. Render builds (`pip install -r requirements.txt && collectstatic`).
2. Release command runs `python manage.py migrate` → applies `customers/0002`
   (the only pending migration; `makemigrations --check` is otherwise clean).
3. Gunicorn restarts; `/api/health/` returns to 200 (verify it).
4. Re-open Staff & Logins and Notifications in the app — the 404s are gone.

**Post-deploy verification checklist:**

- [ ] `https://dukaanflow-1.onrender.com/api/health/` → 200
- [ ] `GET /api/staff/` with an owner token → 200 (not 404)
- [ ] `GET /api/notifications/` with an owner token → 200 (not 404)
- [ ] Add a customer with an existing phone → rejected with 409
- [ ] Record a payment on a khata customer → the bill shows Paid/Due correctly

## 5. What must NOT be deployed by mistake

- `db.sqlite3` (gitignored dev database) — it must never enter the commit.
- `shopzen_crash_log.txt`, `shopzen_fix_log*.txt`, `shopzen_fix.png` — local
  debugging artifacts from an earlier session, not project files.
- `static/apk/shopzen-1.0.0.apk` — the published production APK stays
  untouched (verified SHA-256 `ffc5e50c…e76`).

## 6. The app side is already built

`release/app-release.apk` (this working tree, 1.1.1+3) already contains every
frontend fix (staff screen, notifications, corrected product-detail and
IMEI-history URLs, honest 404 messages, live AdMob banner wiring). It will
keep working against the old server for every feature except Staff &
Logins and Notifications, which only light up after the backend deploy.
