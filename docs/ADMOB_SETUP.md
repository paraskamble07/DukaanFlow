# ShopZen — AdMob Setup Guide (Owner)

ShopZen is **free for every shop owner and employee**. Its only monetization is
Google AdMob **banner ads** — there are no subscriptions, paywalls or in-app
purchases, and all business payment features (khata, UPI payments, invoices)
are completely unaffected.

This guide tells the owner exactly how to switch the app from Google's test
ads to live ads, and what the current status is.

---

## Current status (honest)

| Item | Status |
|---|---|
| Google Mobile Ads SDK integrated | ✅ Done (`google_mobile_ads ^9.1.0`, Phase 12) |
| Google UMP consent flow | ✅ Done (consent form shown where required; ads gated on consent) |
| Banner placement code | ✅ Done — banners only on dashboard, product list, customer list, settings |
| Adaptive (responsive) banner size | ✅ Done — Google adaptive anchored banner with a 320x50 fallback |
| Live/production ad unit IDs | ✅ **Configured** (owner-provided on 2026-10-17; table below) |
| AdMob App ID in `AndroidManifest.xml` | ✅ Real ShopZen App ID |
| Real ad impressions verified on a device | ❌ **Still not done** — no physical Android device in the build environment; the owner must verify on a real phone (step 6) |

**Live configuration in this source tree:**

| Setting | Value | Where it lives |
|---|---|---|
| AdMob Android App ID | `ca-app-pub-8559634762194466~5030925195` | `mobile_app/android/app/src/main/AndroidManifest.xml` (`com.google.android.gms.ads.APPLICATION_ID`) |
| Banner Ad Unit ID (live) — **ShopZen_Banner_Home** | `ca-app-pub-8559634762194466/2011019340` | `mobile_app/lib/core/ads/ad_config.dart` (`AdConfig.liveBannerUnitId`) |
| Google test banner unit | `ca-app-pub-3940256099942544/6300978111` | same file (`AdConfig.testBannerUnitId`) |

**A release build uses the live unit; every development build (`flutter run`,
`flutter test`) uses Google's test unit automatically (see "Switching test
vs. live" below). Nothing has been shipped to users, and live ads only
actually serve once the AdMob account verification below is complete — a
successful build is NOT proof of live impressions.**

---

## Why it is not "earning" yet

1. Google requires an **approved AdMob account** (identity + address
   verification, PIN by post, tax/ payment profile) before live ads serve.
   This approval takes days to weeks and depends on Google, not on the code.
2. The real **ad unit ID** and **App ID** are now configured in this source
   tree (owner-provided 2026-10-17), and the release build compiles them in —
   but no live impression has been observed, because no physical Android
   device is available in the build environment.

Per the project rules, nothing here is reported as "done" without evidence.

---

## Owner activation steps (one-time)

> Steps 2–3 are **already done** — the owner registered the app
> (`com.dukaanflow.app`) and created the **ShopZen_Banner_Home** ad unit on
> 2026-10-17, and both IDs are wired into the source tree. They are kept here
> as a record of where the IDs came from. Only step 1 (account verification)
> and step 6 (on-device check) may still be open.

### 1. Finish AdMob account verification
- Sign in at https://admob.google.com with the Google account that will
  receive payments.
- Complete **Identity verification**, **Address verification (PIN)** and the
  payment profile. Nothing serves live ads until these pass.

### 2. Register the app (done)
- AdMob → **Apps → Add app** → **Android**, package name
  **`com.dukaanflow.app`** (no Play Store listing needed; select
  "No, my app isn't on any app stores yet" and enter the package name).
- Copy the app's **App ID** (`ca-app-pub-XXXXXXXXXXXXXXXX~XXXXXXXXXX`) —
  this produced `ca-app-pub-8559634762194466~5030925195`.

### 3. Create a banner ad unit (done)
- Inside the app → **Ad units → Add ad unit → Banner**.
- Named **ShopZen_Banner_Home** → ad unit ID
  `ca-app-pub-8559634762194466/2011019340`.
- The app reads exactly **one** unit id at build time (see step 5 below);
  a second unit can be added later if you want to A/B placements.

### 4. App ID in the manifest — already done
`mobile_app/android/app/src/main/AndroidManifest.xml` already carries the real
ShopZen App ID `ca-app-pub-8559634762194466~5030925195` (owner-provided
2026-10-17). No edit is needed unless the AdMob account/app changes:

```xml
<meta-data
    android:name="com.google.android.gms.ads.APPLICATION_ID"
    android:value="ca-app-pub-8559634762194466~5030925195" />
```

> Google policy note: the App ID in the manifest must be the registered App ID
> of the app in your AdMob account. A wrong/other-account ID causes the SDK to
> crash at first ad load.

### 5. Rebuild — the live ad unit is already wired in
`AdConfig.liveBannerUnitId` holds `ca-app-pub-8559634762194466/2011019340`
(**ShopZen_Banner_Home**). A plain release build picks it up automatically:

```bash
cd mobile_app
flutter build apk --release
cp build/app/outputs/flutter-apk/app-release.apk ../release/app-release.apk
```

The unit is chosen at compile time from `kReleaseMode`, so a release build
can never accidentally serve test traffic and a debug build can never serve
live traffic. Optional manual overrides (rarely needed):

```bash
# Force the test unit in a release build (e.g. for a pre-launch check):
flutter build apk --release \
  --dart-define=ADMOB_BANNER_UNIT_ID=ca-app-pub-3940256099942544/6300978111
# Ad-free build (the banner widget renders nothing):
flutter build apk --release --dart-define=ADMOB_ENABLED=false
```

Switching back is just rebuilding without the define — nothing in source has
to change, so test and live IDs are never confused.

### 6. Test before shipping to users
- Add your test device's ID in AdMob → Settings → **Test devices** so your
  own impressions never count and never violate policy (test ads are always
  labelled "Test Ad").
- On a real phone: open the app, accept the consent form when shown, then
  check the banner appears on the dashboard, product list, customer list and
  settings **only**.
- Check AdMob dashboard: the unit shows requests/impressions (delayed up to
  ~24h).

**Only after impressions appear in the AdMob dashboard is the monetized build
verified.** Until then, report the integration as complete but unverified.

---

## Consent (UMP) — what users see

- On first launch (where EEA/UK/other applicable regions require it), the app
  shows the Google consent form. Ads load only when the user consents or
  consent is not required in their region.
- Users can reset consent via Android **Settings → Apps → ShopZen → Storage →
  Clear data**; the form then re-appears.
- The SDK is never initialized without usable consent on a supported platform;
  a failed/absent consent check simply hides banners (the app works fully).

## AdMob policies that matter for this app

- **No PII in ad requests.** The app passes no user, shop or customer data to
  AdMob; the banner uses the default targeting only.
- **No ads on sensitive screens.** Banners are placed only on dashboard,
  product list, customer list and settings — never on login, invoices,
  payment confirmation, or above action controls.
- **No invalid traffic.** Never click your own live ads; use test devices.
