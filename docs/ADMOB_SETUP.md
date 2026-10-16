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
| Live/production ad unit IDs | ❌ **Not provided yet — owner action required** |
| AdMob App ID in `AndroidManifest.xml` | ⚠️ Currently Google's **test** App ID |
| Real ad impressions verified on a device | ❌ Not possible until the steps below are done |

**The current build serves Google's test creatives only. It earns no revenue
and must never be shipped to users as a monetized build.**

---

## Why it is not live yet

1. Google requires an **approved AdMob account** (identity + address
   verification, PIN by post, tax/ payment profile) before live ads serve.
   This approval takes days to weeks and depends on Google, not on the code.
2. Live ads need a real **ad unit ID** and a real **AdMob App ID** tied to the
   approved account. Inventing IDs is not allowed — invalid IDs crash the SDK
   on start.

Per the project rules, nothing here is reported as "done" without evidence.

---

## Owner activation steps (one-time)

### 1. Finish AdMob account verification
- Sign in at https://admob.google.com with the Google account that will
  receive payments.
- Complete **Identity verification**, **Address verification (PIN)** and the
  payment profile. Nothing serves live ads until these pass.

### 2. Register the app
- AdMob → **Apps → Add app** → **Android**, package name
  **`com.dukaanflow.app`** (no Play Store listing needed; select
  "No, my app isn't on any app stores yet" and enter the package name).
- Copy the app's **App ID** (`ca-app-pub-XXXXXXXXXXXXXXXX~XXXXXXXXXX`).

### 3. Create a banner ad unit
- Inside the app → **Ad units → Add ad unit → Banner**.
- Name it e.g. "ShopZen dashboard banner".
- Copy the **ad unit ID** (`ca-app-pub-XXXXXXXXXXXXXXXX/XXXXXXXXXX`).
- (Optional but recommended) create a second banner unit for safe targets.
  The app reads exactly **one** unit id at build time (see below).

### 4. Update the App ID in the manifest
Edit `mobile_app/android/app/src/main/AndroidManifest.xml`, replacing the
test value:

```xml
<meta-data
    android:name="com.google.android.gms.ads.APPLICATION_ID"
    android:value="ca-app-pub-XXXXXXXXXXXXXXXX~XXXXXXXXXX" />
```

> Google policy note: the App ID in the manifest must be the registered App ID
> of the app in your AdMob account. A wrong/other-account ID causes the SDK to
> crash at first ad load.

### 5. Rebuild with the live ad unit ID
The banner unit ID is injected at build time so it never gets hard-coded into
source control:

```bash
cd mobile_app
flutter build apk --release \
  --dart-define=ADMOB_BANNER_UNIT_ID=ca-app-pub-XXXXXXXXXXXXXXXX/XXXXXXXXXX
cp build/app/outputs/flutter-apk/app-release.apk ../release/app-release.apk
```

(Add `--dart-define=ADMOB_ENABLED=false` for an ad-free build.)

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
