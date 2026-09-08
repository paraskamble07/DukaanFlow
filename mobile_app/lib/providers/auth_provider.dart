import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../core/network/api_client.dart';
import '../models/user_model.dart';
import '../models/business_model.dart';

final apiClientProvider = Provider<ApiClient>((ref) => ApiClient());

class AuthState {
  final bool isLoading;
  final bool isAuthenticated;
  final UserModel? user;
  final BusinessModel? business;
  final String? errorMessage;

  AuthState({
    this.isLoading = false,
    this.isAuthenticated = false,
    this.user,
    this.business,
    this.errorMessage,
  });

  AuthState copyWith({
    bool? isLoading,
    bool? isAuthenticated,
    UserModel? user,
    BusinessModel? business,
    String? errorMessage,
  }) {
    return AuthState(
      isLoading: isLoading ?? this.isLoading,
      isAuthenticated: isAuthenticated ?? this.isAuthenticated,
      user: user ?? this.user,
      business: business ?? this.business,
      errorMessage: errorMessage,
    );
  }
}

/// ShopZen v2 — local-first: there is NO login, NO server and NO account.
/// "Authentication" simply means "a shop profile exists on this device".
/// - checkAuth() loads the local profile (was: JWT restore).
/// - register() creates/updates the local shop profile (first launch).
/// - resetApp() wipes all local data after a double confirmation.
class AuthNotifier extends StateNotifier<AuthState> {
  final ApiClient _client;

  AuthNotifier(this._client) : super(AuthState()) {
    checkAuth();
  }

  Future<void> checkAuth() async {
    try {
      final res = await _client.dio.get('/api/auth/profile/');
      final userJson = res.data['user'];
      final bizJson = res.data['business'];
      state = state.copyWith(
        isAuthenticated: bizJson != null,
        user: userJson != null ? UserModel.fromJson(userJson) : null,
        business: bizJson != null ? BusinessModel.fromJson(bizJson) : null,
      );
    } catch (_) {
      state = state.copyWith(isAuthenticated: false);
    }
  }

  /// First-launch shop setup — purely local, no account is created.
  Future<bool> register({
    required String fullName,
    required String shopName,
    required String phone,
    String email = '',
    String password = '',
  }) async {
    state = state.copyWith(isLoading: true, errorMessage: null);
    try {
      final res = await _client.dio.post(
        '/api/auth/register/',
        data: {
          'full_name': fullName.trim(),
          'shop_name': shopName.trim(),
          'phone': phone.trim(),
          'email': email.trim(),
        },
      );
      final user = UserModel.fromJson(res.data['user']);
      final business = BusinessModel.fromJson(res.data['business']);
      state = state.copyWith(
        isLoading: false,
        isAuthenticated: true,
        user: user,
        business: business,
      );
      return true;
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        errorMessage: 'Could not save your shop profile: $e',
      );
      return false;
    }
  }

  /// DANGEROUS — wipes every local record. The DB wipe itself
  /// (AppLocalDb.resetAll) runs in the settings screen right before this,
  /// behind a double confirmation dialog.
  Future<void> resetApp() async {
    state = AuthState();
  }
}

final authProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  return AuthNotifier(ref.watch(apiClientProvider));
});
