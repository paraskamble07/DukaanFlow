import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:user_messaging_platform/user_messaging_platform.dart';
import 'package:dukaanflow/core/ads/ad_banner.dart';
import 'package:dukaanflow/core/ads/ad_config.dart';
import 'package:dukaanflow/core/ads/ads_service.dart';
import 'package:dukaanflow/core/ads/consent_service.dart';

void main() {
  group('AdConfig', () {
    test('ads are enabled by default', () {
      expect(AdConfig.enabled, isTrue);
    });

    test('falls back to the official Google test banner unit id', () {
      expect(AdConfig.bannerUnitId, AdConfig.testBannerUnitId);
      expect(AdConfig.bannerUnitId, 'ca-app-pub-3940256099942544/6300978111');
    });

    test('test unit id is never reported as a live unit id', () {
      expect(AdConfig.isLiveUnitId, isFalse,
          reason: 'default build must never claim live ad traffic');
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

    test('ConsentResult.canRequestAds mirrors the consent verdict', () {
      expect(
          const ConsentResult(status: ConsentStatus.obtained, formShown: true)
              .canRequestAds,
          isTrue);
      expect(
          const ConsentResult(status: ConsentStatus.notRequired, formShown: false)
              .canRequestAds,
          isTrue);
      expect(
          const ConsentResult(status: ConsentStatus.required, formShown: false)
              .canRequestAds,
          isFalse);
      expect(
          const ConsentResult(status: ConsentStatus.unknown, formShown: false)
              .canRequestAds,
          isFalse);
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
  });
}
