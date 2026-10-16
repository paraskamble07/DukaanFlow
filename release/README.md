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
