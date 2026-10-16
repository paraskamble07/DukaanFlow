# ShopZen — Final Report

**Project:** ShopZen / DukaanFlow — free shop management app
**Release target:** Android APK, package `com.dukaanflow.app`, version 1.0.0
(code 1)
**Report date:** 2026-10-16
**Final commit of this cycle:** see `git log -1` after the Phase 17–18 push

This report is factual: every claim below either has evidence in the repo or
is explicitly listed as not performed, with the exact blocker.

---

## 1. What was delivered

The 18-phase master plan is complete for everything that does not depend on
an external account, approval or physical device:

| Phases | Content | Commit |
|---|---|---|
| 1–8 | Audit, subscription paywall removal (free app), hardening, settings, reminders, ledger PDF, UPI QR, hi/mr localization, backup/restore | earlier commits |
| 9 | Offline mode + sync status banner; offline dashboard keeps last snapshot | `d82c89b` |
| 11 | IMEI device history, server-derived warranty, dead-stock rule, per-product purchase history | `54f1f97` |
| 12 | AdMob banner SDK + Google UMP consent; banners only on 4 screens | `25415b1` (+ build fix) |
| 13–15 | Financial-integrity hardening + regression suite + 21-step acceptance doc | `290e325` |
| 16 | Release APK rebuilt and fully verified | this push |
| 17–18 | AdMob, privacy, security, test, release, update, backup docs + this report | this push |

## 2. Test results (exact numbers)

**Backend** (all apps, in-memory sqlite, synthetic data only):

```
python manage.py check                    → 0 issues
python manage.py makemigrations --check   → "No changes detected"
python manage.py test api updates reminders subscriptions
→ api 116/116 OK, updates 13/13, reminders+subscriptions 21/21,
  legacy tests/ 1/5 → 151/155 total
```

The 4 failing legacy tests are **pre-existing**, verified identical on the
pre-Phase-13 tree: they call the removed pre-API endpoints and assert the
removed subscription plan cap. They were not deleted, weakened or faked —
full list in `docs/TEST_REPORT.md`.

**Flutter:**

```
flutter test    → 36/36 passed
flutter analyze → 0 errors, 0 warnings (34 pre-existing style infos)
Localization   → 598 keys × 3 locales, exact parity (en/hi/mr)
```

**Release APK (Phase 16, verified):**

| Property | Value |
|---|---|
| Build exit code | 0 |
| Artifact | `release/app-release.apk` |
| Size | 73.8 MB (77,380,596 bytes) |
| SHA-256 | `ffc5e50c4358977b4d712e0ee0c2fd256eaca3919ae30ef4fc00b1f9ced01e76` (equal for build output and the release copy) |
| Package id | `com.dukaanflow.app` |
| versionName / versionCode | `1.0.0` / `1` |
| API base URL (in the binary) | `https://dukaanflow-1.onrender.com` |
| Ad unit in build | Google **test** unit (no live ads) |
| ABIs | arm64-v8a, armeabi-v7a, x86_64 |
| Signing | debug keystore (side-load channel; same signature allows upgrades) |

**Not performed:** installing the APK on a physical phone and running the
device acceptance steps (no device in this cycle). Device testing was
therefore **not** performed and is not claimed — see
`docs/END_TO_END_ACCEPTANCE.md` for the 21-step scenario to run on the first
available device.

## 3. Real bugs fixed in this cycle

1. **Double-sell of IMEI units (Phases 13–15).** Checkout never checked a
   device's status, so a sold unit could be billed again, overwriting its
   customer, sale record and warranty. Now validated before any write; 13
   regression tests cover it.
2. **Negative/absurd POS lines.** Quantity < 1, negative price or discount,
   and line discount above the line total are now rejected (previously a
   negative line could be silently clamped into a zero-value bill).
3. **AdMob release build incompatibilities (Phase 16).** The UMP plugin
   `user_messaging_platform` has no AGP-8 namespace (replaced with the UMP API
   inside `google_mobile_ads`) and plugin modules needed compileSdk 36 (AGP
   subprojects workaround in `android/build.gradle`). Both were invisible to
   `flutter analyze`/`flutter test` and only surfaced on a real release build
   — so the release build is now part of the release checklist.
4. **Phase 9 (earlier):** offline checkout left the cart populated with an
   invisible error string; now the cart clears and shows a localized
   confirmation.

## 4. Remaining blockers (exactly what, and who unblocks each)

| # | Blocker | Blocks | Owner action |
|---|---|---|---|
| 1 | **Render deploy of current code is pending.** Production health is 200 but new endpoints (e.g. `/api/updates/check/`, `/api/inventory/imei/<id>/history/`) return 404 — the service still runs the old build. | Production use of Phases 9–15 + device acceptance against production | Render dashboard: **Manual Deploy** (or re-enable auto-deploy). Steps in `docs/DEPLOYMENT_GUIDE.md`; `build.sh` migrates automatically. |
| 2 | **AdMob account approval + real ad unit ids.** The build serves Google test creatives and earns nothing. | Live monetization, live ad impressions | `docs/ADMOB_SETUP.md` — verify account, register the app, create the banner unit, rebuild with `--dart-define=ADMOB_BANNER_UNIT_ID=...`, set the live App ID in the manifest. |
| 3 | **No physical Android device.** | Device install test, steps 15–21 of the acceptance scenario | Install `release/app-release.apk` (SHA-256 above) on a phone and run `docs/END_TO_END_ACCEPTANCE.md` sections A–G. |
| 4 | **Play Store submission.** | Store distribution | The APK is debug-signed for side-loading; create a release keystore per `docs/ANDROID_BUILD.md` and submit an AAB. Not part of this release channel. |

No task in the plan was skipped for any other reason; nothing was faked, and
no working feature, user change, migration, or the signing identity was
modified or rolled back.

## 5. Production database

PostgreSQL by configuration (`render.yaml` wires `DATABASE_URL` to the managed
`dukaanflow-db`; `build.sh` runs migrations on deploy). SQLite is only the
local default. Row-level verification against the live instance re-checks
after the owner's deploy (Step 1).

## 6. Documentation set

Implementation plan/status: `IMPLEMENTATION_PLAN.md`,
`IMPLEMENTATION_STATUS.md` (per-phase checkpoints with numbers).
Acceptance & testing: `END_TO_END_ACCEPTANCE.md`, `TEST_REPORT.md`,
`TESTING.md`. Security: `SECURITY.md`, `SECURITY_AUDIT.md`. Release &
operations: `RELEASE_GUIDE.md`, `ANDROID_BUILD.md`, `DEPLOYMENT_GUIDE.md`,
`DEPLOYMENT.md`, `PRODUCTION_SETUP.md`, `PRODUCTION_DEPLOYMENT.md`,
`APP_UPDATE_GUIDE.md`, `BACKUP_AND_RECOVERY.md`, `INSTALLATION_GUIDE.md`.
Monetization & privacy: `ADMOB_SETUP.md`, `PRIVACY_AND_ADS.md`,
`PAYMENT_SETUP.md`, `PAYMENT_SUBSCRIPTION_GUIDE.md` (historical; the app is
now free), `ADMIN_GUIDE.md`, `USER_GUIDE.md`, `API_DOCUMENTATION.md`,
`README.md`.
