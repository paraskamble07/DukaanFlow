import 'dart:async';

import 'package:flutter/services.dart';
import 'package:google_mobile_ads/google_mobile_ads.dart';
import 'ad_config.dart';

/// Outcome of the startup consent (UMP) check.
class ConsentResult {
  const ConsentResult({required this.canRequestAds, required this.formShown});

  /// Whether Google's UMP allows ad requests after this check.
  final bool canRequestAds;

  /// Whether a UMP consent form was presented to the user.
  final bool formShown;
}

/// Pure helper: the UMP rules permit ad requests only when consent is
/// [ConsentStatus.obtained] or not required in the user's region.
bool consentAllowsAds(ConsentStatus status) {
  return status == ConsentStatus.obtained || status == ConsentStatus.notRequired;
}

/// Wraps the Google User Messaging Platform (UMP) consent flow that ships
/// inside the `google_mobile_ads` SDK.
///
/// The flow runs once at startup: request a consent info update, and when
/// consent is required and a form is available, present the form. Ad
/// permission always comes from the SDK's authoritative
/// `ConsentInformation.canRequestAds()`. Any SDK failure (no network, missing
/// plugin on desktop) is swallowed into a negative result, which keeps ads
/// off but never blocks the app.
class ConsentService {
  ConsentService._();
  static final ConsentService instance = ConsentService._();

  Future<ConsentResult> requestConsent() async {
    if (!AdConfig.enabled) {
      return const ConsentResult(canRequestAds: false, formShown: false);
    }
    try {
      await _requestConsentInfoUpdate();
      final status = await ConsentInformation.instance.getConsentStatus();
      if (status == ConsentStatus.required &&
          await ConsentInformation.instance.isConsentFormAvailable()) {
        await _showConsentForm();
        // After the user interacts, the SDK is authoritative.
        return ConsentResult(
          canRequestAds: await ConsentInformation.instance.canRequestAds(),
          formShown: true,
        );
      }
      return ConsentResult(
        canRequestAds: await ConsentInformation.instance.canRequestAds(),
        formShown: false,
      );
    } on PlatformException {
      // UMP unreachable; banners simply stay hidden until the next check.
      return const ConsentResult(canRequestAds: false, formShown: false);
    }
  }

  Future<void> _requestConsentInfoUpdate() {
    final completer = Completer<void>();
    ConsentInformation.instance.requestConsentInfoUpdate(
      ConsentRequestParameters(tagForUnderAgeOfConsent: false),
      completer.complete,
      (error) => completer.completeError(
        PlatformException(code: 'ump:${error.errorCode}', message: error.message),
      ),
    );
    return completer.future;
  }

  Future<void> _showConsentForm() {
    final completer = Completer<void>();
    ConsentForm.loadConsentForm(
      (form) => form.show((formError) {
        if (formError == null) {
          completer.complete();
        } else {
          completer.completeError(
            PlatformException(code: 'ump:${formError.errorCode}', message: formError.message),
          );
        }
      }),
      (error) => completer.completeError(
        PlatformException(code: 'ump:${error.errorCode}', message: error.message),
      ),
    );
    return completer.future;
  }
}
