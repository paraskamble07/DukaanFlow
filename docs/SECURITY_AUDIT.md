# ShopZen — Security Audit

Auditor: project engineering review
Scope: full codebase as of 2026-10-16 (commits through Phases 13–15)
Verdict: **No high or critical issues open.** Two hardening fixes shipped in
this cycle (double-sell device validation, POS input validation). The
remaining notes are operational, not code defects.

---

## 1. Authentication & authorization

- **JWT (SimpleJWT)** access/refresh; access lifetime short, refresh flow
  implemented in the app.
- Passwords: Django's PBKDF2 validator chain (minimum length 6 + common +
  numeric + similarity checks active in `AUTH_PASSWORD_VALIDATORS`).
- **Role model:** `OWNER` and `STAFF`. Staff read `permissions` list on
  `UserProfile`; permission classes `HasActiveBusiness` (tenant attach),
  `OwnerOnly`, `PaymentsPermission`, `SuppliersPermission` gate module-level
  access.
- Verified by `api/tests_security.py` (29 tests): employee cannot see purchase
  prices, denied expenses/supplier/profit reports/business settings/IDOR
  attempts, cross-tenant 403/404.
- **Secrets:** `SECRET_KEY`, `DJANGO_STAFF_PASSWORD` etc. come from
  environment, never hard-coded. The default dev keys remain in
  `config/settings.py` only as local fallbacks (production values are set in
  the Render dashboard); they are **not** production keys. No `.env` with
  production values is committed.

## 2. Tenant isolation

- Every business model extends `TenantModel` (FK `business`), and every
  serializer/list view/queryset filters on `request.business`.
- Cross-shop reads/sells rejected — regression-tested in Phases 11 and 13
  (device from another shop, purchase history isolation, IMEI history 404).
- IDs are never trusted to imply ownership: objects are re-fetched with
  `business=business` before mutation.

## 3. Financial integrity

- All money columns are `DecimalField(max_digits=12, decimal_places=2)`;
  `Decimal` arithmetic end-to-end; `float()` appears only at the JSON
  serialization boundary (audited pos/payments/dashboard/reports/serializers).
- **Client math is never trusted:** checkout recomputes subtotal, discount,
  tax, total, paid and due on the server; a padded `paid_amount` is clamped
  to the bill.
- **Stock-once rule (fixed this cycle):** an IMEI unit already sold cannot be
  billed again; devices of another product/shop/nonexistent are rejected
  before any row is written.
- Rejected checkouts leave **zero** rows (atomic validation before write).
- Overpayments are rejected so money cannot disappear inside a floor-at-zero
  sum; payments never mutate the original bill's audit row.
- `api/tests_phase13.py` (13 tests) covers all of the above.

## 4. Input validation & injection

- DRF serializer validation on all create/update endpoints; raw JSON inputs at
  POS validated explicitly (quantity ≥ 1, non-negative price/discount, line
  discount ≤ line total, valid decimals).
- SQL: 100% ORM/parametrized; no raw SQL with interpolation.
- XSS/injection into PDFs: invoice data rendered via the PDF service, not
  string-templated HTML.
- No `DEBUG=True` in production (`DEBUG` from env, Render sets `False`).
- `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` are environment-configured.

## 5. Transport & storage

- API is HTTPS-only in production (Render terminates TLS; `https`
  default API URL; the app rejects plain-`http` base URLs via the
  network-security config).
- Android network security config restricts cleartext traffic.
- Tokens/tokens stored in Flutter secure storage (Keystore/Keychain), not
  shared preferences.
- Backups export plain JSON — the owner must treat the export file as
  confidential (it contains customer phone numbers and invoices).

## 6. Ads & privacy

- AdMob SDK initializes only after UMP consent permits; no PII is sent to
  AdMob; banners only on the four allowed screens (never on invoices or
  payment confirmations).
- Live ad IDs are not (yet) configured — test IDs only, so no user is yet
  tracked by ad impressions beyond the SDK's own traffic
  (`docs/PRIVACY_AND_ADS.md`).

## 7. Open items (operational)

| Item | Risk | Action |
|---|---|---|
| Render deploy of current code is pending | service runs stale build, new endpoints 404 | Owner: manual deploy |
| Live AdMob account unapproved | no revenue, no policy risk yet | `docs/ADMOB_SETUP.md` |
| Release APK is debug-signed | cannot be listed on Play Store | fine for side-loading; create a release keystore before Play submission |
| Production PostgreSQL backup retention | depends on Render plan | verify on dashboard; encourage weekly in-app exports |
| 4 legacy tests fail against removed pre-API endpoints | none functionally (covered by current suites); kept per rules | documented in `docs/END_TO_END_ACCEPTANCE.md` |

## 8. What was deliberately NOT done

- No production data used for any test (all test data is synthetic; the demo
  shop is seeded data, only used for smoke checks).
- No destructive test against the live server (backup restore, DB resets).
- No penetration testing with external tooling was performed — this is a code
  and configuration review, not a third-party audit.
