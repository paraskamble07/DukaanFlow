# ShopZen — Implementation Plan

**Created:** 2026-10-15
**Derived from:** `docs/PROJECT_AUDIT.md` (same-day audit of the actual repo)
**Goal:** Complete ShopZen per the final master prompt — free app with
AdMob-only monetization, all core business features verified end-to-end,
priority features (reminders, ledger PDF, UPI QR, localization,
backup/restore, offline, shop intelligence), tested, and a verified
release APK.

---

## Guiding constraints (from the master prompt)

- Preserve working features, user data, migrations, Android application
  ID (`com.dukaanflow.app`) and signing identity.
- Never weaken tests or fake results; diagnose failures to the root cause.
- Customer/supplier payments, khata, invoices and UPI business
  transactions stay; only **app subscription monetization** is removed.
- Server is authoritative for financial totals; client input can never
  override balances.
- External blockers (AdMob account, real device, email/SMS provider)
  must be documented, with all independent work completed.

---

## Phase 1 — Audit and recovery ✅

- `docs/PROJECT_AUDIT.md` written from real repo inspection.
- Baseline: 57 backend tests (isolated), 6 Flutter tests, `flutter
  analyze` 0 errors / 48 infos, production health 200, verified release
  APK checksum.
- **Root cause of the combined-run test failures (recorded for
  reproducibility):** data migration `updates.0002_seed_initial_release`
  seeds `AppRelease(version_code=1)` into the pristine test database,
  colliding with fixtures that created the same build number. Fix
  applied in `updates/tests.py` setUp: tests clear the seeded rows so
  they are independent of production seed data (assertions unchanged).

## Phase 2 — Remove subscription monetization

- Flutter: delete/neutralize `subscription_screen.dart` entry points,
  "Premium" tiles, subscription banner in `main.dart`, Premium label in
  MoreScreen header and Dashboard.
- Flutter business payment features are untouched (khata, customer
  payments, supplier payments, invoices, UPI details).
- Backend: **no core endpoint gates on plan** (verified in audit), so no
  enforcement change is needed. Keep `subscriptions` tables and routes so
  historical subscription payment data is preserved (no destructive
  migration); the admin payment-verification UI is retired from the app.
- Add tests: every previously paid feature reachable by a normal owner
  (no paywall); customer payments still work.
- Update obsolete subscription docs; keep `PAYMENT_SETUP.md` history note.

## Phase 3 — Core feature completion (trace + verify)

Screen → provider → request → validation → transaction → response → UI.
Adds where missing: product archive, pagination/search behavior checks,
duplicate-purchase protection tests, concurrent-sale oversell test,
invoice and shop details correctness. (Gap list from audit §4 items that
relate to existing modules.)

## Phase 4 — Payment reminders (Priority 1)

- Backend: derive due date from existing sale data (credit sale date +
  configurable credit days); `ReminderLog` model (customer, amount,
  channel, sent_at, note); endpoint listing upcoming/overdue balances
  recalcuated server-side, excluding settled.
- Flutter: reminder list screen (customer, due date, outstanding,
  status), one-tap WhatsApp/SMS composer with shop name + address +
  phone + amount + due date; duplicate-guard (confirm dialog + recent
  reminder shown); settled balances excluded.
- Honest messaging: composer-driven only; automatic sending documented
  as requiring an external provider (blocker documented).

## Phase 5 — Customer ledger statement PDF (Priority 2)

- Backend generation (reportlab or pdfkit) OR Flutter-side generation —
  decided during implementation; decimal-safe from persisted ledger
  entries; shop identity + full address, opening balance, entries,
  running balance, closing outstanding, statement period.
- Share via standard Android sharing; optional WhatsApp.
- NO cross-business data (queryset business-filtered); tests for empty,
  long, partial, settled, date-boundary statements.

## Phase 6 — UPI QR (Priority 3)

- Owner settings: shop UPI ID + payee name (validated format, not
  existence); QR rendered from the configured string.
- Amount + reference display; explicit copy that scanning only
  *initiates* payment.
- Manual confirmation flow for recording a payment (method, amount,
  date, reference) — no invented callbacks.

## Phase 7 — Localization (Priority 4)

- Extend `AppLocalizations` to full coverage of all screens (nav,
  forms, errors, empty/loading states, reminders, settings).
- Persist language choice (already via settings_provider); keep EN;
  verify missing-key fallback; add localization tests.

## Phase 8 — Backup and restore (Priority 5)

- Server is authoritative: full data is re-fetched on login from any
  device.
- Local cache documented; export/import JSON backup validated by
  schema/ownership/version; no tokens in backup files; restore blocked
  across businesses.

## Phase 9 — Offline mode (Priority 6)

- Cache read-only reference data (products, categories, customers);
  online/offline/syncing indicator; durable pending-operation queue with
  idempotency keys; server-side duplicate protection (already partially
  via invoice-number collision skip); conflict handling requires user
  action.

## Phase 10 — Permissions and tenant isolation

- Already implemented and tested; extend audits to new endpoints
  (reminders, PDF, UPI config) and add tests for them.

## Phase 11 — Shop intelligence (Priority 7)

- IMEI sales history (link device → product → sale), warranty duration +
  expiry derivation, configurable low-stock thresholds, dead-stock rule
  (stock + last movement date; labelled "potential"), customer purchase
  history with pagination. Tests for duplicates, cross-business, edge
  cases.

## Phase 12 — AdMob banners only

- Official `google_mobile_ads` SDK; Android App ID in manifest,
  banner Ad Unit IDs configurable per flavor/build; test IDs for dev;
  no production IDs invented.
- Banners on dashboard / product list / customer list / settings only —
  never on login, invoices, payment confirmations, or over controls.
- Consent (UMP) flow; privacy policy updated; no PII in ad parameters.
- Failure-tolerant: ad unavailable ⇒ feature works.

## Phase 13–15 — Integrity, deployment, tests

- Decimal-safe re-verification; stock-once/ledger-history regression
  tests; acceptance scenario (21 steps) in
  `docs/END_TO_END_ACCEPTANCE.md`; migration check; production
  PostgreSQL verification (no silent SQLite); Render deploy evidence.

## Phase 16 — Release APK

- Rebuild after all changes; verify exit code, size, SHA-256, package
  ID, version, API URL, and copy verified artifact to
  `release/app-release.apk` with checksum match. Device test marked
  "not performed" if no device is available.

## Phase 17–18 — AdMob activation + final docs

- `docs/ADMOB_SETUP.md`, `PRIVACY_AND_ADS.md` with honest account
  readiness status and owner actions; complete doc set:
  SECURITY_AUDIT, TEST_REPORT, DEPLOYMENT_GUIDE, RELEASE_GUIDE,
  APP_UPDATE_GUIDE, BACKUP_AND_RECOVERY, END_TO_END_ACCEPTANCE.
- Final factual report with exact test results and remaining blockers.

---

## Execution order

Audit ✅ → subscription removal → core completion → priority features
(reminders → PDF → UPI QR → localization → backup → offline) →
intelligence → AdMob → full test pass → deployment verification →
release APK → final docs/report.
