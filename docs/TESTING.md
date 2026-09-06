# ShopZen Testing Guide

How to test the whole system — automated suites, API smoke tests and the manual phone checklist. Use this before every release.

---

## 1. Automated test suites (run before every release)

### Backend (Django)

```bash
cd DukaanFlow
./venv/Scripts/python.exe manage.py test api subscriptions      # Windows
# or: python manage.py test api subscriptions                   # Linux/Render shell

./venv/Scripts/python.exe manage.py check                        # config sanity
./venv/Scripts/python.exe manage.py makemigrations --check       # no missing migrations
./venv/Scripts/python.exe manage.py migrate                      # apply locally
```

**Expected:** `OK` — 23 tests (14 API incl. tenant isolation/POS atomicity + 9 subscription/payment: config auth, submit→PENDING no-activation, duplicate block, owner blocked from admin APIs 403, approve ₹60 → +60 days, double-approve 404, reject+resubmit, dashboard stats, UTR search).

### Flutter

```bash
cd mobile_app
C:/src/flutter/bin/flutter analyze        # 0 errors (infos/warnings are lint-level)
C:/src/flutter/bin/flutter test          # "All tests passed!" (6 tests)
```

### Release build

```bash
cd mobile_app
C:/src/flutter/bin/flutter clean
C:/src/flutter/bin/flutter pub get
C:/src/flutter/bin/flutter analyze
C:/src/flutter/bin/flutter test
C:/src/flutter/bin/flutter build apk --release
# → build/app/outputs/flutter-apk/app-release.apk
```

## 2. Live API smoke test (against production)

```bash
# Health (public)
curl https://dukaanflow.onrender.com/api/health/
# → {"status":"ok","app":"ShopZen","version":"1.0.0","database":"up",...}

# Login rejects bad credentials with a clean message
curl -X POST https://dukaanflow.onrender.com/api/auth/login/ \
  -H "Content-Type: application/json" -d '{"email":"x@x.com","password":"y"}'
# → 401 {"error":"Invalid credentials. Please verify your email and password."}
```

Then with a real token (`"Authorization: Bearer <access>"`): dashboard, products list, subscription status, payment config — each must return 200 with JSON (not HTML).

## 3. Manual phone checklist (run after every APK install)

| # | Test | Pass when |
|---|---|---|
| 1 | Install APK, open | Splash shows "ShopZen / Developed by PARAS KAMBLE" then Login |
| 2 | Register new shop | Lands on dashboard, business name shows |
| 3 | Login wrong password | "Incorrect email or password." style message, no crash |
| 4 | Backend unreachable (airplane mode) | "Unable to connect / check internet" message, no crash |
| 5 | Add product | Appears in stock list with correct price |
| 6 | POS cash sale | Invoice generated, stock decreases, sale in history |
| 7 | POS sale more than stock | Rejected with friendly message, no partial record |
| 8 | Khata sale + payment | Due = credit − payment, matches customer detail screen |
| 9 | Supplier + purchase | Stock increases by purchase qty, payable shows |
| 10 | Expenses | Listed, visible in P&L and expense report |
| 11 | Reports | Today's sales include today's bills (IST date), amounts match |
| 12 | WhatsApp share | Opens WhatsApp with the bill text |
| 13 | Premium screen | QR shows, UPI ID shows, UTR submit → "Payment Under Verification" |
| 14 | Premium NOT auto-active | After submit, hero still says EXPIRED until admin approves |
| 15 | Admin account login | "ShopZen Admin" tile visible in More |
| 16 | Admin approves payment | Owner app (or re-login) shows ACTIVE + expiry = today+30d |
| 17 | Double approve | Second admin review returns 404, nothing changes |
| 18 | Kill app → reopen | Still logged in, data intact |
| 19 | Logout → login | Works, tokens refresh |
| 20 | Laptop off, mobile data on | Everything above still works (cloud backend) |

## 4. Subscription flow — precise dates test

1. Note today's date. Submit a ₹30 payment (UTR anything).
2. Verify in DB (or via owner's app): still EXPIRED, one PENDING request.
3. Admin approves. Owner's status now ACTIVE, expiry = today + 30 days.
4. Approve ₹60 from another shop: expiry = today + 60 days.
5. Try approving the same request again → 404, expiry unchanged.
6. Reject flow: submit → reject with reason → owner sees reason, can resubmit → resubmit succeeds.

## 5. Tenant isolation quick test

Register shops A and B. From A's token: `GET /api/products/<B's product id>/` → **404**. Same for customers, sales, suppliers. This is IDOR protection: cross-shop ids are indistinguishable from non-existent ones.

## 6. Offline behaviour (current, honest)

The app requires the server for checkout; if the connection drops mid-checkout the sale is **not** created (atomic server transaction — no partial bills) and the user sees a clear error to retry. A persistent offline bill queue is **not** in this release; see the final report's limitations section.

## 7. Where results are recorded

- CI-less environment: paste the three command outputs (backend test, analyze, flutter test) into the release note, plus this checklist with ✅/❌ per row.
- Any ❌ row → fix, rebuild, re-run the whole checklist before sending the APK to a shop owner.
