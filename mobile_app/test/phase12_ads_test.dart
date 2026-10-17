import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:google_mobile_ads/google_mobile_ads.dart';
import 'package:dukaanflow/core/ads/ad_banner.dart';
import 'package:dukaanflow/core/ads/ad_config.dart';
import 'package:dukaanflow/core/ads/ads_service.dart';
import 'package:dukaanflow/core/ads/consent_service.dart';

void main() {
  group('AdConfig', () {
    test('ads are enabled by default', () {
      expect(AdConfig.enabled, isTrue);
    });

    test('debug builds use the official Google test banner unit id', () {
      // The test host is a debug build (kReleaseMode == false), so the
      // effective unit is the Google test unit — never live traffic.
      expect(AdConfig.bannerUnitId, AdConfig.testBannerUnitId);
      expect(AdConfig.bannerUnitId, 'ca-app-pub-3940256099942544/6300978111');
    });

    test('the live unit is the ShopZen_Banner_Home unit id', () {
      expect(AdConfig.liveBannerUnitId, 'ca-app-pub-8559634762194466/2011019340');
      // Structural guard: an AdMob app id (~) must never be used as a unit id (/).
      expect(AdConfig.liveBannerUnitId.contains('/'), isTrue);
      expect(AdConfig.liveBannerUnitId.contains('~'), isFalse);
    });

    test('test unit id is never reported as a live unit id', () {
      expect(AdConfig.isLiveUnitId, isFalse,
          reason: 'default debug build must never claim live ad traffic');
    });

    test('supportsPlatform only allows Android and iOS', () {
      expect(AdConfig.supportsPlatform(isAndroid: true, isIos: false), isTrue);
      expect(AdConfig.supportsPlatform(isAndroid: false, isIos: true), isTrue);
      expect(AdConfig.supportsPlatform(isAndroid: true, isIos: true), isTrue);
      expect(AdConfig.supportsPlatform(isAndroid: false, isIos: false), isFalse,
          reason: 'desktop/test hosts never serve banners');
    });
  });

  group('consent gating', () {
    test('consentAllowsAds permits only obtained and notRequired', () {
      expect(consentAllowsAds(ConsentStatus.obtained), isTrue);
      expect(consentAllowsAds(ConsentStatus.notRequired), isTrue);
      expect(consentAllowsAds(ConsentStatus.required), isFalse);
      expect(consentAllowsAds(ConsentStatus.unknown), isFalse);
    });

    test('ConsentResult reports ad permission from the SDK verdict', () {
      expect(
          const ConsentResult(canRequestAds: true, formShown: true).canRequestAds,
          isTrue);
      expect(
          const ConsentResult(canRequestAds: true, formShown: false).canRequestAds,
          isTrue);
      expect(
          const ConsentResult(canRequestAds: false, formShown: false).canRequestAds,
          isFalse,
          reason: 'a failed or declined consent check never allows ads');
    });
  });

  group('AdsService', () {
    test('shouldInitialize requires enabled platform and consent', () {
      expect(
          AdsService.shouldInitialize(
              enabled: true, supported: true, consentGranted: true),
          isTrue);
      expect(
          AdsService.shouldInitialize(
              enabled: false, supported: true, consentGranted: true),
          isFalse);
      expect(
          AdsService.shouldInitialize(
              enabled: true, supported: false, consentGranted: true),
          isFalse,
          reason: 'desktop builds must not initialize the SDK');
      expect(
          AdsService.shouldInitialize(
              enabled: true, supported: true, consentGranted: false),
          isFalse,
          reason: 'no UMP consent, no ads');
    });

    test('a fresh service cannot show banners', () {
      // The test host is a desktop platform, so banners are off regardless of
      // the consent state.
      expect(AdsService.instance.isInitialized, isFalse);
    });
  });

  group('AdBanner widget', () {
    testWidgets('renders nothing when the SDK cannot serve banners',
        (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(body: AdBanner()),
        ),
      );
      await tester.pump();

      expect(find.byType(AdBanner), findsOneWidget);
      // No banner is loaded on the desktop test host: the widget collapses to
      // zero size instead of showing a placeholder.
      final size = tester.getSize(find.byType(AdBanner));
      expect(size.width, 0);
      expect(size.height, 0);
      expect(find.byType(SizedBox), findsWidgets);
    });

    testWidgets(
        'unmounting and remounting the banner leaks nothing and never throws',
        (tester) async {
      // Simulates navigating away from a screen and back: the state disposes
      // its observer/ad, a fresh instance starts from scratch. No duplicate
      // instances accumulate, no exceptions escape on the desktop host.
      for (var i = 0; i < 3; i++) {
        await tester.pumpWidget(
          const MaterialApp(
            home: Scaffold(body: AdBanner()),
          ),
        );
        await tester.pump();
        expect(find.byType(AdBanner), findsOneWidget);
        // Replacing the tree disposes the widget between cycles.
        await tester.pumpWidget(const MaterialApp(home: Scaffold()));
        await tester.pump();
      }
      expect(tester.takeException(), isNull);
    });
  });
}
