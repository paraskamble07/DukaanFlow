import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:package_info_plus/package_info_plus.dart';

import '../core/constants/api_constants.dart';
import '../core/network/api_client.dart';
import '../models/app_update_model.dart';
import 'auth_provider.dart';

final appUpdateProvider =
    StateNotifierProvider<AppUpdateNotifier, AppUpdateState>((ref) {
  return AppUpdateNotifier(ref.read(apiClientProvider));
});

class AppUpdateState {
  final bool isChecking;
  final AppUpdateInfo? info;
  final String? errorMessage;

  /// Installed build details (from package_info_plus).
  final String installedVersion;
  final int installedBuildNumber;

  AppUpdateState({
    this.isChecking = false,
    this.info,
    this.errorMessage,
    this.installedVersion = '',
    this.installedBuildNumber = 0,
  });

  AppUpdateState copyWith({
    bool? isChecking,
    AppUpdateInfo? info,
    String? errorMessage,
    String? installedVersion,
    int? installedBuildNumber,
  }) {
    return AppUpdateState(
      isChecking: isChecking ?? this.isChecking,
      info: info ?? this.info,
      errorMessage: errorMessage,
      installedVersion: installedVersion ?? this.installedVersion,
      installedBuildNumber:
          installedBuildNumber ?? this.installedBuildNumber,
    );
  }

  bool get updateAvailable => info?.updateAvailable ?? false;
  bool get mandatoryUpdate => info?.mandatoryUpdate ?? false;
}

class AppUpdateNotifier extends StateNotifier<AppUpdateState> {
  final ApiClient _client;

  AppUpdateNotifier(this._client) : super(AppUpdateState()) {
    _loadPackageInfo();
  }

  Future<void> _loadPackageInfo() async {
    try {
      final pkg = await PackageInfo.fromPlatform();
      state = state.copyWith(
        installedVersion: pkg.version,
        installedBuildNumber: int.tryParse(pkg.buildNumber) ?? 0,
      );
    } catch (_) {
      // Stays at defaults (0) — the check then reports whatever the
      // server says, and the UI shows the version string it has.
    }
  }

  /// Queries the trusted manifest. Safe to call on every app start:
  /// failures leave the previous state intact and never block the user
  /// (unless the server explicitly demands a mandatory update).
  Future<AppUpdateInfo?> checkForUpdates({
    bool failSilently = true,
  }) async {
    state = state.copyWith(isChecking: true, errorMessage: null);
    try {
      final res = await _client.dio.get(
        ApiConstants.appUpdateCheck,
        queryParameters: {
          'platform': 'android',
          'version_code': state.installedBuildNumber,
        },
      );
      if (res.statusCode == 200 && res.data is Map<String, dynamic>) {
        final info = AppUpdateInfo.fromJson(
            res.data as Map<String, dynamic>);
        state = state.copyWith(isChecking: false, info: info);
        return info;
      }
      state = state.copyWith(
        isChecking: false,
        errorMessage: 'Unexpected response from the update service.',
      );
    } catch (e) {
      state = state.copyWith(
        isChecking: false,
        errorMessage: 'Could not reach the update service. Check your connection.',
      );
      if (!failSilently) rethrow;
    }
    return null;
  }
}
