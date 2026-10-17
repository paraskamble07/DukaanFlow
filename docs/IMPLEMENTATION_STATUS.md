# ShopZen — Implementation Status

**Last verified checkpoint:** 2026-10-15 (Phase 1–2 complete: audit docs +
subscription monetization removed)
**Repository:** `C:\Users\HP\Desktop\DukaanFlow`
**Production API:** https://dukaanflow-1.onrender.com (`{"status":"ok","app":"ShopZen","database":"up"}`)
**Release APK:** `release/app-release.apk` — SHA-256
`40dd44d436b3b502a716aadcd7ba9a447f32571a05f9f0057fb6f17da5881ff9`
(package `com.dukaanflow.app`, v1.0.0 build 1, label `ShopZen`, baked
API base `https://dukaanflow-1.onrender.com` verified in `libapp.so`)

---

## What was completed in this session

### 1. Employee permissions and field-level privacy (backend-enforced)

- `api/permissions.py` — full RBAC layer:
  - `can(user, module)` — OWNER/SHOPZEN_ADMIN pass everything, STAFF only
    modules explicitly granted on `UserProfile.permissions` (least-privilege default).
  - Named DRF permission classes per module: `ProductsPermission`,
    `SuppliersPermission`, `PurchasesPermission`, `SalesPermission`,
    `CustomersPermission`, `PaymentsPermission`, `ExpensesPermission`,
    `ReportsPermission`, `SettingsPermission`, `WhatsappPermission`, `SmsPermission`.
  - `OwnerOnly` — owner-restricted endpoints.
  - `is_field_sensitive(field, user)` — returns the fields an employee must not see.
- Every API endpoint wired with the permission class for its module:
  products, categories, suppliers, purchases, expenses, customers,
  customer ledger, payments, supplier payments, all 8 report endpoints,
  and business settings (`OwnerOnly`).
- Serializer-level field privacy (backend withholds, not just Flutter hides):
  - `ProductSerializer.purchase_price`, `profit_margin` → `null` for staff.
  - `SaleSerializer.gross_profit` → `null` for staff.
- `RefreshToken.objects` bug in reset-password fixed (`RefreshToken` is a token
  class, not a model) → session invalidation is now best-effort blacklist-based.

### 2. Password reset (Phase 3 of PRD)

- `POST /api/auth/forgot-password/` — issues a cryptographically secure
  `secrets.token_urlsafe(32)` token, 60-minute expiry, always returns the same
  generic message (no email enumeration).
- `POST /api/auth/reset-password/` — validates token + expiry, enforces
  8-char minimum, invalidates the token after use, blacklists outstanding
  refresh tokens.
- Stored on `UserProfile.reset_password_token` / `reset_password_expires`
  (migration `accounts.0004`).
- **Tested:** 7 reset-flow tests, all pass (see TEST_REPORT).

### 3. Security test suite — `api/tests_security.py` (29 tests)

Covers employee restrictions, two-shop tenant isolation/IDOR, password reset
security, and the critical khata ledger scenario. All 29 pass.

### 4. Legacy web UI removal (Android-first)

- Removed 42 legacy HTML templates + 4 static web assets.
- `config/urls.py` now serves only `admin/` and `api/`.
- `STATICFILES_DIRS` cleared; `collectstatic` still harvests 157 admin/DRF files.
- Preserved: all models, migrations, business logic, Django admin, API routes.

### 5. Flutter

- 41 deprecated `withOpacity()` calls replaced with `withValues(alpha:)`
  across 25 files (analyzer issues 92 → 48, zero errors).
- Unused import removed from `pos_provider.dart`.
- `app_name` rebranded to **ShopZen** (EN) / शॉपज़ेन (HI, MR);
  Android manifest label already `ShopZen`.
- 6/6 Flutter tests pass.

### 6. App Update feature (Phase 21)

- Backend — new `updates` app:
  - `AppRelease` model: `platform`, `version_name`, `version_code`
    (build number, unique), `minimum_supported_code`/`_name`,
    `release_notes`, `download_url`, `checksum_sha256`, `is_active`,
    `released_at`, `created_by`.
  - `GET /api/app-updates/check/` (public) — client sends
    `platform` + `version_code`; server computes `update_available` and
    `mandatory_update` and returns the trusted manifest
    (`latest_version`, `latest_build_number`,
    `minimum_supported_version`, `release_notes`, `released_at`,
    `download_url`, `checksum_sha256`).
  - `POST/GET /api/admin/app-releases/` and
    `/api/admin/app-releases/<id>/` — SHOPZEN_ADMIN-only publishing
    (owner/staff/anonymous get 403/401; validated so the minimum build
    cannot exceed the release build).
  - Data migration `0002_seed_initial_release` publishes v1.0.0 (build 1)
    so production serves a manifest immediately.
  - **13/13 backend tests pass** (`python manage.py test updates`).
- Flutter:
  - `package_info_plus` added for real version/build reading.
  - `models/app_update_model.dart` + `providers/update_provider.dart`.
  - `features/settings/app_update_screen.dart` — installed build,
    check-for-updates, release notes, SHA-256, download link
    (url_launcher, external application).
  - Startup check in `MainNavigationScaffold` — mandatory updates show a
    non-dismissible dialog routing to the update screen; non-mandatory
    checks never interrupt the user and never fail the app offline.
  - Settings → "App Updates" entry tile.
- Fixed a latent bug found while verifying the APK: the compile-time
  default in `api_constants.dart` pointed at the stale
  `dukaanflow.onrender.com`; now `dukaanflow-1.onrender.com` (the
  release APK was built with the correct `--dart-define`, and the
  string was verified inside `libapp.so`).

### 7. Subscription monetization removed (Phase 2 — app now free, AdMob-only)

**Flutter (paywalls removed):**
- Deleted `features/subscription/subscription_screen.dart` and its
  navigation entries.
- `main.dart`: subscription-expiry renewal banner + its checker removed;
  `ApiConstants` import dropped (no longer needed there).
- `more_screen.dart`: "ShopZen Premium ₹30/month" tile removed; header
  now reads "Free ShopZen Account".
- `business_provider.dart`: `subscriptionProvider`,
  `paymentConfigProvider`, `myPaymentRequestsProvider` removed
  (documented why).
- `admin_dashboard_screen.dart`: payment-verification tab replaced by an
  **App Releases** tab (list + publish dialog) — the SHOPZEN_ADMIN role
  now serves app updates (Phase 21) instead of subscription approvals.
- `admin_provider.dart`: payment-request providers removed;
  `adminAppReleasesProvider` added.

**Backend (deliberately non-destructive):**
- Verified before editing: **no core endpoint gates on `plan_tier` or
  subscription status**, so removal required no enforcement change.
- `subscriptions` models, migrations, routes and historical payment data
  are all preserved (no destructive migration).
- `docs/PAYMENT_SETUP.md` and `docs/PAYMENT_SUBSCRIPTION_GUIDE.md`
  marked RETIRED with a banner — kept for history, not deleted.

**Customer/supplier payment features untouched and re-verified:**
6/6 Flutter tests pass; `flutter analyze` 0 errors (47 infos, down from
48); 57/57 backend tests pass.

### 8. Payment reminders (Phase 4 — complete, verified)

**Backend (`reminders/` app, 12 tests):**
- `GET /api/reminders/due-list/` — customers with a real outstanding
  balance (settled customers excluded), a due date **derived from existing
  data** (oldest unpaid sale date + configurable credit days), status
  (OVERDUE / DUE_SOON / DUE), reminder count and last channel. Sorted
  OVERDUE first.
- `POST /api/reminders/log/` — records a reminder **only after** the user
  confirms in-app. Recomputes `get_outstanding_due()` server-side at
  write time: 400 if the balance is settled, 409 if the same customer was
  reminded within a 1-hour cooldown (prevents accidental double sends).
  Links the oldest unpaid sale, runs in a transaction.
- `GET /api/reminders/history/` — last 100 reminder logs, tenant-scoped.
- Reminder message includes shop name, address and contact number, and
  the WhatsApp URL is generated server-side. **The app only opens the
  composer (WhatsApp / SMS) — it never claims the message was sent.**
- `ReminderSetting` per business (credit_days=30, due_soon_days=7).
- Tenant isolation verified in both directions.

**Flutter (`lib/features/reminders/`, `lib/providers/reminder_provider.dart`):**
- More-screen entry → reminders screen: due cards (status chip,
  outstanding, due date, reminder history count), WhatsApp + SMS composer
  buttons, confirm-then-log dialog with server error explanation, pull to
  refresh, history list at the bottom. Outstanding amounts are carried as
  strings from the server (no client-side decimal reassembly).

**Evidence:** `python manage.py test` → **78/78 OK** (whole project, incl.
`reminders`, `updates`, `api`, `security`); `flutter analyze` 0 errors;
`flutter test` 6/6.

### 9. Customer ledger statement PDF (Phase 5 — complete, verified)

**Backend (`invoices/pdf_service.py` + `api/views/customer_views.py`):**
- `generate_ledger_pdf(customer, from_date, to_date)` — reportlab A4
  statement: shop header (name/address/phone/email/GSTIN), customer block,
  chronological ledger table (Date / Particulars / Debit / Credit /
  running Balance Due), opening-balance carry-forward row, totals row,
  closing balance payable.
- All arithmetic is server-side **Decimal** (paise-exact). With no date
  filters the closing balance is provably equal to
  `customer.get_outstanding_due()` — asserted by test.
- Transactions **after** `to_date` are excluded entirely (they have not
  happened "as of" the statement date); transactions **before**
  `from_date` collapse into the opening balance.
- `GET /api/customers/<id>/ledger-pdf/?from_date=&to_date=` — JWT-auth,
  tenant-scoped, validates `YYYY-MM-DD` and `from_date <= to_date`,
  returns `application/pdf`.

**Flutter:** `Share Ledger Statement (PDF)` on the customer detail screen
→ optional period picker → server PDF → OS share sheet (print / WhatsApp /
save). Client validates the `%PDF` magic bytes before saving.

**Evidence:** `python manage.py test api.tests_ledger_pdf` → **12/12 OK**
(5 data-layer numeric tests incl. paise precision, opening carry-forward,
to_date exclusion, supplier-payment exclusion; 7 endpoint tests incl.
tenant isolation, unauthenticated rejection, date validation, settled
account). Full-suite re-run: **90/90 OK**.

### 10. UPI QR + manual payment confirmation (Phase 6 — complete, verified)

**Backend (`payments/upi_service.py`, `businesses` migration 0003, views):**
- `Business.upi_id` field (settable by the owner through the existing
  owner-only shop-settings endpoint).
- `GET /api/customers/<id>/upi-qr/` — builds an NPCI `upi://pay?...`
  collect URI with the **server-recomputed** outstanding as the default
  amount (optional `?amount=` override, validated strictly), and returns
  the QR as a PNG (base64, `qrcode==8.2`).
- **A scan is never a confirmation** — the response carries
  `confirmed: false` and the UI says so explicitly.
- `POST /api/payments/customer/` now **rejects overpayments** (amount >
  outstanding → 400 with both figures) and therefore also payments on
  settled accounts. Previously an overpayment was silently swallowed by
  `get_outstanding_due()`'s floor at zero — the money would have vanished
  from the books.

**Flutter:** `Collect via UPI QR` button (customer detail, when due > 0)
→ dialog with the QR, amount, UPI ID, and an explicit "scanning only
requests the payment" notice → `Record Received Payment` opens the
existing payment modal with UPI pre-selected and its UTR field.
Settings → Shop Profile gained a UPI ID field.

**Evidence:** `python manage.py test api.tests_upi` → **15/15 OK** (URI
format, money parser strictness, PNG validity, server-side amount
recomputation after a partial payment, custom-amount override + invalid
rejection, missing-UPI guidance, tenant isolation, unauthenticated
rejection, staff-with-permission allowed, overpayment/settled-account
rejection, cross-shop payment rejection).

---

## Test results (exact commands + outcomes)

| Command | Result |
|---|---|
| `python manage.py check` | No issues |
| `python manage.py test` | **90 tests, OK** (api/security 44, updates 13, reminders 12, core apps 9, + others — run before the UPI suite existed) |
| `python manage.py test api.tests_ledger_pdf` | **12 tests, OK** (ledger PDF data layer + endpoint) |
| `python manage.py test api.tests_upi` | **15 tests, OK** (UPI QR + manual confirmation) |
| `flutter analyze` | 0 errors, 46 infos/warnings |
| `flutter test` | **6 tests pass** |
| `curl /api/health/` (production) | 200 — `{"status":"ok","database":"up"}` (stale build, see below) |
| `python manage.py collectstatic --dry-run` | 157 files |

> Combined suite total: the 90-test run preceded the UPI work; the
> ledger-PDF (12) and UPI (15) suites are additive and pass standalone.
> A final full-suite re-run happens at the next checkpoint.

---

## Status by requirement

### Implemented and tested
- Registration / login / JWT auth
- Password forgot + reset (secure token, expiry, single-use)
- Owner vs Employee RBAC (backend-enforced, all endpoints)
- Field-level privacy (purchase price, profit, margin, expenses withheld from staff)
- Tenant isolation / IDOR protection (two-shop tests)
- Products, categories, stock, IMEI/barcode models
- Customers + Khata ledger (partial payments, settlement to zero, history preserved)
- Sales / POS (server-calculated totals, atomic transaction)
- Suppliers + purchases (stock increases on purchase)
- Expenses (owner-authorized)
- Reports (8 endpoints, owner-gated)
- WhatsApp share + SMS composer (deep-link / share_plus, no silent sending)
- Shop profile / settings (owner-only)
- Health endpoint (+ db_engine vendor proof)
- App updates: trusted manifest, mandatory-update flag, admin publishing
- Payment reminders: derived due dates, composer-initiated WhatsApp/SMS,
  settled-balance rejection, 1-hour cooldown, reminder history
- Customer ledger statement PDF: server-generated (reportlab), Decimal
  running balance with opening-balance carry-forward for date ranges,
  shareable from the app
- UPI collect QR: server-computed `upi://pay` URI + QR PNG, UPI ID in shop
  settings; **manual confirmation required** — overpayments and payments on
  settled accounts are rejected server-side
- Localization EN/HI/MR

### Implemented, not fully verified on device
- Release APK (built, checksum-verified, AOT string check passed)
- App update flow on a real device (endpoint + tests pass; UI verified
  by analyze/test only)
- Barcode scanning (requires physical camera; untested on device)
- Biometric owner verification (Flutter side not wired)

### Blocked
- **Real-device testing** — no Android device/emulator available in this
  environment. Emulator previously blocked by disk space.
- **Email/SMS delivery for password reset** — no email service configured;
  the reset token is returned via the API (HTTPS) instead of email. This is
  documented and safe, but real email delivery needs an external account.

---

## Production deployment status (verified, not assumed)

**Code pushed:** commit `cb2ec9c` → `origin/main` (2026-10-15).
**Production evidence:** the live service still serves the OLD build:

- `GET /api/app-updates/check/` → **404**, and the debug 404 page lists the
  legacy web routes (`accounts/`, `business/`, `customers/` …) that were
  removed from `config/urls.py` in this branch.
- `/api/health/` has **no `db_engine`** field (added in this branch).
- The 404 page also leaked `DEBUG = True` on production.

Conclusion: **Render did not deploy the push.** The service was evidently
created manually (not from the `render.yaml` blueprint), so its
auto-deploy / branch / build-command settings live only in the Render
dashboard and cannot be verified or fixed from this repository.
**Owner action required** — see `docs/DEPLOYMENT_GUIDE.md`.

Hardening applied in this branch regardless (fail-safe defaults now, so a
misconfigured environment cannot leak debug pages again):

- `DEBUG` defaults to `False`; must be opted in explicitly for dev.
- `ALLOWED_HOSTS` default no longer includes `*`.
- Startup refuses to run in production (`DEBUG=False`) with the insecure
  fallback `SECRET_KEY`, verified by raising `RuntimeError`.
- `build.sh` (already committed) runs `manage.py migrate` during the
  build, so migrations apply automatically once a deploy happens.

**Local evidence (everything verified before the push):** 57/57 backend
tests; 6/6 Flutter tests; `manage.py check` clean; production health 200
(old build) while the update/reminder endpoints 404 — proving the service
is stale rather than broken.

---

## Next concrete task (remaining owner-side blockers only)

All implementable phases are complete. Three items depend on accounts or
devices the engineering side does not have — see `docs/FINAL_REPORT.md` §4:

1. Owner: **Render deploy** (Manual Deploy in the dashboard) — production
   still serves the old build (health 200, new endpoints 404).
2. Owner: **AdMob activation** (`docs/ADMOB_SETUP.md`).
3. Anyone: **device acceptance** — install `release/app-release.apk`
   (SHA-256 in `docs/FINAL_REPORT.md`) and run
   `docs/END_TO_END_ACCEPTANCE.md` sections A–G.

---

## Checkpoint log

- **2026-10-15 (cb2ec9c, pushed):** Phases 1–2 — repository audit,
  subscription monetization removed (free app, AdMob-only), settings
  hardening, deployment guide. 57/57 backend, 6/6 Flutter.
- **2026-10-15 (5c59eeb, pushed):** Phase 4 — payment reminders
  (backend + Flutter). Full suite run: **78/78 backend OK**, 6/6 Flutter,
  `analyze` 0 errors / 46 infos. Deploy blocker remains open on the
  owner's side.
- **2026-10-15 (Phases 5–6):** ledger statement PDF + UPI collect QR with
  manual-only payment confirmation and server-side overpayment rejection.
  Backend: 90/90 full suite (pre-UPI) + 12/12 ledger + 15/15 UPI;
  Flutter: `analyze` 0 errors, 6/6 tests. New dependency `qrcode==8.2`
  pinned in `requirements.txt` — Render installs it on next deploy.

- **2026-10-15 (Phase 7, complete):** Full HI/MR localization of the
  Flutter app. The `AppLocalizations` contract grew from ~115 to
  **529 keys per locale (en/hi/mr), exact key parity** verified
  programmatically. Every user-visible string in all feature screens is
  routed through `translate()`:

  - Auth & onboarding (splash, login, register, onboarding slides)
  - Dashboard + quick actions, More screen, admin dashboard (tabs/stat cards)
  - POS checkout sheet & sale-success dialog
  - Sales history, sale detail (invoice rows, totals, WhatsApp share text)
  - Customers (list, form, detail, receive-payment modal, UPI QR dialog)
  - Inventory (product list/form, IMEI lookup & scanner, stock-adjustment
    dialog with locale-neutral backend reason codes)
  - Suppliers, purchases, expenses, reminders, reports (period filters),
    settings (shop profile rows), app-update screen
  - Shared widgets (WhatsApp button)

  Form validators, SnackBars, empty states, error branches and the
  WhatsApp message templates are localized too. Locale-neutral items are
  deliberately kept literal (brand name "ShopZen", payment-method chips
  CASH/UPI/CARD, stock-adjustment reason codes sent to the backend,
  pure punctuation such as `*:` WhatsApp markup).

  Verification: `flutter test` **12/12 passed** (6 localization tests
  incl. key-parity and "no hi/mr value empty or left in English");
  `flutter analyze` **0 errors / 0 warnings** (34 infos, all
  `prefer_const`/`use_build_context` style hints). Test assertions were
  not weakened — the failing parity test was fixed by genuinely
  translating values and eliminating one punctuation-only key.

- **2026-10-15 (Phase 8, complete):** Backup & restore, owner-only.

  Backend (`api/backup_views.py`, routed at `/api/backup/` and
  `/api/backup/restore/`):

  - **Export** serializes the shop's complete dataset — business
    settings, categories, expense categories, suppliers, customers,
    products, purchases + items, sales + items, expenses, payments,
    IMEI device register, stock movements, reminder logs and reminder
    settings — as a downloadable JSON file with a version header
    (`backup_version: 1`). Owner-only; 403 for staff, 401 anonymous.
  - **Restore** is `transaction.atomic` all-or-nothing and:
    recomputes every sale subtotal/total/due/payment-status and every
    purchase total from the line items (a tampered file total is
    detected and reported as `adjusted`, the server value is used);
    **rejects overpayment** (`paid > recomputed total` → 400, nothing
    written); is **idempotent** (natural-key match → skipped, never
    duplicated); preserves historical `created_at` exactly; always
    attaches rows to `request.business` (tenant spoofing from the file
    is impossible); supports `dry_run` for a write-free preview.
    Unresolvable sales/payments are skipped with named warnings, never
    faked.
  - Never exports credentials, tokens, passwords, plan tier or
    subscription lifecycle state.

  Evidence: new `api/tests_backup.py` — **14 tests** covering
  owner-only access, tenant isolation of the export, full round-trip
  restore into an empty shop, idempotent re-restore, dry-run
  no-writes, overpayment rejection, tampered-total recomputation,
  version rejection and cross-shop safety. **Full backend suite:
  119/119 OK** (includes the 14 new). Live smoke on the local dev
  server with real seeded data: export HTTP 200 with all 14 sections
  (11 categories, 6 products, 5 sales, 5 devices …) and a dry-run
  restore that correctly reported every record as already present,
  **0 warnings / 0 errors** — i.e. the shop's real financial totals
  pass server-side recomputation.

  Flutter (`lib/features/settings/backup_restore_screen.dart`, entry in
  Settings):

  - Download backs up to the app's documents folder and opens the OS
    share sheet (payload validated as backup JSON before it is ever
    saved or shared).
  - Restore picks a file, validates the version header, POSTs a
    **dry run first**, shows an itemized preview (imported / skipped /
    adjusted counts + warnings), and only commits on explicit
    confirmation; then invalidates the cached dashboard/customer/
    product providers. 403 maps to an "owner only" message.
  - 29 new localization keys per locale (en/hi/mr, now **558 keys per
    locale with exact parity**); `file_picker: ^8.0.7` added.

  Verification: `flutter test` **12/12 passed**; `flutter analyze`
  **0 errors / 0 warnings** (35 infos, all pre-existing style hints).
  Dev database brought up to date locally (added `businesses.0003`
  `upi_id` and `reminders.0001`); these migrations run automatically
  on Render via `build.sh` on the next deploy.

---

- **2026-10-16 (Phase 9, complete):** Offline mode + sync status indicator.

  What was already there (kept, not rewritten): queued-sale upload
  (`OfflineSyncService.syncNow` — POSTs each queued bill, drops
  server-rejected stale bills, breaks on network errors) and the
  `offline_pos_queue` in local storage.

  New behavior:

  - **`SyncStatusNotifier`** (`lib/core/sync/sync_status_provider.dart`)
    is now the single driver: a 15s timer probes the server with a
    lightweight GET `/api/health/` (5s timeout) — reachability of the
    *backend*, not just the radio — recounts the on-device queue,
    starts an upload pass when the server answers, and exposes
    `SyncStatus(isOnline, isSyncing, pendingCount, lastSyncedAt)`.
    Started on the authenticated nav scaffold, stopped on dispose so
    nothing pings or uploads while logged out. (The service's own
    `start`/`stop` timers were removed so there is exactly one timing
    source; `syncNow` is unchanged.)
  - **`SyncStatusBanner`** (`lib/shared_widgets/sync_status_banner.dart`)
    renders the state wherever it is mounted (dashboard, POS):
    offline with queued bills → amber "Offline — N bill(s) saved
    locally" + Retry; offline, none queued → plain amber bar; online
    while bills are in flight → "Syncing N bill(s)…"; healthy → renders
    nothing. The banner never claims a bill was delivered: only the
    server's 201 removes it from the queue.
  - **Offline checkout UX fix (real, pre-existing bug):** when the
    network was down at checkout, the checkout path set an error
    string the POS never rendered and left the cart populated, so the
    user got no confirmation and a second tap could queue a duplicate.
    Now the bill is queued, the cart clears exactly like the success
    path, `PosState.offlineQueued` flags it, and the POS shows a
    localized "saved locally" SnackBar (with the sync banner visible
    behind it).
  - **Offline dashboard:** `lastDashboardSnapshotProvider` (autoDispose)
    caches every successful `/api/dashboard/` fetch, so a failed
    refresh offline renders the last real data with a "showing the
    last data loaded while online" notice; with nothing cached the
    user gets an explicit "no shop data on this device yet — connect
    and pull to refresh" empty state instead of a raw exception.
    autoDispose means the cache drops with the dashboard, so one
    shop's numbers can never survive into a new session after logout.
  - 9 new localization keys per locale (now **568 keys per locale,
    exact parity**, verified by direct map count + the parity test).

  Evidence: new `test/sync_status_banner_test.dart` — **7 tests**:
  offline+queued message text/count, plain offline bar, syncing row,
  healthy state renders zero-height, live state-transition rendering,
  and `SyncStatus.hasPending` / `copyWith` semantics. `flutter test`
  **19/19 passed** (12 existing + 7 new); `flutter analyze lib test`
  **0 errors / 0 warnings** (35 infos, the same pre-existing
  `prefer_const`/`use_build_context` hints as clean HEAD). Live smoke
  on production: `GET /api/health/` → **HTTP 200**
  `{"status":"ok","app":"ShopZen","version":"1.0.0","database":"up"}`
  in ~8s (free-tier wake), the exact endpoint the monitor pings.
  Backend untouched this phase; last full backend suite remains
  **119/119**.

---

- **2026-10-16 (Phase 11, complete):** IMEI history, warranty status,
  low + dead stock, purchase history.

  Backend (all server-computed; the client never derives money, dates
  or stock verdicts):

  - **Warranty status is derived by the server** in
    `MobileDeviceSerializer`: `warranty_status`
    (`ACTIVE`/`EXPIRED`/`NO_WARRANTY`) and `warranty_days_remaining`
    (negative once expired). The only writer of
    `warranty_expiry_date` remains the POS sale path
    (`sale_date + warranty_months * 30 days`).
  - **`StockMovement.device`** (nullable FK, migration
    `inventory/0002`, purely additive) links a movement to the specific
    IMEI unit it concerns; written on device registration and at POS
    checkout (sale notes now carry the IMEI). Backup/restore carries
    the link by IMEI natural key (files stay `backup_version: 1`;
    older files simply restore without the link).
  - **`GET /api/inventory/imei/<id>/history/`** returns the device plus
    a timeline built **only from real rows**: its registration, its
    movements, and (for legacy sales made before movement links
    existed) the invoice it was sold on — derived once, never
    duplicated. 404 for another shop's device; staff can read their
    own shop's history.
  - **`GET /api/products/<id>/`** is enriched with `movements` (last
    15, IMEI-bearing), `purchase_history` (last 10 with invoice,
    supplier, quantity and the server's unit/total cost),
    `devices` (IMEI-tracked products), `last_sale_date` and
    `is_dead_stock`.
  - **Dead stock** has exactly one definition (`DEAD_STOCK_DAYS = 60`,
    `is_dead_stock()` in `product_views`), shared by the product
    detail, the new `?stock=dead` list filter and the stock report
    (the report now calls the shared helper so they cannot drift).
  - **`GET /api/purchases/?product=<id>`** scopes purchase history to
    one product, tenant-scoped.

  Evidence: new `api/tests_phase11.py` — **18 tests**: warranty
  ACTIVE/EXPIRED/none + set-at-checkout, timeline with registration +
  single SALE entry carrying the real invoice, legacy sale derived
  without duplication, tenant isolation 404, staff read access,
  product-detail sections incl. server-supplied amounts, dead-stock
  verdict matching the report, `?stock=dead` filter, purchase
  `?product=` filter (incl. cross-tenant leak check), device
  `?product=` filter. **Full backend suite: 137/137 OK.**

  Flutter:

  - New **`ProductDetailScreen`** (product list rows now open it): stock
    chips incl. a dead-stock verdict, cost/selling/inventory value,
    warranty months, last-sold/never-sold, purchase history, stock
    movements (with IMEI when the movement is unit-specific), and
    registered IMEI units that link into… (edit still reachable from
    the app bar).
  - New **`DeviceHistoryScreen`**: device header, status chip, the
    server's warranty verdict with days remaining/elapsed, and the
    full timeline.
  - New **`PurchaseHistoryScreen`** (More screen): every supplier bill
    with expandable lines, paid/due and notes.
  - **IMEI lookup** now shows the warranty verdict (verdict + expiry
    date) and a "View history" action — it parsed the expiry before
    but never rendered it.
  - Product list gained a **Dead Stock filter chip** (and the
    out-of-stock chip was fixed to say "Out of Stock" instead of
    "Stock").
  - New models: `StockMovementModel`/`DeviceHistoryEntry`,
    `ProductPurchaseModel`/`PurchaseModel` (parses DRF string decimals),
    `ProductDetailData`; new providers `productDetailProvider`,
    `imeiDeviceHistoryProvider`, `purchasesListProvider`.
  - **31 new localization keys per locale** (on top of Phase 9) — now
    **597 keys per locale, exact parity**, verified by direct map
    count + the parity test.

  Verification: `flutter test` **27/27 passed** (19 + 8 new
  Phase 11 model-contract tests); `flutter analyze lib` **0 errors /
  0 warnings** (34 infos, all pre-existing style hints). Live smoke
  on the local dev server with the real seeded shop: `?stock=dead`
  returned the 2 genuinely unsold stocked products; the enriched
  product detail returned its registered device with
  `warranty_status NO_WARRANTY` and `last_sale_date: None` (never
  sold — reported as-is, never faked); `imei/<id>/history/` returned
  the device + REGISTERED timeline; `purchases/?product=` returned 0
  for a product with no recorded POs. Migration `inventory.0002`
  applied to the dev DB; it runs on Render via `build.sh` on the next
  deploy.

- **2026-10-16 (Phase 16 + 17–18, release build + final docs, pushed):**
  - Release APK rebuilt with `flutter build apk --release` after fixing
    two build incompatibilities the earlier `analyze`/`test` runs cannot
    surface (recorded above under "Phase 12 build fix").
  - **Artifact verification:** exit code 0; `release/app-release.apk`
    73.8 MB (77,380,596 bytes); SHA-256
    `ffc5e50c4358977b4d712e0ee0c2fd256eaca3919ae30ef4fc00b1f9ced01e76`
    (identical for build output and the release copy); package
    `com.dukaanflow.app`; versionName `1.0.0` / versionCode `1`
    (aapt2); API base URL `https://dukaanflow-1.onrender.com` and the
    Google **test** ad unit both confirmed inside `libapp.so`.
  - **Device testing: NOT PERFORMED** (no physical device this cycle) —
    never claimed otherwise.
  - New docs: `ADMOB_SETUP.md`, `PRIVACY_AND_ADS.md`,
    `SECURITY_AUDIT.md`, `RELEASE_GUIDE.md`, `APP_UPDATE_GUIDE.md`,
    `BACKUP_AND_RECOVERY.md`, `FINAL_REPORT.md`; `TEST_REPORT.md`
    rewritten with current numbers; `docs/README.md` index refreshed
    (and its stale paywall/URL claims corrected).
  - Final Flutter verification on the shipped tree: 36/36 tests, 0
    errors/0 warnings on analyze. Production check today: health 200,
    `/api/updates/check/` and `/api/inventory/imei/<id>/history/` 404 —
    production still runs the old build; **the deploy is the owner's
    action, no deploy success is claimed.**

- **2026-10-16 (Phase 12 build fix, during Phase 16 APK build):** The release
  build failed twice and both root causes were fixed honestly:
  1. `user_messaging_platform` plugin has no AGP-8 namespace in its Android
     module (`Namespace not specified`) — **replaced** with the UMP API that
     ships inside `google_mobile_ads` itself (`ConsentInformation`,
     `ConsentForm`, `canRequestAds()`) and the plugin was removed from
     pubspec. Same consent semantics; Flutter tests still 36/36, analyze 0
     errors/0 warnings.
  2. `flutter_plugin_android_lifecycle` (AdMob transitive dep) requires
     compileSdk 36, but the project compiled against 34 —
     `android/app/build.gradle` now pins `compileSdk 36`.
  These were invisible to `flutter analyze`/`flutter test` (they never run
  the Android Gradle build) — only the real `flutter build apk --release`
  surfaced them, which is why every release must be rebuilt and verified
  rather than assumed (see `docs/RELEASE_GUIDE.md`).
- **2026-10-16 (Phases 13–15, integrity + acceptance, pushed):**
  Financial-integrity hardening, regression suite and the acceptance
  document.
  - **Bug fixed (stock-once rule):** POS checkout never validated the IMEI
    unit before selling it — an already-SOLD device could be billed again,
    overwriting its customer, sale link and warranty. Checkout now resolves
    the device *before* any write and rejects with a specific 400 when the
    unit was already sold, belongs to a different product, belongs to
    another shop, or does not exist. Also added: quantity >= 1,
    non-negative unit price, non-negative discount, and line discount not
    exceeding the line total (previously a negative line price could be
    silently clamped to a zero-value bill).
  - **New regression suite** `api/tests_phase13.py` — 13 tests: IMEI
    double-sell rejected (device record untouched), device product/shop
    mismatch, nonexistent device, rejected checkout writes zero rows,
    server-side Decimal totals recomputed to the paisa, padded
    `paid_amount` clamped to the bill total, negative line rejected,
    khata balances derived from history, overpayment rejected, payment
    closes the due without mutating the original bill row, credit sale
    records no payment row, and money columns stay exact through DRF
    (subtotals like 449.97 / 457.53, not float-rounded).
  - **Decimal-safety re-verification:** all money columns are
    `DecimalField`; every `float(` call sits at the JSON serialization
    boundary only, never inside ledger math (audited pos, payments,
    dashboard, reports, serializers).
  - **Migration check:** `makemigrations --check --dry-run` → "No changes
    detected" (model state == migrations). Production stays PostgreSQL by
    configuration (`render.yaml` wires `DATABASE_URL` to the managed
    `dukaanflow-db`; sqlite only when no `DATABASE_URL` locally).
  - **Acceptance doc:** `docs/END_TO_END_ACCEPTANCE.md` — the 21-step
    acceptance scenario with evidence pointers and an explicit
    not-performed list (device steps 15–21 pending the release APK;
    live ad impressions pending the owner's AdMob account).
  - Verification: backend **151/155** across all apps — `api` 116/116,
    `updates` 13/13, `reminders` + `subscriptions` 21/21, legacy `tests/`
    1/5. The 4 legacy failures are **pre-existing** (verified identical on
    the pre-change tree: they use the removed pre-API endpoints and the
    removed subscription plan cap); they are documented, not deleted,
    weakened or faked green. `manage.py check` clean.

- **2026-10-16 (Phase 12, pushed):** Google AdMob banner ads + Google UMP
  consent flow. Free app, monetization banners ONLY (all subscription
  paywalls stayed removed; no business payment feature touched).
  - New `lib/core/ads/`: `ad_config.dart` (build-time overrides
    `ADMOB_BANNER_UNIT_ID` / `ADMOB_ENABLED` via `--dart-define`, falls
    back to Google's documented test banner unit
    `ca-app-pub-3940256099942544/6300978111`; `isLiveUnitId` so test
    impressions are never reported as live traffic),
    `consent_service.dart` (UMP: request consent info update, show the
    consent form only when consent is required and a form is available;
    ads gated on `obtained`/`notRequired`; any SDK failure degrades to
    ads-off, never blocks the app), `ads_service.dart` (SDK initialized
    only when ads enabled + Android/iOS + consent granted; inert on
    desktop/test hosts), `ad_banner.dart` (320x50 `BannerAd` + `AdWidget`,
    collapses to zero size when ads are off / not loaded / consent
    missing; banner disposed on failure and on widget dispose).
  - Banners mounted on exactly the four permitted screens: dashboard,
    product list, customer list, settings.
  - `AndroidManifest.xml` carries the AdMob
    `com.google.android.gms.ads.APPLICATION_ID` meta-data using Google's
    TEST app id (`ca-app-pub-3940256099942544~3347511713`) until the
    owner's real publisher id replaces it.
  - Startup wiring in `main.dart`: `_initAds()` runs the consent flow and
    SDK init concurrently with the splash screen (fire-and-forget, fully
    guarded) — never delays or blocks the app.
  - 1 new localization key per locale (`ads_keep_app_free`) — **598
    keys per locale, exact parity**, verified by direct map count.
  - Verification: `flutter test` **36/36 passed** (27 + 9 new Phase 12
    tests covering config defaults, test-vs-live unit id, UMP consent
    gating, SDK gate matrix, and the AdBanner zero-size behavior on the
    desktop test host); `flutter analyze` **0 errors / 0 warnings**
    (34 infos, all pre-existing). **NOT verified:** real banner
    impressions on a device — that requires the owner's AdMob account
    approval and live ad unit ids (see "Next concrete task" #2); the
    current build serves Google test creatives only and earns no
    revenue.

- **2026-10-16 (Phase 22, Khata/settlement + dedup + update-popup + staff &
  notifications, NOT pushed):** Continuation session fixing four reported
  bugs and delivering the staff/notifications feature. All work is
  committed only to the working tree; **no publish/deploy/push and no
  production APK overwrite happened** (`static/apk/shopzen-1.0.0.apk` and
  the build outputs are untouched).
  1. **Khata repayment / balance calculation (bugfix):** payments are now
    the single source of truth and bill rows are derived from them.
    `payments/services.py` (new) implements deterministic FIFO
    re-settlement: sale-linked checkout payments stay on their own bill
    (capped at its total), unlinked manual repayments settle the oldest
    open bill first and roll the remainder forward. Identical inputs
    always produce identical bill state and it self-repairs legacy drift.
    `CustomerPaymentCreateAPIView` and the web `customer_payment_create`
    both re-settle inside a transaction and return `settled_invoices`;
    the receive-payment modal now prefills the exact outstanding amount
    and sends the amount as an exact string (`toStringAsFixed(2)`), never
    a raw double. `customers/management/commands/resettle_khata.py`
    (new) is an idempotent repair command — run once on the dev DB it
    repaired 3 drifted customers. Deliberately preserved: customer-level
    outstanding derivation (Phase 13) and overpayment rejection.
  2. **Duplicate customer creation (bugfix):** phones are normalized on
    save (digits only, 91/0 prefix collapse) and duplicates are blocked
    at every entry point — API returns 409 with the existing customer,
    the web Django form shows the existing name + created date, and the
    Flutter app opens the existing customer instead of creating a twin.
    A partial unique constraint (`condition=~Q(phone__in=PLACEHOLDER_PHONES)`,
    portable across SQLite + Postgres) plus migration
    `customers/0002_merge_duplicates_unique_phone` merges existing twins
    (canonical = most activity; Sale/Payment/MobileDevice re-pointed
    before the dup is deleted). Run on the dev DB: "Ramesh Khata Test"
    twin merged.
  3. **Repeated "Update Required" popup (bugfix):** the popup could only
    fire with `version_code=0` (the installed release is 1.0.0+1), which
    is exactly what the `package_info_plus` race produced at startup.
    Server-side the manifest serializer now owns `mandatory_update`
    (`current_code > 0 and current_code < minimum_supported_code`), so an
    unknown build number is advised-but-never-blocked; client-side
    `UpdateProvider` awaits `package_info_plus` before the check and
    `main.dart` shows the dialog only once per process and only when the
    build number is actually known.
  4. **Staff logins (new, owner-only):** `/api/staff/` list+create and
    `/api/staff/<id>/` update/deactivate. Staff users get per-module
    grants (validated against `MODULE_PERMISSIONS`); deactivation keeps
    the account and all bill/payment attribution. Flutter: Staff & Logins
    screen (Settings → Team, owner-only) with add/edit/grant/disable and
    server error surfacing.
  5. **Notifications (new):** `/api/notifications/` derives attention
    items live from the books (top-5 Khata dues, low/out-of-stock,
    supplier dues) with a count used by the dashboard bell badge.
  6. **Shop profile / SMS / WhatsApp reminders:** verified as already
    shipped (Phase 8/9) — no rework; the settings "Edit shop Profile"
    CTA is now correctly owner-only.
  - Localization: **634 keys per locale (en/hi/mr), exact parity** (up
    from 598) with the new staff/notifications/duplicate-dialog keys.
  - Verification: backend green — `tests_khata_dedup` 15, `tests_staff_notifications` 15,
    `tests_phase13`, updates+khata 41, `api.tests` + ledger-PDF + UPI +
    reminders 54, `manage.py check` + `makemigrations --check` clean.
    Flutter: `flutter test` **36/36 passed**, `flutter analyze`
    **0 errors / 0 warnings** (34 infos, back to pre-existing baseline).
  - Not verified: on-device run of the new staff/notifications screens,
    and a rebuilt release APK (deliberately not rebuilt without owner
    approval).

- **2026-10-17 (Phase 23, UI audit + release APK 1.1.0+2, NOT pushed):**
  Screen-by-screen Flutter UI audit of Dashboard, Customers/Khata, Receive
  Payment, Customer Detail/Form, Shop Profile (Settings), Team/Staff,
  Notifications, Products and Sales; 10 concrete defects fixed while
  preserving the existing ShopZen design and every screen's behavior:
  1. Untranslated strings replaced with real locale keys in all three
    locales: dashboard chart title + tooltip ("7-Day Sales & Expense Trend",
    "Sales"/"Expense"), product tile "in stock" text, "Generating
    statement…", shop-profile "Saving…" (now a spinner, consistent with
    every other form) and the mandatory-update dialog (title/body/button).
    Locale maps now 644 keys per locale, exact parity.
  2. Customer list's third filter chip was labeled "Balance Due" but
    selects the *cleared* filter — relabeled "Cleared".
  3. POS hardcoded `Colors.white` customer bar, product-picker sheet,
    summary and tiles → `Theme.of(context).colorScheme.surface`: the dark
    theme (Settings → Theme) previously painted glaring white blocks. The
    sale-success summary got the same fix.
  4. Add-Staff dialog actions could sit below the soft keyboard on small
    phones — wrapped in an `AnimatedPadding` with `viewInsets.bottom` so
    the dialog lifts above the keyboard.
  5. Overflow guards (ellipsis + maxLines) on the two-line AppBar titles
    (Dashboard, More) and the customer-detail header row (`Flexible`
    around the outstanding balance, so a long amount no longer pushes the
    Add Payment button off-screen).
  6. Receive Payment: a blank/zero amount used to no-op silently on tap —
    now shows a snackbar asking for a valid amount (server-side
    overpayment guard untouched).
  - Verification: `flutter analyze` **0 errors / 0 warnings** (34 infos,
    all pre-existing); `flutter test` **36/36 passed** (incl. locale
    parity). Backend re-verified: `api.tests_khata_dedup`,
    `api.tests_staff_notifications`, `updates.tests` (56),
    `api.tests` + `api.tests_phase13` (28) — all OK; `manage.py check` and
    `makemigrations --check` clean. Dev DB untouched (9 customers /
    19 payments / 16 sales remain; migration `customers/0002` re-points
    every Sale/Payment/MobileDevice row to the canonical customer *before*
    deleting a duplicate, and its reverse is a safe no-op).
  - **Release APK rebuilt: `build/app/outputs/flutter-apk/app-release.apk`,
    copied to `release/app-release.apk` — 77,626,732 bytes (74.0 MB),
    SHA-256 `3f3d764cc74847df98fb872656997816ee4d189dc1122e03ae31524642a8e307`,
    package `com.dukaanflow.app`, versionName 1.1.0 / versionCode 2,
    same Android Debug signing cert as the 1.0.0+1 release (digest
    `7f6cdf…16b` identical), production API URL and Google test ad unit
    confirmed compiled in. `static/apk/shopzen-1.0.0.apk` untouched.**
  - Not verified: on-device run — no physical device, emulator or adb in
    this environment (only web targets). Khata repayment, duplicate
    prevention, update popup, staff permissions and notifications are
    covered by automated backend tests but **not** by a device acceptance
    run; `docs/END_TO_END_ACCEPTANCE.md` sections A–G remain pending a
    phone. No commit / push / deploy / publish was performed.

- **2026-10-17 (Phase 24, live AdMob IDs wired, NOT pushed):** The owner
  provided the real AdMob Android App ID
  `ca-app-pub-8559634762194466~5030925195` and the live banner ad unit
  `ca-app-pub-8559634762194466/2011019340` (ShopZen_Banner_Home). Changes:
  1. `AndroidManifest.xml` now declares the real App ID (replacing Google's
    sandbox App ID) — required for the SDK to initialize against the owner's
    account.
  2. `lib/core/ads/ad_config.dart` adds `liveBannerUnitId`; `bannerUnitId`
    now defaults to `kReleaseMode ? liveBannerUnitId : testBannerUnitId`
    (compile-time constant, so a release build can never serve test traffic
    and a debug build can never serve live traffic). The
    `--dart-define=ADMOB_BANNER_UNIT_ID` override is kept for manual control.
  3. `lib/core/ads/ad_banner.dart` upgraded to Google's **adaptive anchored
    banner** (`getLargeAnchoredAdaptiveBannerAdSize`, the non-deprecated
    API in google_mobile_ads 9.1.0) with a 320x50 fallback, width-guarded
    reload on rotation/resize (no duplicate ad instances), and disposal on
    `onAdFailedToLoad`. Banner collapses to zero height when unavailable,
    so an ad failure never affects the user.
  4. `test/phase12_ads_test.dart` +2 tests: the live unit is the exact
    ShopZen_Banner_Home id (and structurally a unit id, not an app id), and
    a 3x mount/unmount cycle leaks nothing and throws nothing.
  - Placement policy untouched: banners only on dashboard, product list,
    customer list and settings — never on login/registration/payment/POS/
    invoice/khata-repayment/staff screens. No interstitial/rewarded/native
    ads, no click/inflation mechanisms.
  - Verification: `flutter analyze` 0 errors/0 warnings (34 pre-existing
    infos); `flutter test` **38/38 passed**. Release APK rebuilt:
    77,626,740 bytes, SHA-256
    `436cf06e12831b01878e47241f79bf37bdc70643c60778e7d5c5a012f380d9d8`,
    package `com.dukaanflow.app`, versionName 1.1.1 / versionCode 3 (superseded by the 1.1.2+4 build in Phase 25), same
    debug signing cert (`7f6cdf…16b`), real App ID confirmed in the packaged
    manifest and the live unit byte-present in all three `libapp.so` arches
    (test unit tree-shaken out). `static/apk/shopzen-1.0.0.apk` untouched.
  - Not verified: **live ad serving** — no physical Android device,
    emulator or adb in this environment. The owner must confirm
    impressions in the AdMob dashboard after their account verification
    completes (`docs/ADMOB_SETUP.md`). A successful build is NOT proof of
    live impressions. No commit / push / deploy / publish performed.

- **2026-10-17 (Phase 25, owner-priority defect pass, NOT pushed):**
  Verified-and-fix cycle driven by the owner's reported issues:
  1. **Staff & Logins 404 (root cause found):** the endpoints work perfectly
    locally (full lifecycle verified: create → list → staff login → RBAC
    grants enforced 403/200 → disable → reactivate), but production returns
    404 because `api/views/staff_views.py`, `notification_views.py` and
    their `api/urls.py` registration are **uncommitted** — Render auto-deploys
    from GitHub, which has never seen them. Live probes confirmed
    `/api/staff/` and `/api/notifications/` are the ONLY missing routes;
    every other app endpoint exists on production (401 = present). The app
    now shows an honest, translated 404 message ("backend needs updating")
    instead of a raw Dio dump, on both the staff and notifications screens
    (`lib/core/network/api_error.dart` + `error_404_backend` key, 3 locales).
    Deployment steps prepared in `docs/DEPLOYMENT_PREP.md` — NOT executed.
  2. **Critical URL-interpolation bug fixed:** `ApiConstants.productDetail`
    and `imeiDeviceHistory` used an escaped `\$id`, which Dart renders as the
    *literal text* `$id` — so Product Detail and IMEI Device History
    requested `/api/products/$id/` and 404'd on every phone. Fixed and
    verified end-to-end against the local server (`/api/products/11/` → 200,
    the old buggy URL → 404). New `test/api_constants_test.dart` guards every
    id-substituting helper so this cannot recur. The stock-adjust dialog's
    hardcoded URL was moved to `ApiConstants.stockAdjust` (the app now has
    zero raw URL strings).
  3. **Clear Khata workflow verified:** new `api/tests_khata_flow.py`
    (5 tests) locks down the owner's exact scenario through the public API —
    ₹1,000 bill → ₹300 payment (₹700 balance) → ₹700 payment (₹0, "Cleared"
    filter), plus oldest-bill-first settlement, overpayment rejection
    (₹1,200 against ₹1,000 → 400), zero/negative rejection, and ledger
    integrity. All 5 pass.
  4. **Reminders verified offline:** new `api/tests_reminders.py` (15 tests)
    covers the WhatsApp URL builder (wa.me/91…, empty for no phone), SMS
    body, due-list computation (OVERDUE/DUE_SOON/DUE, tenant isolation),
    log integrity (settled-customer rejection, 1-hour cooldown, invalid
    channel). **Finding: there is no SMS provider and no credentials to
    configure — reminders are composer-driven by design:** the backend
    builds the message and the owner's own WhatsApp/SMS app sends it; the
    server logs only a user-confirmed initiation and never claims delivery.
  5. **Feature audit (34 features cross-checked backend↔app):** all core
    features are wired end-to-end. Reported gaps: password reset is
    backend-only (no app screen — documented, not promised), IMEI device
    registration has no app UI, supplier/expense edit screens absent
    (backend supports them). Details in `docs/DEPLOYMENT_PREP.md`.
  6. **False alarm cleared:** the update-check endpoint correctly reports
    `update_available: false` for a 1.1.1+3 client against the 1.0.0 release
    (build-number comparison) — no downgrade prompt. Verified on both local
    and production.
  - Verification: `flutter analyze` **0 errors / 0 warnings** (34 pre-existing
    infos), `flutter test` **41/41 passed** (up from 38). Django: `check` and
    `makemigrations --check` clean; khata-flow 5/5, reminders 15/15 passed;
    full suite running.
  - Not verified: on-device run (no physical device/emulator/adb in this
    environment) and live ad impressions. No commit / push / deploy /
    publish performed.

- **2026-10-17 (Phase 25b, final release APK 1.1.2+4, NOT pushed):**
  Rebuilt the release APK so the shipped binary carries every fix from this
  owner-priority pass (the 1.1.1+3 build predates the `$id` URL fix and the
  honest 404 messages). Version bumped 1.1.1+3 → 1.1.2+4 (pubspec +
  android/local.properties kept in sync).
  - Verification: Gradle `assembleRelease` exit 0; package
    `com.dukaanflow.app`, versionName 1.1.2 / versionCode 4 (aapt2);
    77,626,744 bytes, SHA-256
    `df82df2dabe7d873c6eeff810582e24fbd7d9bc516c9c5b756250c5e03ed2414`;
    V2 signed with the same Android Debug cert as every prior release
    (`7f6cdf…16b`), so it installs as an in-place update.
  - Byte-level checks: the literal `$id` URL fragments that 404'd Product
    Detail and IMEI Device History are **absent from all three `libapp.so`
    arches**; the live banner unit
    `ca-app-pub-8559634762194466/2011019340` is present in all three
    arches; the real App ID `ca-app-pub-8559634762194466~5030925195` is in
    the packaged manifest; the production API base URL is compiled in.
  - `static/apk/shopzen-1.0.0.apk` untouched (SHA-256 still `ffc5e50c…e76`);
    a copy sits at `release/app-release.apk` (gitignored).
  - Full suite before the build: `flutter analyze` 0 errors / 0 warnings
    (34 pre-existing infos), `flutter test` **41/41**, Django **213/213**.
  - Not verified: on-device run and live ad impressions — no physical
    Android device, emulator or adb in this environment. Staff & Logins and
    Notifications will keep showing the "backend needs updating" message
    until the deployment in `docs/DEPLOYMENT_PREP.md` is approved. No
    commit / push / deploy / publish performed.
