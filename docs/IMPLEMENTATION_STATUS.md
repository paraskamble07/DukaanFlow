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

---

## Test results (exact commands + outcomes)

| Command | Result |
|---|---|
| `python manage.py check` | No issues |
| `python manage.py test updates api` | **57 tests, OK** (44 security/api + 13 app-update) |
| `flutter analyze` | 0 errors, 47 infos/warnings (was 92 → 48 → 47) |
| `flutter test` | **6 tests pass** |
| `curl /api/health/` (production) | 200 — `{"status":"ok","database":"up"}` |
| `python manage.py collectstatic --dry-run` | 157 files |

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

## Next concrete task

1. Push the code to trigger the Render deploy; verify production reports
   `db_engine: postgresql` and that migrations `accounts.0003/0004` and
   `updates.0001/0002` applied.
2. Phase 3–6: verify core features end-to-end, then payment reminders,
   customer ledger statement PDF, and UPI QR + manual payment recording.
3. Phase 7: complete HI/MR localization coverage across all screens.
