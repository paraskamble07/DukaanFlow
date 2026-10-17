import 'package:dio/dio.dart';

import '../localization/app_localizations.dart';

/// Renders an API failure honestly and usefully.
///
/// A 404 on a feature screen does not mean "no data" — it means the running
/// ShopZen backend predates that feature (e.g. staff logins or notifications
/// before they were deployed). Say that instead of dumping a raw
/// [DioException], so the shop owner knows the fix is a backend update and
/// not something they did.
String apiErrorMessage(Object error, AppLocalizations l10n) {
  final status = error is DioException ? error.response?.statusCode : null;
  if (status == 404) {
    return '${l10n.translate('error_404_backend')} (HTTP 404)';
  }
  return '${l10n.translate('error_prefix')}$error';
}
