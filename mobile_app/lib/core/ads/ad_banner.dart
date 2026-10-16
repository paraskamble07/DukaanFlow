import 'package:flutter/material.dart';
import 'package:google_mobile_ads/google_mobile_ads.dart';
import 'ad_config.dart';
import 'ads_service.dart';

/// A 320x50 AdMob banner.
///
/// Rendered ONLY on the dashboard, product list, customer list and settings
/// screens (per the product spec). Until the SDK is initialized and UMP
/// consent permits requests — including on desktop/test hosts — this widget
/// collapses to zero size, so screens look identical on non-ad builds.
class AdBanner extends StatefulWidget {
  const AdBanner({super.key});

  @override
  State<AdBanner> createState() => _AdBannerState();
}

class _AdBannerState extends State<AdBanner> {
  BannerAd? _bannerAd;
  bool _adLoaded = false;

  @override
  void initState() {
    super.initState();
    if (!AdsService.instance.canShowBanners) return;

    _bannerAd = BannerAd(
      adUnitId: AdConfig.bannerUnitId,
      size: AdSize.banner,
      request: const AdRequest(),
      listener: BannerAdListener(
        onAdLoaded: (_) {
          if (mounted) setState(() => _adLoaded = true);
        },
        onAdFailedToLoad: (ad, error) {
          ad.dispose();
          if (mounted) setState(() => _adLoaded = false);
        },
      ),
    )..load();
  }

  @override
  void dispose() {
    _bannerAd?.dispose();
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
