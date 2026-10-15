# ShopZen — Project Audit

**Audit date:** 2026-10-15
**Auditor:** ShopZen engineering (automated full-repo audit)
**Repository:** `C:\Users\HP\Desktop\DukaanFlow` (git, branch `main`)
**Flutter app:** `mobile_app/` (package `com.dukaanflow.app`)
**Backend:** Django REST Framework (see `config/settings.py`)
**Production API:** https://dukaanflow-1.onrender.com

> This audit was produced by inspecting the actual repository — models,
> serializers, views, URLs, permissions, migrations, Flutter screens,
> providers, tests, build artifacts and production health — not from
> memory or prior plans. It is the baseline for all subsequent phases.

---

## 1. Repository shape

### Backend (Django / DRF)

| Area | Finding |
|---|---|
| Django version | 6.1.1 (requirements.txt) |
| DRF | 3.18.0, simplejwt 5.5.1 |
| Installed apps | 13 project apps: `core, accounts, businesses, customers, products, inventory, suppliers, purchases, sales, expenses, payments, subscriptions, invoices, reports, dashboard, landing, api, updates` |
| API URL routes | 50 endpoints under `/api/` (`api/urls.py`) |
| Migrations | 15 non-initial migrations across apps; every business app has an initial migration; `updates` has 2 (model + seed) |
| Databases | Dev/test: SQLite via `dj_database_url.config(default=...)`; production: PostgreSQL through `DATABASE_URL` (Render) |
| Legacy web UI | **Removed** in prior checkpoint — `config/urls.py` serves only `admin/` + `api/`; 42 templates deleted after proving no API ↔ template coupling |
| Static | `STATICFILES_DIRS = []`, `collectstatic` harvests 157 admin/DRF files; `CompressedManifestStaticFilesStorage` via WhiteNoise |

### Flutter

| Area | Finding |
|---|---|
| Flutter / Dart | Flutter 3.47.2, Dart 3.13.2 |
| State management | Riverpod (`flutter_riverpod` 2.5.1) |
| Networking | Dio 5.4.3+1 with JWT refresh interceptor (`core/network/api_client.dart`) |
| Storage | `shared_preferences` + `flutter_secure_storage` |
| Screens | 34 dart files under `lib/features/`, ~9,820 LOC in `lib/` |
| Localization | Custom `AppLocalizations` (EN/HI/MR), ~21 keys — **incomplete coverage** (see §4) |
| Build | Release APK built and verified: `release/app-release.apk`, 70.2 MB, SHA-256 `40dd44d436b3b502a716aadcd7ba9a447f32571a05f9f0057fb6f17da5881ff9` |

---

## 2. Feature inventory (what actually exists and works)

### Implemented and backend-enforced

- **Auth**: register, login, JWT access/refresh, profile, business
  settings, forgot-password + reset-password (secure token, expiry,
  single-use, no email enumeration, session invalidation).
- **RBAC**: `api/permissions.py` — `can(user, module)` with OWNER /
  SHOPZEN_ADMIN passing everything and STAFF only permitted modules;
  per-module permission classes wired to **every** endpoint group
  (products, inventory, suppliers, purchases, sales, customers,
  payments, expenses, reports, settings).
- **Field-level privacy**: backend withholds `purchase_price`,
  `profit_margin`, `gross_profit` from non-owner users via
  `is_field_sensitive()` — not merely hidden in Flutter.
- **Tenant isolation**: querysets filtered by `request.business`
  (`HasActiveBusiness`); tested with two separate businesses.
- **Products / stock**: categories, products, stock movements, stock
  adjustment, IMEI device registration + lookup.
- **Purchases / suppliers**: supplier CRUD, purchase entry, stock
  increase.
- **Sales / POS**: server-calculated totals, atomic checkout, invoice
  number generation with collision skipping, sale history + detail.
- **Customers & Khata**: customer CRUD, ledger with running balances,
  partial payments settling to zero, ledger history preserved.
- **Expenses**: categories, CRUD, owner-authorized.
- **Reports**: 8 endpoints (profit-loss, sales, stock, khata, expenses,
  GST, top products, top customers), module-gated.
- **App updates (Phase 21)**: trusted manifest endpoint + mandatory
  flag + SHOPZEN_ADMIN publishing; seeded v1.0.0 (build 1).
- **Health endpoint**: public, includes `db_engine` vendor proof.

### Implemented in Flutter, functional

- Dashboard with KPI cards, sales chart, quick actions.
- POS billing screen, cart math, checkout.
- Product list, IMEI scanner/lookup, customer list, supplier screens,
  expense screen, reports screen, sales history/detail, admin screen,
  settings (theme, language, shop profile).
- WhatsApp/SMS composer deep links (Android confirmation, no silent
  sending).
- Offline sync service scaffolding (`core/sync/offline_sync_service.dart`).

---

## 3. Security audit summary (details in `docs/SECURITY_AUDIT.md`)

| Check | Status |
|---|---|
| Every list/detail endpoint enforces business ownership | ✅ (tests) |
| Sensitive financially fields withheld server-side | ✅ (tests) |
| Employee cannot reach owner-only reports | ✅ (tests) |
| Password reset tokens secure, single-use, expiring | ✅ (tests) |
| No email enumeration on reset | ✅ (tests) |
| Cross-business IDOR attempts blocked | ✅ (tests, 2 businesses) |
| JWT refresh rotation / blacklist | ⚠️ best-effort (token_blacklist not installed; blacklist loop wrapped in try/except) |
| Rate limiting | ⚠️ not configured (see SECURITY_AUDIT) |
| DEBUG / SECRET_KEY | ✅ production uses env; DEBUG=False in render.yaml |
| HTTPS / hosts / CORS | ✅ `.onrender.com` host suffix; see SECURITY_AUDIT |

---

## 4. Gaps found by this audit (drives the implementation plan)

1. **Monetization model must change.** The app currently has a ₹30/month
   "ShopZen Premium" subscription flow (subscription screen, payment
   requests, admin verification, dashboard banners). New requirement:
   **AdMob banner ads only**; subscription paywalls must go while all
   business payment features stay.
2. **No backend subscription gate exists** (nothing blocks on
   `plan_tier`), so removal is UI + informational, not a data
   migration — historical subscription data must be preserved.
3. **Localization coverage is shallow**: ~21 keys for EN/HI/MR while the
   app has 34 screens of predominantly hardcoded English strings.
4. **No PDF generation** anywhere — customer ledger statements
   (new requirement) are not implemented.
5. **No payment reminder workflow** — WhatsApp/SMS composer exists for
   invoices, but no reminder list, due dates, or reminder history.
6. **No UPI QR configuration** in the app (a UPI id exists in render.yaml
   env but no owner-facing QR screen; note scanning ≠ payment
   confirmation).
7. **Offline support is scaffolding only** — no cached-read indicator,
   no pending-operations queue, no idempotency keys.
8. **Shop intelligence missing**: no warranty tracking, no low-stock
   threshold configuration, no dead-stock rule, no customer purchase
   history view.
9. **No AdMob SDK** in the project at all.
10. **Step scripts** (`step_*.py`) at repo root are obsolete
    scaffolding scratch files not used by the live code (documented,
    not part of the app).
11. **`landing` app** still in INSTALLED_APPS; its templates were
    removed. Harmless but should be documented or retired cleanly.
12. **Test coverage**: 57 backend tests pass in isolation; combined-run
    issues being triaged. Flutter has 6 widget/model tests only — thin.

---

## 5. Production state

- Render web service `dukaanflow` (starter, singapore), PostgreSQL
  `dukaanflow-db` (basic-256mb), auto-deploy on push, health check on
  `/api/health/`.
- Live health verified: `{"status":"ok","app":"ShopZen","version":"1.0.0","database":"up"}`.
- Pending production migrations (not yet deployed):
  `accounts.0003`, `accounts.0004`, `updates.0001`, `updates.0002`.
- Release APK verified against production API base URL
  (`https://dukaanflow-1.onrender.com` baked into `libapp.so`).

---

## 6. Verdict

The repository is a functioning, secure, multi-tenant shop-management
API + Flutter app with real financial workflows and solid permission
tests. The outstanding work is **feature completion against the new
AdMob monetization model** (removal of subscription paywalls, reminder
workflow, ledger PDF, UPI QR, full localization, offline, shop
intelligence, AdMob banners) — not rework of broken foundations.
