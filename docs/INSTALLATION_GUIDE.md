# ShopZen — Android Phone Installation & Testing Guide

ShopZen is the Flutter mobile app for the DukaanFlow backend (same Django + PostgreSQL, same database, same business logic).

---

## 1. Prerequisites (one-time)

1. **Flutter SDK** (3.x stable): install from https://docs.flutter.dev/get-started/install/windows — choose "Add to PATH" during setup.
2. **Android Studio** (for the Android SDK + platform tools) OR standalone command-line tools.
3. **Java 17** (Android Gradle Plugin 8.3 requires it). Check: `java -version` → 17.x. (Java 23 also works for AGP 8.3.2, but 17 is the LTS target.)
4. A physical Android phone with **USB debugging enabled**:
   Settings → About phone → tap Build number 7× → Developer options → enable USB debugging.

Verify the toolchain from a terminal:

```bash
flutter doctor
flutter doctor --android-licenses   # accept licenses
```

## 2. Connect your Android phone

```bash
flutter devices
```
You should see your phone listed (e.g. `R58M… • SM-A235F • android-arm64 • true`).
Accept the "Allow USB debugging" popup on the phone if it appears.

## 3. Point the app at your backend

The API base URL lives in `mobile_app/lib/core/constants/api_constants.dart`:

| Scenario | baseUrl value |
|---|---|
| Backend deployed on Render (default) | `https://dukaanflow.onrender.com` |
| Django running on your laptop + **Android emulator** | `http://10.0.2.2:8000` |
| Django running on your laptop + **physical phone on same Wi-Fi** | `http://<YOUR-LAPTOP-LAN-IP>:8000` (find it with `ipconfig` → IPv4, e.g. `http://192.168.1.5:8000`) |

⚠️ Never use `localhost` or `127.0.0.1` on the phone — that points at the phone itself.

Start a local backend if needed:
```bash
cd DukaanFlow
./venv/Scripts/python.exe manage.py runserver 0.0.0.0:8000
```

## 4. Run on the phone (live reload)

```bash
cd mobile_app
flutter pub get
flutter run
```
Select your phone when prompted. Hot reload: press `r`; hot restart: `R`; quit: `q`.

## 5. Build the APK

**Debug APK** (installs on any phone, logs visible):
```bash
flutter build apk --debug
```
→ `build/app/outputs/flutter-apk/app-debug.apk`

**Release APK** (smaller, faster):
```bash
flutter build apk --release
```
→ `build/app/outputs/flutter-apk/app-release.apk`

(Release builds are currently signed with the debug key so they install directly. For Play Store, create a keystore and configure `android/key.properties` — see `android/app/build.gradle` comment.)

## 6. Install the APK on the phone

Option A — via USB:
```bash
cd build/app/outputs/flutter-apk
adb install app-release.apk     # or: flutter install
```

Option B — manual: copy the APK to the phone (WhatsApp/USB/Drive), open it, allow "Install from unknown sources" when asked.

## 7. Login & smoke test

1. Open **ShopZen** on the phone (blue shop icon).
2. Register a shop (or login with your existing web credentials — same accounts).
3. Dashboard loads → tap **+ NEW SALE** → pick a product → Complete Sale → WhatsApp share prompt appears.
4. Check Stock tab — the quantity decreased.
5. More → Reports → Profit & Loss shows the real server-calculated numbers.

## 8. Troubleshooting

| Problem | Fix |
|---|---|
| `flutter: command not found` | Reopen terminal after install, or add `<flutter>\bin` to PATH |
| Phone not in `flutter devices` | Re-plug USB, accept debugging popup, install OEM USB driver |
| App opens but "Connection error" | Wrong baseUrl — use LAN IP, not localhost; check laptop firewall allows port 8000 |
| `Gradle ... failed` | Run `flutter clean`, delete `~/.gradle/caches`, retry; ensure Java 17 |
| Cleartext HTTP blocked on Android 9+ | For LAN dev add `android:usesCleartextTraffic="true"` in the `<application>` tag of AndroidManifest.xml and rebuild (only for local testing — production uses HTTPS) |
| Hot reload not applying | Press `R` for full restart |

## 9. Test suite

```bash
flutter test          # widget + model + currency format tests
flutter analyze       # static analysis (0 issues expected)
```
