# ShopZen — End-to-End Acceptance Document

Project: DukaanFlow / ShopZen — free shop management app (Flutter + Django REST)
Target release: Android APK (`com.dukaanflow.app`)
Production API: `https://dukaanflow-1.onrender.com`
Last updated: 2026-10-16 (Phases 13–15)

This document defines the 21 acceptance steps every release must pass before it
ships, and records the evidence for the current build. Steps marked **NOT
PERFORMED** were genuinely not executed — nothing is reported as verified
without evidence.

---

## How to run the acceptance suite

- Backend: `python manage.py test api` (in-memory sqlite; synthetic data only —
  **never production data**).
- Flutter: `flutter test` (desktop test host), `flutter analyze`.
- API smoke against production: `curl` with a demo JWT (demo@dukaanflow.com).
- Device steps (15, 16, 20, 21): install the release APK on a physical Android
  phone and run the shop-owner scenario.

---

## The 21 acceptance steps

### A. Authentication & tenant isolation

1. **Owner login → business resolution.**
   POST `/api/auth/login/` with owner credentials returns JWT access + refresh;
   GET `/api/auth/profile/` returns the user with the correct business.
   Evidence: `api/tests.py::test_profile_returns_business_for_jwt_client`.

2. **Staff roles keep working.** A `STAFF` user with `payments` permission can
   list payments; a staff user *without* the permission gets 403.
   Evidence: `api/tests.py` permission tests, `HasActiveBusiness` +
   `PaymentsPermission` (`api/permissions.py`).

3. **Cross-tenant isolation (XSS of the data kind).** Shop A can never read or
   sell Shop B's products, customers, devices or ledgers; cross-shop requests
   return 404 / 400.
   Evidence: Phase 11 + Phase 13 tenant tests
   (`test_device_from_another_shop_is_rejected`, purchase-history
   cross-tenant tests); every list view filters by `request.business`.

### B. Catalog & inventory

4. **Product CRUD with categories.** Create/list/update products; search `?q=`
   and category filter work.
   Evidence: `api/tests.py::test_products_api`, product view tests.

5. **Stock filters honest.** `?stock=low` and `?stock=dead` return only
   products genuinely matching the server-side rule (dead = in stock and no
   sale in the last 60 days); a product sold today is never dead.
   Evidence: `api/tests_phase11.py::DeadStockFilterTest`.

6. **IMEI lifecycle.** Register device → sell via checkout → device `SOLD`
   with warranty expiry derived server-side; `/api/inventory/imei/lookup/`
   and `/api/inventory/imei/<id>/history/` show registration + sale timeline.
   Evidence: `api/tests_phase11.py` (warranty + IMEI history tests).

### C. Billing & financial integrity

7. **Server-side bill totals (no client math trusted).** Checkout recomputes
   subtotal, discount, tax, total, paid and due from the accepted cart lines
   with `Decimal` precision; a padded `paid_amount` is clamped to the bill
   total.
   Evidence: `api/tests_phase13.py::ServerTotalsTest`.

8. **Negative/absurd lines rejected.** Negative price, negative discount,
   line discount exceeding the line total, or quantity < 1 → 400, no rows
   written.
   Evidence: `test_negative_line_total_is_rejected`, `qty < 1` guard in
   `pos_views.py` (covered by the same code path).

9. **Stock cannot go negative.** Billing more than available stock → 400 with
   the available quantity named; **no** half-committed bill (0 sales, 0 lines,
   0 movements, 0 payments, stock untouched).
   Evidence: `test_rejected_checkout_writes_nothing`.

10. **An IMEI unit is sold exactly once.** A second sale of the same unit is
    rejected with "already sold"; the device's original customer/sale/warranty
    stay intact. A device of another product or another shop is rejected.
    Evidence: `api/tests_phase13.py::StockOnceTest`.

11. **Khata ledger integrity.** Customer balances are derived from sale +
    payment history; overpayment is rejected so money can never vanish in a
    floor-at-zero sum; recording a payment closes the due without mutating the
    original bill's audit row.
    Evidence: `api/tests_phase13.py::LedgerImmutabilityTest`.

12. **Credit sales.** `payment_method=CREDIT` records no payment row, due =
    total; supplier payments record vouchers against payables.
    Evidence: `test_credit_sale_records_no_payment_row`, supplier payment
    tests.

### D. Money movement that must stay real

13. **Customer Khata payments.** POST `/api/payments/customer/` records a
    payment within the outstanding due and returns the new balance.
    Evidence: `LedgerImmutabilityTest` (above) + `api/tests.py` payment tests.

14. **Expenses.** Owners record expenses (rent/electricity/salary); reports
    subtract them from net profit.
    Evidence: `api/tests.py` expense/report tests.

15. **Device example of a real rupee flow — checkout on a physical phone.**
    Bill an IMEI product, pay partially by UPI, check the invoice PDF
    (total/paid/due exact to the paisa) and share it.
    **NOT PERFORMED for the current build** — requires a release APK on a
    physical device (see Phase 16 for the APK artifact and the device-test
    status).

### E. Reports & dashboard

16. **Dashboard numbers equal the books.** Today's sales, gross profit,
    expenses, receivables, payables and the 7-day chart all derive from the
    same server-side aggregates; offline load shows the last cached snapshot
    with a "showing last data" notice instead of a dead error screen.
    Evidence: `api/tests.py::test_dashboard_api`,
    `mobile_app/test/sync_status_banner_test.dart` (Phase 9), plus the live
    smoke notes in `IMPLEMENTATION_STATUS.md`.

17. **Profit & loss and ledger PDF / UPI QR.** Reports compute from real rows;
    the customer ledger exports to PDF; UPI deep-link/QR uses the shop's own
    UPI id.
    Evidence: `api/tests.py::test_profit_loss_report_api`, Phase 4–7 tests,
    `mobile_app` PDF tests.

### F. Data safety & operations

18. **Backup & restore round-trip.** Owners export a JSON backup and restore
    it into a fresh business; products, stock, devices (incl. IMEI links on
    movements), customers, sales, payments and purchases survive the
    round-trip.
    Evidence: Phase 8 backup tests (117–119 series).

19. **Offline queuing.** With no connection, a bill is saved locally and the
    sync banner shows "Offline — N bill(s) saved locally"; on reconnect it
    uploads and the queue clears; the cart clears on success.
    Evidence: Phase 9 (`sync_status_provider`, offline checkout tests).

20. **App update flow.** The app checks the update endpoint, shows
    what's-new/download progress, and offers install — never silently changes
    the app.
    Evidence: `updates/tests.py` (server side: availability/mandatory/
    inactive-release/version-code tests) + the Flutter update screens;
    production endpoint status depends on the pending deploy (see Deployment
    status below).

21. **Free app, ads only, no paywall.** Login, billing and every feature work
    without any payment; banner ads appear **only** on dashboard, product
    list, customer list and settings — never on invoices, payment
    confirmations or over controls; the UMP consent form gates first ad
    impression.
    Evidence: `mobile_app/test/phase12_ads_test.dart`; banner placement audit
    (4 screens exactly); subscription models exist only as inactive history
    (per Phase 2 audit).

---

## Current-build evidence summary

| Check | Result |
|---|---|
| Backend tests, all apps (`manage.py test api updates reminders subscriptions`) | **151/155 pass**. Breakdown: `api` **116/116**, `updates` 13/13, `reminders` + `subscriptions` 21/21, legacy `tests/` 1/5 (see known failures below). Phase 13 integrity suite alone: **13/13** |
| Legacy `tests/` suite | **4 pre-existing failures, unchanged by this build** — see below; verified identical on the pre-Phase-13 tree |
| `manage.py check` | clean, 0 issues |
| `makemigrations --check --dry-run` | **No changes detected** (model state == migrations) |
| Flutter tests | **36/36** (Phase 12 included) |
| `flutter analyze` | 0 errors / 0 warnings (34 pre-existing infos) |
| Localization parity | 598 keys in each of en/hi/mr |
| Decimal-safety audit | money columns stay `DecimalField`; every `float()` call is at the JSON serialization boundary only, never in ledger math (audit: `pos_views`, `payment_views`, `dashboard_views`, `report_views`, `serializers`) |
| Demo data | OK to use `demo@dukaanflow.com` seeded shop for smoke only |
| Production health | `https://dukaanflow-1.onrender.com/api/health/` → 200 (see note) |

### Known pre-existing failures (legacy suite `tests/`)

These 4 tests target the **pre-API URL surface** (e.g.
`/sales/api/checkout/` with Django session auth) that the JWT REST API
replaced early in the project, or a feature the product spec deliberately
removed (subscription plan limits). They fail **identically on the tree
before Phase 13** (verified: `git stash` → run → same 4 failures), so they are
pre-existing, not regressions. Per the project rules they are **not** deleted,
not weakened and not faked green:

- `test_auth_and_business.test_plan_limits_enforcement` — asserts the old
  Free-plan cap of 50 customers/products; the app is now free for all shops
  (limits raised to 999999 when paywalls were removed), so the expectation no
  longer matches the product.
- `test_auth_and_business.test_tenant_data_isolation`,
- `test_reports_and_profit.test_gross_and_net_profit_calculation`,
- `test_sales_and_pos.test_pos_checkout_flow` — all call the old non-JWT
  endpoints which 404; the same behaviors are covered today by strict tests
  against the current API (`api/tests.py`, `api/tests_phase11.py`,
  `api/tests_phase13.py`).

### Deployment status (honest)

The last verified production deploy predates Phases 9–13: the service serves
the older build (health 200, while newer endpoints 404). The owner must
re-link auto-deploy or press **Manual Deploy** in the Render dashboard; the
build then runs `build.sh` (migrations + collectstatic) automatically. **A
deploy of the current code has NOT been performed and is NOT claimed.** Full
steps: `docs/DEPLOYMENT_GUIDE.md`.

### Production database (no silent SQLite)

`config/settings.py` resolves `DATABASES` from `DATABASE_URL` via
`dj_database_url`; on Render, `render.yaml` wires `DATABASE_URL` to the
managed PostgreSQL `dukaanflow-db` (region singapore, plan basic-256mb) and
`build.sh` runs `python manage.py migrate --noinput` against it. The sqlite
default only ever applies on a developer machine without `DATABASE_URL`. The
production DB is PostgreSQL **by configuration**; row-level verification
against the live instance re-checks after the owner's deploy (Step: verify
`\dt`-equivalent via a Django shell on the Render service — requires the
deploy to have happened).

### Not performed — and who unblocks it

| Item | Blocker | Owner action |
|---|---|---|
| Steps 15–21 device runs, real APK install | release APK rebuild + physical device | Phase 16 build; owner for the device |
| Live AdMob banner impressions | AdMob account approval + real ad unit ids | `docs/ADMOB_SETUP.md` (Phase 17) |
| Production serving of Phases 9–13 | pending Render deploy | Render dashboard manual deploy |
