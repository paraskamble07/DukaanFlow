# ShopZen startup crash — investigation log (2026-10-16)

Reported symptom: the published APK (`static/apk/shopzen-1.0.0.apk`, build
`1.0.0+1`) installs successfully on a TECNO BF7 (Android 12) but the app
closes immediately when the icon is tapped.

## Environment during investigation

- Flutter 3.47.2 / Dart 3.13.2, AGP 9.0.1, Gradle 9.1.0, Kotlin 2.2.20
- `adb` available (SDK platform-tools 37.0.1), **no device attached**
- **No Android emulator installed, no system images, no AVD** — the SDK only
  contains build-tools, platform-tools, NDK and platforms.
  `flutter emulators` / `emulator -list-avds` are therefore unavailable, so
  the crash could not be reproduced in this session.

## Verified by static forensics on the published APK (SHA-256
`ffc5e50c…ced01e76`, byte-identical to `release/app-release.apk`)

1. **Manifest is valid**: `com.dukaanflow.app`, `versionCode=1`,
   `minSdkVersion=24`, `targetSdkVersion=36`, `MainActivity` exported with
   MAIN/LAUNCHER. Nothing an Android 12 device would reject (it installs,
   confirming this).
2. **All manifest-referenced resources resolve** (`xml/network_security_config`,
   `style/LaunchTheme`, `mipmap/ic_launcher`, both `FileProvider` paths).
3. **Theme chain is intact** (`LaunchTheme` → `@drawable/launch_background`).
4. **APK signature verifies** (v1/v2/v3, debug keystore — the documented
   release signing configuration; same key as prior builds).
5. **Native libraries present for all three ABIs** (`arm64-v8a`,
   `armeabi-v7a`, `x86_64`), each containing `libapp.so` + `libflutter.so`.
   A TECNO BF7 runs arm64-v8a, which is included.
6. **Dex is complete, not stripped of needed classes**: the release build is
   R8-obfuscated (engine classes renamed, e.g. `MainActivity`'s superclass
   resolves to `a8/f`), but the class hierarchy is intact and no class
   referenced at runtime is missing. `GeneratedPluginRegistrant` and every
   manifest component resolve.
7. **`android:name="android.app.Application"` on `<application>` is stock**:
   Flutter 3.47's Gradle plugin deliberately sets the `applicationName`
   placeholder to `android.app.Application`
   (`flutter_tools/gradle/…/BaseApplicationNameHandler.kt`), so this is not a
   deviation and not the cause.
8. **Flutter assets** are present and structurally normal.
9. **The shipped APK is exactly the artifact built by
   `flutter build apk --release`** (identical SHA-256), so the website is not
   serving a stale or corrupted file.

Conclusion at that point: no structural defect had been found in the published
APK, and the remaining cause had to be runtime-only.

# ─────────────────────────────────────────────────────────────────────────
# UPDATE 2026-10-16 18:0x — DEVICE LOG COLLECTED, ROOT CAUSE CONFIRMED
# ─────────────────────────────────────────────────────────────────────────

`shopzen_crash_log.txt` (device log, UTF-16) contains two identical
`FATAL EXCEPTION` blocks (PIDs 1743 and 1830):

    java.lang.RuntimeException: Unable to get provider
    androidx.startup.InitializationProvider:
    com.google.android.gms.internal.ads.dd:
    java.lang.RuntimeException: Failed to create an instance of
    androidx.work.impl.WorkDatabase
        ... ActivityThread.installProvider / handleBindApplication
    Caused by: com.google.android.gms.internal.ads.dd:
    java.lang.RuntimeException: Failed to create an instance of
    androidx.work.impl.WorkDatabase
        at j2.a.b(...)                              # androidx.startup.AppInitializer
        at androidx.startup.InitializationProvider.onCreate
    Caused by: java.lang.RuntimeException: Failed to create an instance of
    androidx.work.impl.WorkDatabase
        at z2.k.<init> / z2.k.c                      # androidx.room.RoomDatabase$Builder
        at androidx.work.WorkManagerInitializer.b    # Initializer.create()
        at j2.a.b(...)

The crash happens **before Flutter runs** (during ContentProvider
installation in `handleBindApplication`), which is why no Dart-level handler
could ever catch it — and why the app closed instantly.

## Deepest cause (proven, not assumed)

`RoomDatabase.Builder` instantiates the generated
`androidx.work.impl.WorkDatabase_Impl` **reflectively**:
`Class.forName(name + "_Impl")` + `clazz.getDeclaredConstructor()`. Since the
constructor has no direct program-graph reference, **R8 (release build)
stripped it**. Parsing the published `classes.dex` proves it:

    OLD (crashed) APK — WorkDatabase_Impl:
      direct methods: []            ← NO <init> constructor at all
      instance fields: []
    NEW (fixed) APK — WorkDatabase_Impl:
      direct methods: [<init>]      ← restored by the keep rule
      instance fields + DAO methods retained

So the deepest exception is Room's
`RuntimeException("Failed to create an instance of
androidx.work.impl.WorkDatabase")` caused by the missing public no-arg
constructor (R8 shrink; the wrapping `NoSuchMethodException`/cause chain was
dropped by the device's Transsion exception reporter, but no other failure is
possible at that call site once the class is found — and the class name in the
message proves Room found it). AdMob appears in the trace only because its
`androidx.startup` initializer depends on WorkManager; it is a victim of the
same crash, not the cause.

## Fix

**`mobile_app/android/app/proguard-rules.pro` (new file).** Flutter's Gradle
plugin already adds `app/proguard-rules.pro` to the release build when
minification is enabled (`FlutterPlugin.kt`, confirmed in the Flutter 3.47
source), so no Gradle change was required. The rules keep the no-arg
constructor of every Room generated `*_Impl` (the general rule) plus
WorkManager's own database explicitly:

    -keep class * extends androidx.room.RoomDatabase { <init>(); }
    -keep class androidx.work.impl.WorkDatabase { <init>(); }
    -keep class androidx.work.impl.WorkDatabase_Impl { <init>(); }
    -keep class androidx.work.impl.WorkSqliteOpenHelper$Callback { <init>(); }

Nothing was removed from the `AndroidManifest.xml`, AdMob/consent/WorkManager
components were all left in place, no dependencies were upgraded or
downgraded, application ID / signing / UI / authentication untouched. The
`main.dart` bootstrap hardening from the first pass is retained as defense in
depth.

## Verification (real, on the device)

- `flutter pub get`, `flutter analyze` (0 errors, 0 warnings, 34 infos),
  `flutter test` — 36/36 pass.
- `flutter build apk --release` — success, existing signing config.
- Dex re-parsed: `WorkDatabase_Impl.<init>` now present.
- Phone `096433133G053759` connected and authorized:
  - `adb install -r` → Success (no data loss, same versionCode + signature).
  - `adb logcat -c`, launched via `am start` → process stayed alive,
    `MainActivity` became the resumed/top activity.
  - **Zero** occurrences of `FATAL EXCEPTION`, `WorkDatabase`,
    `InitializationProvider` in the fresh log (`shopzen_fix_log.txt`,
    `shopzen_fix_log2.txt`).
  - The log also shows the system re-killing a *cached* process
    (`adj 700, remove task`), a normal launcher-tap relaunch (process
    22527), a UMP/consent webview process spawning, and the soft keyboard
    opening in a text field inside the app — the app is fully usable on the
    device.
- Screenshot evidence: `shopzen_fix.png` (valid PNG, 60 KB).

## Production safety

`static/apk/shopzen-1.0.0.apk` remains untouched; nothing was pushed or
deployed; the fix APK stays at
`mobile_app/build/app/outputs/flutter-apk/app-release.apk`
(SHA-256 `078a5e72…f1e83`, 77,413,364 bytes, `versionCode=1`) until the owner
approves publishing it.

## Fix applied (defensive, smallest change)

`mobile_app/lib/main.dart` — bootstrap hardening so no optional subsystem or
first-frame error can kill the process:

- `main()` now runs the bootstrap inside `runZonedGuarded`, so an uncaught
  error from the fire-and-forget ads init can never become an uncaught
  root-zone error (which in an AOT release build tears the process down with
  no UI).
- `FlutterError.onError` + `PlatformDispatcher.instance.onError` handlers are
  installed so startup errors are reported instead of discarded in release.
- `runApp()` now executes before the optional UMP/AdMob init, so the first
  frame is never dependent on an optional subsystem.

No UI, branding, authentication, business logic, dependencies, application ID,
signing configuration or API contracts were changed.

## Verification performed here

- `flutter pub get` — OK
- `flutter analyze` — 0 errors, 0 warnings (34 pre-existing infos)
- `flutter test` — 36/36 pass
- `flutter build apk --release` — succeeded, existing debug signing config,
  73.8 MB, `versionCode=1`, package `com.dukaanflow.app`
- Output: `mobile_app/build/app/outputs/flutter-apk/app-release.apk`
  (SHA-256 `6ce98a4a…95438`); `classes.dex` unchanged, `libapp.so` updated,
  confirming the new Dart bootstrap is compiled in.
- Django backend: `manage.py check`, `makemigrations --check --dry-run`, and
  the `updates` app suite (25/25) all pass; no backend change was needed for
  this issue.
- **Not verified**: launch on the physical phone — the device is not attached
  to this machine and no emulator exists here.

## Manual steps to finish the diagnosis/verification

1. Connect the TECNO BF7 by USB and enable **Developer options → USB
   debugging** (or use **Wireless debugging** from the same screen and run
   `adb connect <phone-ip>:<port>`).
2. `cd C:\Users\HP\Desktop\DukaanFlow`
3. `C:\Users\HP\AppData\Local\Android\Sdk\platform-tools\adb.exe devices`
4. Replace the app (same signing key, same `versionCode`, so user data is
   kept):
   `…\platform-tools\adb.exe install -r mobile_app\build\app\outputs\flutter-apk\app-release.apk`
5. `…\platform-tools\adb.exe logcat -c`
6. Launch ShopZen from the phone.
7. `…\platform-tools\adb.exe logcat -d > shopzen_crash_log.txt` and search it
   for `FATAL`, `AndroidRuntime`, `flutter`, `tombstone`.

If the app still closes instantly, `shopzen_crash_log.txt` will contain the
exact exception (a `ClassNotFoundException`, a `Resources$NotFoundException`,
an AdMob/GMS error, or a Dart engine error). Paste the first `FATAL EXCEPTION`
block and the fix can be targeted precisely.

## Production safety

`static/apk/shopzen-1.0.0.apk` was **NOT** overwritten and nothing was pushed
or deployed. The rebuild lives only in `mobile_app/build/` until the fix is
confirmed on the phone.
