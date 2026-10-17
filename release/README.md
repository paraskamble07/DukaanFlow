# Release Artifacts

Built from commit: see `git log -1` (mobile_app/ source).

| File | Purpose | Size |
|---|---|---|
| `app-release.apk` | Install directly on any Android phone (production URL) | ~70 MB |
| `app-debug.apk` | Debug/testing build (arm/arm64) | ~142 MB |
| `app-release.aab` | Upload to Google Play Console | ~62 MB |

## Verified release — 2026-10-16 (commit with Phases 13–15)

- Built with `flutter build apk --release` in `mobile_app/`
- Gradle `assembleRelease` exit code **0**
- `app-release.apk`: **73.8 MB** (77,380,596 bytes)
- SHA-256: `ffc5e50c4358977b4d712e0ee0c2fd256eaca3919ae30ef4fc00b1f9ced01e76`
  (verified equal for the build output and the copy in this folder)
- Package id: `com.dukaanflow.app` — versionName `1.0.0`, versionCode `1`
  (aapt2 dump badging)
- Compiled-in API base URL: `https://dukaanflow-1.onrender.com`
  (string found in `lib/arm64-v8a/libapp.so`)
- Banner ad unit in this build: Google **test** unit
  `ca-app-pub-3940256099942544/6300978111` (no live ads until the owner's
  AdMob activation — `docs/ADMOB_SETUP.md`)
- Device install/acceptance: **NOT PERFORMED** (no physical device in this
  cycle — see `docs/END_TO_END_ACCEPTANCE.md`)

These binaries are intentionally NOT tracked in git (GitHub blocks >100 MB
files; repos shouldn't host builds). Rebuild locally with:

    cd mobile_app
    flutter build apk --release && flutter build appbundle --release
    cp build/app/outputs/flutter-apk/app-release.apk  ../release/
    cp build/app/outputs/flutter-apk/app-debug.apk    ../release/
    cp build/app/outputs/bundle/release/app-release.aab ../release/

See docs/ANDROID_BUILD.md for the full guide.

## Verified release — 2026-10-17 (Phase 25: owner-priority defect pass)

- Built with `flutter build apk --release` in `mobile_app/` (Gradle
  `assembleRelease` exit code **0**)
- `app-release.apk`: **74.0 MB** (77,626,744 bytes)
- SHA-256: `df82df2dabe7d873c6eeff810582e24fbd7d9bc516c9c5b756250c5e03ed2414`
  (verified equal for the build output and the copy in this folder)
- Package id: `com.dukaanflow.app` — versionName `1.1.2`, versionCode `4`
  — bumped from 1.1.1+3 because this build carries real fixes
- Signing: V2, **Android Debug** cert, SHA-256 digest
  `7f6cdf58759faa9b845b879a232d92105315da6dc2dfdd08454f93779108916b` —
  identical to every prior ShopZen release, so it installs as an in-place
  update
- Fixes compiled into this build (byte-verified in the APK):
  - the literal `$id` URL defect that 404'd Product Detail and IMEI Device
    History is **gone** (zero `$id` fragments remain in any `libapp.so`);
  - the live AdMob banner unit `ca-app-pub-8559634762194466/2011019340`
    is present in all three arches and the real App ID
    `ca-app-pub-8559634762194466~5030925195` is in the manifest;
  - the production API base URL
    `https://dukaanflow-1.onrender.com` is compiled in
- Full verification: `flutter analyze` 0 errors / 0 warnings (34
  pre-existing infos); `flutter test` **41/41 passed**; Django **213/213
  passed** (`check` + `makemigrations --check` clean)
- `static/apk/shopzen-1.0.0.apk` (production URL target) deliberately
  **untouched** — SHA-256 still `ffc5e50c…e76`
- **Staff & Logins + Notifications still 404 on the live server** — the
  backend fix is prepared but NOT deployed (needs owner approval; see
  `docs/DEPLOYMENT_PREP.md`). The app now explains this on-screen instead
  of showing a raw error.
- Device install/acceptance: **NOT PERFORMED** (no physical Android device,
  emulator or adb in this environment — only web targets available).
  Live ad impressions unverified for the same reason.

## Verified release — 2026-10-17 (Phase 24: live AdMob IDs)

- Built with `flutter build apk --release` in `mobile_app/` (Gradle
  `assembleRelease` exit code **0**)
- `app-release.apk`: **74.0 MB** (77,626,740 bytes)
- SHA-256: `436cf06e12831b01878e47241f79bf37bdc70643c60778e7d5c5a012f380d9d8`
  (verified equal for the build output and the copy in this folder)
- Package id: `com.dukaanflow.app` — versionName `1.1.1`, versionCode `3`
  (aapt2 dump badging) — bumped from 1.1.0+2 so this build is
  distinguishable from the previous one
- Signing: V2, **Android Debug** cert, SHA-256 digest
  `7f6cdf58759faa9b845b879a232d92105315da6dc2dfdd08454f93779108916b` —
  identical to the 1.0.0+1 and 1.1.0+2 releases, so it installs as an
  in-place update
- Compiled-in API base URL: `https://dukaanflow-1.onrender.com` (byte-present
  in the APK)
- AdMob in this build: real ShopZen App ID
  `ca-app-pub-8559634762194466~5030925195` in the packaged
  `AndroidManifest.xml`, and the live banner unit
  `ca-app-pub-8559634762194466/2011019340` (ShopZen_Banner_Home)
  byte-present in every `libapp.so` arch. The Google **test** unit is
  tree-shaken out of release builds (debug/test builds use the test unit
  automatically via `kReleaseMode`). Live impressions still **unverified**
  — no device in this environment (`docs/ADMOB_SETUP.md`)
- `static/apk/shopzen-1.0.0.apk` (production URL target) deliberately
  **untouched** — SHA-256 still `ffc5e50c…e76`
- Device install/acceptance: **NOT PERFORMED** (no physical Android device,
  emulator or adb in this environment — only web targets available)

## Verified release — 2026-10-17 (Phase 22 fixes + Phase 23 UI audit)

- Built with `flutter build apk --release` in `mobile_app/` (Gradle
  `assembleRelease` exit code **0**)
- `app-release.apk`: **74.0 MB** (77,626,732 bytes)
- SHA-256: `3f3d764cc74847df98fb872656997816ee4d189dc1122e03ae31524642a8e307`
  (verified equal for the build output and the copy in this folder)
- Package id: `com.dukaanflow.app` — versionName `1.1.0`, versionCode `2`
  (aapt2 dump badging) — bumped from 1.0.0+1 so the fixed build is
  distinguishable from the shipped one
- Signing: V2, **Android Debug** cert, SHA-256 digest
  `7f6cdf58759faa9b845b879a232d92105315da6dc2dfdd08454f93779108916b` —
  identical to the 1.0.0+1 release, so it installs as an in-place update
  (debug signing is the documented choice; see build.gradle)
- Compiled-in API base URL: `https://dukaanflow-1.onrender.com` (byte-present
  in the APK); banner ad unit still the Google **test** unit
- `static/apk/shopzen-1.0.0.apk` (production URL target) deliberately
  **untouched** — SHA-256 still `ffc5e50c…e76`
- Device install/acceptance: **NOT PERFORMED** (no physical Android device,
  emulator or adb in this environment — only web targets available)
