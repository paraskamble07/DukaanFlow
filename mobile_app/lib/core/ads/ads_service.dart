import 'dart:io';

import 'package:google_mobile_ads/google_mobile_ads.dart';
import 'ad_config.dart';

/// Owns the lifetime of the Google Mobile Ads SDK.
///
/// The SDK is initialized only when all three gates pass:
/// 1. [AdConfig.enabled] (build-time master switch),
/// 2. the platform actually serves banners (Android/iOS),
/// 3. UMP consent permits ad requests.
///
/// On every other platform (desktop/test host) this service stays inert and
/// [canShowBanners] is false, so [AdBanner] renders nothing.
class AdsService {
  AdsService._();
  static final AdsService instance = AdsService._();

  bool _initialized = false;
  bool _consentGranted = false;

  /// Whether [initialize] has run the SDK successfully.
  bool get isInitialized => _initialized;

  /// Whether UMP consent currently permits ad requests.
  bool get consentGranted => _consentGranted;

  /// True only when a banner may be displayed right now.
  bool get canShowBanners =>
      AdConfig.enabled && supportsPlatform && _initialized && _consentGranted;

  /// Whether this device platform serves AdMob banners.
  bool get supportsPlatform =>
      AdConfig.supportsPlatform(isAndroid: Platform.isAndroid, isIos: Platform.isIOS);

  /// Pure gate used both by [initialize] and by tests.
  static bool shouldInitialize({
    required bool enabled,
    required bool supported,
    required bool consentGranted,
  }) {
    return enabled && supported && consentGranted;
  }

  /// Initializes the SDK (ads stay off unless every gate passes).
  Future<void> initialize({required bool consentGranted}) async {
    _consentGranted = consentGranted;
    if (!shouldInitialize(
      enabled: AdConfig.enabled,
      supported: supportsPlatform,
      consentGranted: consentGranted,
    )) {
      return;
    }
    if (_initialized) return;
    await MobileAds.instance.initialize();
    _initialized = true;
  }
}
