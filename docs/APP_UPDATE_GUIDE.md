# ShopZen — App Update Guide

How ShopZen checks for, presents and installs updates — and how the owner
publishes a new release.

Last updated: 2026-10-16.

---

## 1. How updates are delivered

The release channel is **side-loaded APK distribution**: the app is installed
from an `app-release.apk` (Android, package `com.dukaanflow.app`), not from
Google Play. So updates are:

- Announced by a **server-side release record** (checked on app open), and
- Installed by the user downloading the new APK and confirming the Android
  installer prompt.

## 2. The check-for-update flow (what the user sees)

1. On app open, the app calls the update endpoint with its `versionCode`
   (`flutter.versionCode`, currently `1`) and platform (`android`).
2. The server compares it against published releases
   (`Update` model, `updates` app).
3. If a newer active release exists:
   - **Soft update:** a card offers "Download" with what's-new notes; the
     user may decline.
   - **Mandatory update** (minimum build): the app blocks with an
     "Update required" screen until the new APK is installed.
4. The download runs inside the app; tapping install hands the APK to
   Android's package installer. The app never silently installs anything.
5. "You're on the latest version" when nothing is newer.

## 3. Publishing a new release (owner)

Releases are created in the Django admin (`/admin/updates/update/`):

| Field | Meaning |
|---|---|
| `version_name` | e.g. `1.1.0` (display) |
| `version_code` | integer, must be **greater than** the built APK's `flutter.versionCode` (start with a low first value when the built code is 1) |
| `platform` | `android` (default) |
| `download_url` | public URL of the new `app-release.apk` |
| `is_active` | must be true for the release to be served |
| `release_notes` | what's-new text |
| `minimum_build` | versions below this are force-blocked |
| `created_at` | publish date |

Steps for a version bump:

1. Bump `version:` in `mobile_app/pubspec.yaml` (e.g. `1.1.0+2`) — the `+N`
   part is `versionCode`, so it must exceed the previous build.
2. Rebuild (`docs/RELEASE_GUIDE.md`).
3. Upload the APK to a public host (Render static, a CDN, GitHub release,
   Google Drive isn't reliable for direct downloads).
4. Create the active `Update` record with matching `version_code`.
5. Users see the update card on next app open.

## 4. Tested?

- Server side: `updates/tests.py` — availability, mandatory flag, inactive
  releases hidden, invalid version codes rejected, admin publish — all pass.
- Flutter side: update screen + provider tests pass.
- **End-to-end on a physical device: not performed** (no device available for
  this build flow; the APK reinstall path is documented in the acceptance
  document).

## 5. Current status

The production service has not served the App Update endpoints yet — the
pending Render deploy (see `docs/DEPLOYMENT_GUIDE.md`) also activates the
`updates` app on production. Nothing here is reported as verified on
production until that deploy happens.
