# ShopZen — Android Build Guide

Everything needed to build the ShopZen APK/AAB from a clean machine.

## Prerequisites (one-time)

| Tool | Version used | Check with |
|---|---|---|
| Flutter SDK | 3.47.2 (stable) | `flutter --version` |
| Java JDK | 17 | `java -version` |
| Android SDK | platforms 34/35/36, build-tools, cmake 3.22.1 | `flutter doctor` |
| Python | 3.12+ (backend only) | `python --version` |

`flutter doctor` must show no Android toolchain errors before building.

## Project layout

```
mobile_app/            Flutter app (ShopZen Android client)
  lib/                 Dart source
  android/             Gradle wrapper — no Android Studio required
release/               Build outputs are copied here (see below)
```

## 1. Get dependencies

```bash
cd mobile_app
flutter pub get
```

Dependencies are pinned in `pubspec.yaml` + `pubspec.lock` — a fresh machine
reproduces the exact same package set.

## 2. Static analysis + unit tests (before every build)

```bash
flutter analyze     # must report 0 errors
flutter test        # must print "All tests passed!"
```

## 3. API base URL

The app reads `API_BASE_URL` at build time; the **default baked into the
release build is the production Render URL**:

```dart
// lib/core/constants/api_constants.dart
static const String baseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'https://dukaanflow.onrender.com',
);
```

| Build | Command |
|---|---|
| Production (default) | `flutter build apk --release` |
| Point at your PC for device testing | `flutter build apk --release --dart-define=API_BASE_URL=http://127.0.0.1:8000` (phone must reach it via `adb reverse tcp:8000 tcp:8000`) |
| LAN device test | `--dart-define=API_BASE_URL=http://<your-LAN-IP>:8000` |

Never use `localhost`/`127.0.0.1` without adb reverse — on a real phone that
address refers to the phone itself.

## 4. Build outputs

```bash
# Release APK (for shop owners — direct install)
flutter build apk --release
# → build/app/outputs/flutter-apk/app-release.apk

# Debug APK (for testing)
flutter build apk --debug
# → build/app/outputs/flutter-apk/app-debug.apk

# Android App Bundle (for Google Play upload)
flutter build appbundle --release
# → build/app/outputs/bundle/release/app-release.aab
```

Copy the deliverables into the repo's `release/` folder:

```bash
cp build/app/outputs/flutter-apk/app-release.apk  ../release/app-release.apk
cp build/app/outputs/flutter-apk/app-debug.apk    ../release/app-debug.apk
cp build/app/outputs/bundle/release/app-release.aab ../release/app-release.aab
```

## 5. Install on a connected phone

```bash
adb devices                       # phone must be listed
adb install -r release/app-release.apk
```

The APK is universal (arm/arm64/x86/x64) — the AAB is what Play Store
requires, and Play generates per-device APKs from it automatically.

## 6. App identity

| Item | Value |
|---|---|
| Application ID | `com.dukaanflow.app` |
| App name | ShopZen |
| Version | 1.0.0+1 (pubspec `version:`) |
| Splash | ShopZen — Smart Shop Management — Developed by PARAS KAMBLE |

Bump `version:` (e.g. `1.0.1+2`) for every release so Android accepts it as
an update.

## 7. Release signing (Play Store upload)

The debug keystore is only for local testing. For the Play Store:

```bash
keytool -genkey -v -keystore shopzen-release.jks \
  -keyalg RSA -keysize 2048 -validity 10000 -alias shopzen
```

Create `mobile_app/android/key.properties` (git-ignored — never commit):

```properties
storeFile=../../shopzen-release.jks
storePassword=<your store password>
keyAlias=shopzen
keyPassword=<your key password>
```

Then wire it into `android/app/build.gradle` (`signingConfigs.release`) and
build the AAB. **Back up the .jks + passwords somewhere safe** — losing it
means you can never update the app under the same Play listing.
