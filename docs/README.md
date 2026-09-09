# ShopZen (DukaanFlow Mobile) — Project Overview

> **ShopZen — "Sell. Stock. Khata. Profit. Simplified."**
> Android app (Flutter) + REST API (Django REST Framework) built **on top of the existing DukaanFlow production system** — same backend, same PostgreSQL database, same business logic. The existing website is untouched and keeps working.

```
ShopZen App (Flutter) ──HTTPS/JWT──▶ Django REST API (/api/) ──▶ PostgreSQL
                                          ▲
DukaanFlow Website (Django templates) ────┘  (same business logic & data)
```

## Repository layout

| Path | What it is |
|---|---|
| `config/`, `core/`, `accounts/`, `businesses/`, `customers/`, `products/`, `inventory/`, `suppliers/`, `purchases/`, `sales/`, `expenses/`, `payments/`, `invoices/`, `reports/`, `dashboard/`, `landing/` | Original DukaanFlow web app — **unmodified behaviour** |
| `api/` | ShopZen REST API layer (views, serializers, permissions, tests) |
| `mobile_app/` | ShopZen Flutter application (lib/, android/, test/) |
| `docs/` | API docs, security, installation, deployment, user guide |
| `step_*.py` | Build scaffolding scripts from earlier development phases |

## Feature checklist (all wired to real backend data — no mocks)

- **Auth**: register + login + auto-login, JWT with refresh & rotation, secure token storage
- **Dashboard**: today's sales/profit/expenses, khata due, supplier payable, 7-day chart, low-stock alerts, pending khata with 1-tap WhatsApp
- **POS**: cart, search, IMEI scan attach, discount, GST, split/partial payment, Khata (udhar) sales, **atomic checkout** (server transaction), invoice number, WhatsApp share
- **Stock**: products CRUD, stock movement ledger, low-stock thresholds, stock adjustment with reason, barcode/IMEI camera scanning (mobile_scanner)
- **IMEI**: dual-IMEI + serial registration, duplicate prevention, lifecycle lookup (purchase → sale → customer → warranty)
- **Customers & Khata**: ledger, receive payment (auto khata update), WhatsApp reminders, statements
- **Suppliers & Purchases**: supplier CRUD, purchase entry (stock auto-increase), supplier payments & payables
- **Expenses**: 8 pre-seeded categories, list + entry, category breakdown
- **Reports (server-calculated, Decimal)**: P&L, Sales, Stock + dead stock, Khata, Expenses, GST, Top Products, Top Customers
- **Subscription**: one plan — **ShopZen Premium ₹30/month**, paid to the owner's UPI QR, **manually verified by the ShopZen Admin** (submit UTR → PENDING → admin approves → active). Duplicate/replay-proof, fully audited
- **ShopZen Admin (in-app)**: for the authorized admin account only — totals (users/shops/active/expired), pending/approved/rejected payments, revenue, recent registrations, one-tap APPROVE/REJECT with atomic server guarantees
- **Offline**: POS queue with auto-sync, safe 201-only dequeue
- **i18n**: English / हिंदी / मराठी; Light/Dark/System themes; Material 3

## Multi-tenant security

Tenant is derived from the JWT on the server — `shop_id` from the client is ignored. Cross-shop ID → 404. Proven by `api/tests.py::TenantIsolationTest` (9 tests, part of the 14-test suite, all passing).

## Quick start

```bash
# Backend
./venv/Scripts/python.exe manage.py runserver 0.0.0.0:8000
./venv/Scripts/python.exe manage.py test api subscriptions   # 23 tests OK

# Mobile (see docs/INSTALLATION_GUIDE.md)
cd mobile_app
flutter pub get
flutter devices                                     # your Android phone
flutter run                                         # live on device
flutter build apk --release                        # → build/app/outputs/flutter-apk/app-release.apk
```

The release APK defaults to the **production URL** `https://dukaanflow.onrender.com` (override only for local debugging: `--dart-define=API_BASE_URL=http://127.0.0.1:8000` with `adb reverse tcp:8000 tcp:8000`).

## Documentation index

- [API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md) — every endpoint with payloads
- [INSTALLATION_GUIDE.md](docs/INSTALLATION_GUIDE.md) — phone setup, USB debugging, APK build/install
- [DEPLOYMENT.md](docs/DEPLOYMENT.md) — deployment entry point (checklist + links to the full guides)
- [PRODUCTION_SETUP.md](docs/PRODUCTION_SETUP.md) — from repo to permanently-running production (Render + admin + ₹30 setup)
- [PRODUCTION_DEPLOYMENT.md](docs/PRODUCTION_DEPLOYMENT.md) — Render deploy (blueprint + manual deploy + troubleshooting)
- [ANDROID_BUILD.md](docs/ANDROID_BUILD.md) — building debug/release APK + Play Store AAB, keystore signing
- [SECURITY.md](docs/SECURITY.md) — tenant isolation, financial integrity, payment security
- [USER_GUIDE.md](docs/USER_GUIDE.md) — end-user manual (English)
- [PAYMENT_SETUP.md](docs/PAYMENT_SETUP.md) — configuring YOUR ₹30 UPI/QR + verifying payments
- [PAYMENT_SUBSCRIPTION_GUIDE.md](docs/PAYMENT_SUBSCRIPTION_GUIDE.md) — the ₹30 flow: owner pays, admin verifies
- [ADMIN_GUIDE.md](docs/ADMIN_GUIDE.md) — creating and using YOUR admin account
- [TESTING.md](docs/TESTING.md) — automated suites + manual phone checklist
