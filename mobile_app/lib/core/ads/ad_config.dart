import 'package:flutter/foundation.dart';

/// AdMob configuration for ShopZen (Phase 12; live ids added 2026-10-17).
///
/// The app is free for shop owners and employees. Monetization is Google
/// AdMob banner ads only, shown on the dashboard, product list, customer list
/// and settings screens.
///
/// Test vs. live traffic can never be confused:
///  * **debug builds** (`flutter run`, `flutter test`) always use Google's
///    documented **test** banner unit id — test creatives only, never
///    counted as live traffic, safe to look at during development;
///  * **release builds** (`flutter build apk --release`) use the shop's live
///    banner unit **ShopZen_Banner_Home** (ad unit name in the AdMob
///    console);
///  * both defaults are overridable at build time, e.g. to smoke-test the
///    live unit from a debug build or to ship an ad-free release:
///    ```
///    flutter build apk --release \
///      --dart-define=ADMOB_BANNER_UNIT_ID=ca-app-pub-3940256099942544/6300978111
///    ```
///
/// The matching AdMob **application id** (`ca-app-pub-8559634762194466~5030925195`)
/// lives in `android/app/src/main/AndroidManifest.xml` as the
/// `com.google.android.gms.ads.APPLICATION_ID` meta-data: the SDK requires it
/// to identify the AdMob account that owns the live unit below. Test ad units
/// still serve test creatives with any application id, so development builds
/// stay safe.
class AdConfig {
  AdConfig._();

  /// Google-documented Android/iOS test banner unit id
  /// (https://developers.google.com/admob/android/test-ads).
  static const String testBannerUnitId = 'ca-app-pub-3940256099942544/6300978111';

  /// **ShopZen_Banner_Home** — the owner's live banner unit (AdMob publisher
  /// 8559634762194466). Only release builds use this by default.
  static const String liveBannerUnitId = 'ca-app-pub-8559634762194466/2011019340';

  /// Banner ad unit id used by every banner in the app. Debug builds serve
  /// Google test creatives by default; release builds serve the live unit.
  /// Override either with `--dart-define=ADMOB_BANNER_UNIT_ID=...`.
  static const String bannerUnitId = String.fromEnvironment(
    'ADMOB_BANNER_UNIT_ID',
    defaultValue: kReleaseMode ? liveBannerUnitId : testBannerUnitId,
  );

  /// Master switch for all ads. Override at build time with
  /// `--dart-define=ADMOB_ENABLED=false` to ship an ad-free build.
  static const bool enabled = bool.fromEnvironment(
    'ADMOB_ENABLED',
    defaultValue: true,
  );

  /// True only when a real, revenue-earning unit id is configured. Test
  /// impressions must never be reported as live ad traffic, so diagnostics
  /// and documentation check this before claiming anything about revenue.
  static bool get isLiveUnitId => bannerUnitId != testBannerUnitId;

  /// Pure helper: whether banners are supported on a platform.
  static bool supportsPlatform({required bool isAndroid, required bool isIos}) {
    return isAndroid || isIos;
  }
}
