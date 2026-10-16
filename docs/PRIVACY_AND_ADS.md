# ShopZen — Privacy & Ads Policy Notes

App: ShopZen (Android, package `com.dukaanflow.app`)
Free app. Monetization: Google AdMob banner ads only — no subscriptions, no
paywalls, no in-app purchases.
Last updated: 2026-10-16

This document supports the app's public privacy policy (required by Google
Play and AdMob). It states precisely what data the app handles, what the ads
SDK sees, and what it does not.

---

## 1. What ShopZen collects and why

| Data | Where it goes | Why |
|---|---|---|
| Shop profile (name, owner, phone, address, GSTIN, UPI id), entered by the owner | Backend PostgreSQL, only the owner's account | Runs the shop's billing/khata |
| Products, stock, IMEI numbers, customers, sales, payments, expenses | Backend, scoped to the shop (`business`) | The app's purpose |
| Login credentials | App's secure storage (Flutter secure storage) + server-side hashed passwords | Authentication (JWT) |
| Locale / theme / offline queue | On-device | UX, offline billing |

All business data belongs to the shop and stays within its tenant; no other
shop (tenant) can read it (see `docs/SECURITY.md`).

## 2. What the advertising SDK sees

- The Google Mobile Ads SDK is initialized **only** when the UMP consent flow
  allows ad requests (consent obtained, or consent not required in the
  region).
- The app passes **no PII** to AdMob: no shop name, customer name, phone,
  email or invoice data is included in ad requests. Banners use the SDK's
  default request.
- Only **banner** ads — no interstitials, no rewarded ads, no opening ad.

## 3. Ad placement

Banners appear on exactly four screens:

1. Dashboard
2. Product list (inventory)
3. Customer list (khata)
4. Settings

Banners never appear on the login/onboarding screens, the invoice or payment
confirmation screens, or over action controls. Content below a banner scrolls
normally; if an ad fails to load the space collapses (the app is unaffected).

## 4. Consent and controls

- Where required (EEA/UK and other applicable regions) the app shows the
  Google User Messaging Platform (UMP) consent form at first launch.
- If the user declines, **no ads are requested and the app works
  identically** — declining never disables any feature.
- Users can review/reset their consent any time from
  **Settings → Apps → ShopZen → Storage → Clear data**.
- There is no ad-free paid tier (the app is free for everyone).

## 5. Debug/test builds

Developer and current APK builds use Google's **documented test ad unit and
test App ID** (`ca-app-pub-3940256099942544/6300978111`). Test creatives are
labelled "Test Ad", earn no revenue and are used so development devices never
generate policy-violating traffic. Live unit IDs are injected at build time
only when the owner activates monetization (see `docs/ADMOB_SETUP.md`).

## 6. Children

The app is a business tool for shop owners and staff; it is not directed at
children. The consent request sets `tagForUnderAgeOfConsent = false`.

---

## Owner action needed

A public privacy policy page (required by the Play Console/AdMob) should
mirror sections 1–6 of this document and be hosted at a public URL before a
monetized Play Store submission. The app itself contains no embedded privacy
policy URL yet — add it as part of the store listing.
