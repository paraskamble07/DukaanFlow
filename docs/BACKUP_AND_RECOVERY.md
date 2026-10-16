# ShopZen — Backup & Recovery Guide

ShopZen shops hold real money records, so the data is protected at three
layers: daily database backups on Render, owner-exportable JSON backups from
the app, and a tested restore path. This document describes all three and how
to recover.

Last updated: 2026-10-16.

---

## 1. Server-side backups (Render PostgreSQL — automatic)

- The production database is the managed PostgreSQL instance `dukaanflow-db`
  (region: singapore, plan: basic-256mb) created by `render.yaml`.
- Render keeps automated daily snapshots of managed PostgreSQL instances;
  point-in-time recovery is available from the Render dashboard
  (Databases → dukaanflow-db → Backups / Snapshots).
- A snapshot restore provisions the data to a new instance or overwrites the
  current one; `build.sh` runs `python manage.py migrate --noinput` on every
  deploy, so a restored older schema catches up automatically.

### How to restore from the Render dashboard
1. Render → Databases → **dukaanflow-db** → **Backups**.
2. Pick the day → **Restore** (confirm the warning).
3. Redeploy the web service (Settings → Manual Deploy) if needed.

**Note (honest):** Render's basic plan retains a limited number of snapshots;
verify the actual retention shown on the dashboard before promising a date.

## 2. In-app backup (owner — works fully offline)

- **Settings → Backup & Restore → Export backup** downloads a JSON snapshot
  of the shop: products, stock, IMEI devices, customers, suppliers, sales
  (with lines), payments, purchases, expenses and stock movements (including
  the IMEI link on each movement — Phase 11).
- The file can be shared/saved anywhere (WhatsApp, email, drive).
- **Restore** reads such a file into the shop. The restore path is idempotent
  per business and re-links IMEI devices to movements by IMEI string.

### What a restore does **not** do
- It does not delete or overwrite existing rows that already match; run a
  restore into a fresh/empty shop when in doubt.
- Passwords and user accounts are not part of the shop export.

### Recommendation
Shop owners should export a backup weekly and before any big change (bulk
stock edits, app update). Keep at least the last 2–3 exports.

## 3. Failure modes and recovery

| Situation | Recovery |
|---|---|
| Phone lost/broken | Install the app on a new phone, log in — all data is server-side. Offline bills queued on the lost phone would be lost (they were never uploaded). |
| Server unreachable | App keeps working offline: bills are queued locally, uploads when back online, dashboard shows the last cached snapshot. |
| Bad data mistake (wrong price batch edit) | Use the latest in-app backup + restore into a fresh shop, or ask Render to restore the previous day's snapshot. |
| Corrupted production DB | Render snapshot restore + redeploy; verify `/api/health/`. |

## 4. Tested?

- Backup/restore round-trip including IMEI-linked movements, customers and
  payments is covered by `api/tests_backup.py` (14 tests), which passed in
  this build.
- Render snapshot restore itself was **not performed** (would destroy/replace
  live production data — explicitly forbidden by the project rules; it is a
  dashboard operation for the day it is genuinely needed).
