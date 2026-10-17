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

  /// False when package_info could not report the build number, in which
  /// case a server "mandatory" verdict is unverifiable and must not block.
  final bool packageInfoKnown;

  AppUpdateState({
    this.isChecking = false,
    this.info,
    this.errorMessage,
    this.installedVersion = '',
    this.installedBuildNumber = 0,
    this.packageInfoKnown = false,
  });

  AppUpdateState copyWith({
    bool? isChecking,
    AppUpdateInfo? info,
    String? errorMessage,
    String? installedVersion,
    int? installedBuildNumber,
    bool? packageInfoKnown,
  }) {
    return AppUpdateState(
      isChecking: isChecking ?? this.isChecking,
      info: info ?? this.info,
      errorMessage: errorMessage,
      installedVersion: installedVersion ?? this.installedVersion,
      installedBuildNumber:
          installedBuildNumber ?? this.installedBuildNumber,
      packageInfoKnown: packageInfoKnown ?? this.packageInfoKnown,
    );
  }

  bool get updateAvailable => info?.updateAvailable ?? false;
  bool get mandatoryUpdate => info?.mandatoryUpdate ?? false;
}

class AppUpdateNotifier extends StateNotifier<AppUpdateState> {
  final ApiClient _client;

  /// Completes when PackageInfo.fromPlatform() has resolved (or failed).
  /// checkForUpdates awaits it so the request always carries the *real*
  /// build number — otherwise a slow package_info makes the check race and
  /// send build 0, which the server cannot distinguish from a genuinely
  /// ancient build, and the app blocks the user behind a false
  /// "Update required" popup.
  Future<void>? _packageInfoReady;
  bool _packageInfoKnown = false;

  AppUpdateNotifier(this._client) : super(AppUpdateState()) {
    _packageInfoReady = _loadPackageInfo();
  }

  Future<void> _loadPackageInfo() async {
    try {
      final pkg = await PackageInfo.fromPlatform();
      state = state.copyWith(
        installedVersion: pkg.version,
        installedBuildNumber: int.tryParse(pkg.buildNumber) ?? 0,
      );
      _packageInfoKnown = int.tryParse(pkg.buildNumber) != null;
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
    // Never send the build number before package_info has resolved, or the
    // server sees build 0 and answers "mandatory update" for a client that
    // may already be the newest build.
    await _packageInfoReady;

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
        state = state.copyWith(
          isChecking: false,
          info: info,
          packageInfoKnown: _packageInfoKnown,
        );
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
