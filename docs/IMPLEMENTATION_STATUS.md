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

## Next concrete task

1. Owner: re-link Render auto-deploy (or press Manual Deploy) and verify
   the deploy per `docs/DEPLOYMENT_GUIDE.md` (includes the new
   `businesses` 0003 migration).
2. Phase 11: IMEI history/warranty, low + dead stock, purchase history.
3. Phase 12: AdMob banner SDK + UMP consent flow (banners only on
   dashboard, product list, customer list, settings).

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
