import 'dart:async';

import 'package:flutter/material.dart';
import 'package:google_mobile_ads/google_mobile_ads.dart';
import 'ad_config.dart';
import 'ads_service.dart';

/// A responsive AdMob banner (Google's adaptive anchored banner size).
///
/// Rendered ONLY on the dashboard, product list, customer list and settings
/// screens — never on login, payment, POS checkout, Khata collection, staff
/// permissions or any other critical flow. Until the SDK is initialized and
/// UMP consent permits requests — including on desktop/test hosts — this
/// widget collapses to zero size, so screens look identical on non-ad builds
/// and an ad failure never affects functionality.
class AdBanner extends StatefulWidget {
  const AdBanner({super.key});

  @override
  State<AdBanner> createState() => _AdBannerState();
}

class _AdBannerState extends State<AdBanner> with WidgetsBindingObserver {
  BannerAd? _bannerAd;
  bool _adLoaded = false;
  // The screen width the current banner was created for, so a metrics change
  // (rotation, split view) reloads exactly once per new width and never
  // duplicates instances.
  int _loadedWidth = 0;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    _loadBanner();
  }

  @override
  void didChangeMetrics() {
    // Orientation/resize: rebuild the banner at the new width. _loadBanner
    // no-ops when the width is unchanged.
    _loadBanner();
  }

  /// Loads one banner at the current window width, replacing any previously
  /// loaded banner first. Every failure path (no consent, unsupported
  /// platform, plugin missing, SDK without an adaptive height, ad request
  /// failed/no fill) leaves `_adLoaded` false → the widget renders nothing.
  Future<void> _loadBanner() async {
    if (!AdsService.instance.canShowBanners) return;
    if (!mounted) return;
    final width = MediaQuery.sizeOf(context).width.truncate();
    if (width <= 0) return;
    if (_bannerAd != null && width == _loadedWidth) return;

    _disposeAd();
    _loadedWidth = width;

    // Google's adaptive anchored size: full width, Google-optimized height
    // (50px–15% of screen height). Fall back to the fixed 320x50 banner when
    // the SDK cannot return a height (also covers the desktop/test host,
    // where the platform channel is absent).
    AdSize size = AdSize.banner;
    try {
      final adaptive =
          await AdSize.getLargeAnchoredAdaptiveBannerAdSize(width);
      if (adaptive != null && adaptive.height > 0) size = adaptive;
    } catch (_) {
      // Plugin/transport error: fixed banner size is still a valid request.
    }
    if (!mounted) return;

    _bannerAd = BannerAd(
      adUnitId: AdConfig.bannerUnitId,
      size: size,
      request: const AdRequest(),
      listener: BannerAdListener(
        onAdLoaded: (_) {
          if (mounted) setState(() => _adLoaded = true);
        },
        onAdFailedToLoad: (ad, error) {
          // No fill / network error: free the ad and take no space.
          ad.dispose();
          if (mounted) setState(() => _adLoaded = false);
        },
      ),
    )..load();
  }

  void _disposeAd() {
    _bannerAd?.dispose();
    _bannerAd = null;
    _adLoaded = false;
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _disposeAd();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final banner = _bannerAd;
    // AdWidget requires the ad to be loaded before it enters the tree, and
    // a failed/never-loaded banner simply occupies no space.
    if (banner == null || !_adLoaded) return const SizedBox.shrink();
    return Center(
      child: SizedBox(
        width: banner.size.width.toDouble(),
        height: banner.size.height.toDouble(),
        child: AdWidget(ad: banner),
      ),
    );
  }
}
