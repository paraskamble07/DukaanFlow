# ShopZen — Release Guide (Android APK)

Everything needed to produce and verify a ShopZen release. Target distribution
channel: **side-loaded release APK** (Play Store submission is not part of
this release).

Last updated: 2026-10-16.

---

## 1. Pre-release checklist

- [ ] Backend green: `python manage.py check`,
      `python manage.py makemigrations --check --dry-run` (must say
      "No changes detected"),
      backend tests across all apps (see `docs/TEST_REPORT.md` for the
      current numbers).
- [ ] Flutter green: `flutter analyze` (0 errors / 0 warnings),
      `flutter test`.
- [ ] `version: X.Y.Z+N` in `mobile_app/pubspec.yaml` bumped vs. the previous
      release (Z is the display version, N the integer `versionCode`).
- [ ] `ApiConstants.baseUrl` points at production
      (`https://dukaanflow-1.onrender.com`) — it does by default; it can be
      overridden at build time with `--dart-define=API_BASE_URL=...`.
- [ ] AdMob: build with the live unit id if monetization is activated
      (`--dart-define=ADMOB_BANNER_UNIT_ID=...`) — see
      `docs/ADMOB_SETUP.md`. Without it the build serves test ads.
- [ ] The server has been deployed (or the owner has scheduled it) so the app
      and API versions match.

## 2. Build the release APK

```bash
cd mobile_app
flutter clean
flutter build apk --release
```

(Optional with live ads:
`--dart-define=ADMOB_BANNER_UNIT_ID=ca-app-pub-...`.)

Signing: the current release build is signed with the **debug** keystore
(`signingConfig signingConfigs.debug` in
`android/app/build.gradle`). That is intentional for side-load distribution
and preserves the release-signing identity across builds — the same signature
lets users upgrade over the installed app. For a Play Store submission,
create a dedicated keystore + `android/key.properties` and reference it in
the release block (see `docs/ANDROID_BUILD.md`).

## 3. Verify the artifact

Record each of these before shipping (the acceptance checklist in
`docs/END_TO_END_ACCEPTANCE.md` is built on them):

```bash
APK=mobile_app/build/app/outputs/flutter-apk/app-release.apk

# 1. Exit code of the build (must be 0)
echo $?   # immediately after flutter build

# 2. Size
ls -l "$APK"

# 3. SHA-256
sha256sum "$APK"

# 4. Package id + version
unzip -p "$APK" AndroidManifest.xml > /tmp/m.xml            # binary xml
# readable form via aapt2 (Android SDK build-tools):
aapt2 dump packagename "$APK"; aapt2 dump versionname "$APK"
# (or) via gradle: ./gradlew :app:printVersionInfo  if configured
```

Expected values for this app:

| Property | Expected |
|---|---|
| Package id | `com.dukaanflow.app` |
| versionName | matches `pubspec.yaml` (e.g. `1.0.0`) |
| versionCode | matches the `+N` part (e.g. `1`) |
| API base URL | `https://dukaanflow-1.onrender.com` |
| ABI | fat APK (`arm64-v8a, armeabi-v7a, x86_64`) |
| Ad unit | Google test unit unless `--dart-define` overrides |

Then run the smoke tests on the artifact: install it (see 4), log in as the
demo shop, create a bill, and confirm the numbers to the paisa.

## 4. Publish

1. Copy the verified APK into place:

   ```bash
   cp mobile_app/build/app/outputs/flutter-apk/app-release.apk release/app-release.apk
   cp mobile_app/build/app/outputs/flutter-apk/app-debug.apk   release/app-debug.apk
   cp mobile_app/build/app/outputs/bundle/release/app-release.aab release/app-release.aab
   ```

   (`release/` is git-ignored — binaries are not committed.)
2. Host `app-release.apk` at a public URL and register the
   `Update` record so existing installs get the update card
   (`docs/APP_UPDATE_GUIDE.md`).
3. Users install/upgrade by opening the APK ("Install from unknown source"
   required once).

## 5. Rollback / emergency

- Keep the previous APK + its SHA-256. Users reinstall it over the current
  one (same signature allows downgrade in side-loading).
- Server keeps data; an app rollback never loses shop data.
- If a release is bad, set its `is_active = false` in the Django admin so no
  further users get the update card.
