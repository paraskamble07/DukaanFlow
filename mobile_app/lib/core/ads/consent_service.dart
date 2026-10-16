import 'package:flutter/services.dart';
import 'package:user_messaging_platform/user_messaging_platform.dart';
import 'ad_config.dart';

/// Outcome of the startup consent (UMP) check.
class ConsentResult {
  const ConsentResult({required this.status, required this.formShown});

  /// Consent status reported by the UMP SDK after this check.
  final ConsentStatus status;

  /// Whether a UMP consent form was presented to the user.
  final bool formShown;

  /// Ads may only be requested when consent was obtained or is not required.
  bool get canRequestAds => consentAllowsAds(status);
}

/// Pure helper: Google's UMP rules permit ad requests only when consent is
/// [ConsentStatus.obtained] or not required in the user's region.
bool consentAllowsAds(ConsentStatus status) {
  return status == ConsentStatus.obtained || status == ConsentStatus.notRequired;
}

/// Wraps the Google User Messaging Platform (UMP) consent flow.
///
/// The flow runs once at startup: request consent info update, and if consent
/// is required and a form is available, present the form. Any SDK failure
/// (no network, missing plugin on desktop) is swallowed and reported as
/// [ConsentStatus.unknown], which keeps ads off but never blocks the app.
class ConsentService {
  ConsentService._();
  static final ConsentService instance = ConsentService._();

  Future<ConsentResult> requestConsent() async {
    if (!AdConfig.enabled) {
      return const ConsentResult(status: ConsentStatus.unknown, formShown: false);
    }
    try {
      final info = await UserMessagingPlatform.instance.requestConsentInfoUpdate(
        ConsentRequestParameters(tagForUnderAgeOfConsent: false),
      );
      if (info.consentStatus == ConsentStatus.required &&
          info.formStatus == FormStatus.available) {
        final updated = await UserMessagingPlatform.instance.showConsentForm();
        return ConsentResult(status: updated.consentStatus, formShown: true);
      }
      return ConsentResult(status: info.consentStatus, formShown: false);
    } on PlatformException {
      // UMP unreachable; banners simply stay hidden until the next check.
      return const ConsentResult(status: ConsentStatus.unknown, formShown: false);
    }
  }
}
