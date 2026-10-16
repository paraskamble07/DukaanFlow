# ShopZen — Test Report (Final)

**Build under test:** main through Phases 13–15 (`290e325` + the Phase 16
build fix), 2026-10-16
**Environment:** Windows host, Python 3.13 / Django 6.1.1 / DRF 3.18.0,
Flutter 3.47.2 / Dart 3.13.2
**Test data:** synthetic, per-test in-memory SQLite. **Production data was
never used for any test.**

---

## 1. Django system check + migration state

```
python manage.py check
→ System check identified no issues. (0 silenced)

python manage.py makemigrations --check --dry-run
→ No changes detected
```

Model state and migrations match exactly.

## 2. Backend suites (all apps)

| Suite | Tests | Result |
|---|---|---|
| `api.tests` | 15 | OK |
| `api.tests_security` | 29 | OK |
| `api.tests_backup` | 14 | OK |
| `api.tests_ledger_pdf` | 12 | OK |
| `api.tests_upi` | 15 | OK |
| `api.tests_phase11` | 18 | OK |
| `api.tests_phase13` (financial integrity) | 13 | OK |
| `api` total | **116** | **OK** |
| `updates.tests` | 13 | OK |
| `reminders.tests` + `subscriptions.tests` | 21 | OK |
| **All apps total** | **151/155** | **4 pre-existing legacy failures (below)** |

### What the Phase 13 integrity suite proves (`api/tests_phase13.py`)

- An IMEI unit **cannot be sold twice**; the device's original customer, sale
  and warranty survive a second attempt. Devices from another product or
  another shop are rejected before any write.
- A rejected checkout leaves **zero rows**: no sale, no line, no stock
  movement, no payment; stock untouched.
- Bill totals are **server-computed with Decimal precision** to the paisa
  (`149.99 × 3 − 0.49 = 449.48`; total `457.53`), and a client-padded
  `paid_amount` is clamped to the bill total.
- Negative prices/discounts, discount exceeding the line total, and
  quantity < 1 are rejected.
- Khata balances are derived from sale/payment **history**: overpayments are
  rejected (no money swallowed by a floor-at-zero), and recording a payment
  closes the due **without mutating the original bill's audit row**.
- Money columns stay exact through serialization (DRF sends `'449.97'`, not
  a rounded float).

### Known pre-existing failures — legacy `tests/` (4, not regressions)

`tests/test_auth_and_business.py` (2), `tests/test_reports_and_profit.py` (1),
`tests/test_sales_and_pos.py` (1) target the removed pre-API URL surface
(e.g. `/sales/api/checkout/` with session auth) and the removed subscription
plan cap (`limit == 50` vs the free-app limit). **Verified identical on the
pre-Phase-13 tree** (`git stash` → same 4 failures). Per project rules they
are not deleted, not weakened, and not faked green; the same behaviors are
covered strictly by the current API suites above.

## 3. Flutter (mobile_app)

```
flutter analyze → 0 errors, 0 warnings (34 pre-existing prefer-const /
                  deprecation infos)
flutter test    → 36/36 passed
```

| Area | Tests | Notes |
|---|---|---|
| Model/contract tests | 27 | product/customer/sale/cart math, Phase 11 models, backup/restore |
| Sync/offline (`sync_status_banner`) | 7 | offline + queued bills, syncing, clean state, transitions |
| Ads (`phase12_ads_test`) | 9 | config defaults, test-vs-live unit id, UMP consent gating, SDK gate matrix, AdBanner collapses to zero size on a non-ad platform |

Localization: **598 keys per locale (en/hi/mr), exact parity**, enforced by
the parity test.

## 4. Integration/smoke evidence

- Local dev server + live production smoke (dashboard, products, IMEI
  history, purchase history, `?stock=dead`) logged in
  `docs/IMPLEMENTATION_STATUS.md` per phase — every value reported is what
  the server actually returned (e.g. `last_sale_date: None` for an unsold
  product; 0 purchases for a product without POs; nothing faked).
- Production API health endpoint: 200, **stale build** (newer endpoints 404)
  — see `docs/DEPLOYMENT_GUIDE.md`; no deploy success is claimed.

## 5. Not performed (truthful list)

| Item | Reason |
|---|---|
| Release APK install + device acceptance steps | No physical device in this cycle; see `docs/END_TO_END_ACCEPTANCE.md` |
| Live AdMob impressions | Owner's AdMob account/units not ready; build serves test creatives |
| Render deploy of current code | Requires owner action (manual deploy) |
| Render PostgreSQL snapshot restore | Forbidden: would destroy/replace live data |

## 6. Upgrade-check evidence for this release

- `git log --oneline` for the commit list; each phase checkpoint in
  `docs/IMPLEMENTATION_STATUS.md` records its own verification numbers.
