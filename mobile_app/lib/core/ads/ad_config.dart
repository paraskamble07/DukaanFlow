/// AdMob configuration for ShopZen (Phase 12).
///
/// The app is free for shop owners and employees. Monetization is Google
/// AdMob banner ads only, shown on the dashboard, product list, customer list
/// and settings screens.
///
/// The live ad unit id is supplied at build time with
/// `--dart-define=ADMOB_BANNER_UNIT_ID=ca-app-pub-<publisher>/<unit>` so the
/// owner's real ids stay out of source control. Until a live unit id is
/// provided we fall back to Google's documented test banner unit id, which
/// renders test creatives and never earns revenue.
class AdConfig {
  AdConfig._();

  /// Google-documented Android/iOS test banner unit id
  /// (https://developers.google.com/admob/android/test-ads).
  static const String testBannerUnitId = 'ca-app-pub-3940256099942544/6300978111';

  /// Banner ad unit id used by every banner in the app. Override at build
  /// time: `--dart-define=ADMOB_BANNER_UNIT_ID=ca-app-pub-.../...`.
  static const String bannerUnitId = String.fromEnvironment(
    'ADMOB_BANNER_UNIT_ID',
    defaultValue: testBannerUnitId,
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
