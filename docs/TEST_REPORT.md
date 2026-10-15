# ShopZen — Test Report

**Date:** 2026-10-15
**Environment:** local test DB (SQLite, isolated), Python 3.13, Django 6.1.1,
DRF 3.18.0, Flutter 3.47.2 / Dart 3.13.2

---

## 1. Django system check

```
python manage.py check
→ System check identified no issues.
```

## 2. Backend test suite

```
python manage.py test api
→ Ran 44 tests in ~350s … OK
```

### `api.tests` — 15 tests (existing integration suite)

Register, login, profile, products, IMEI lookup, POS checkout, khata
settlement, purchase, expense, reports, subscription approval flow.
All 15 pass.

### `api/tests_security.py` — 29 NEW tests

#### EmployeePermissionTest (11)
- `test_employee_cannot_see_purchase_price` — list endpoint returns `null`
- `test_employee_cannot_see_purchase_price_in_detail`
- `test_owner_can_see_purchase_price`
- `test_employee_denied_expenses` → 403
- `test_employee_denied_expense_reports` → 403
- `test_employee_denied_supplier_module` → 403
- `test_employee_denied_supplier_payments` → 403/400
- `test_employee_denied_business_settings` → 403
- `test_employee_denied_profit_and_loss_report` → 403
- `test_employee_with_grant_can_access_granted_module` → 200 (no lockout)
- `test_employee_without_grant_denied_customer_module` → 403
- `test_employee_cannot_change_own_permissions`

#### TenantIsolationTest (10) — two shops
- Shop B cannot read / list / modify / delete Shop A's products
- Shop B cannot read / edit / delete / view ledger of Shop A's customers
- Shop B cannot checkout a sale referencing Shop A's customer or product
- Shop B cannot view Shop A's supplier
- Shop B's reports contain none of Shop A's data (4 report endpoints)

#### PasswordResetFlowTest (7)
- Unregistered email does not reveal account existence
- Token issued for registered email
- Valid token resets password
- Token is single-use (second attempt → 400)
- Expired token rejected (400)
- Short password rejected (400)
- Old password fails after reset (401)

#### KhataLedgerScenarioTest (1) — PRD §71 critical scenario
Purchase 10 → stock 10 → sell 2 → stock 8 → pay ₹4,000 → outstanding
₹16,000 → pay ₹16,000 → outstanding ₹0 → both payments still in ledger.

## 3. Flutter

```
flutter analyze  → 0 errors, 48 infos/warnings (improved from 92)
flutter test     → All 6 tests passed!
```

Tests: currency formatting, ProductModel JSON parsing, CustomerModel khata
fields, SaleModel parsing, PosState cart math, splash render.

## 4. Production

```
curl https://dukaanflow-1.onrender.com/api/health/
→ 200 {"status":"ok","app":"ShopZen","version":"1.0.0","database":"up"}
```

## 5. Not covered / known limits

- No physical Android device — barcode scan, biometric prompt, and
  in-app WhatsApp/SMS share intents are implemented but not verified on
  real hardware.
- Password-reset token is delivered over the API (no SMTP configured).
- No load/performance benchmarks run; performance work so far is
  structural (pagination, select_related, query counts).
