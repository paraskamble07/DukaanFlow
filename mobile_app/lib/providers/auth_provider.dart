import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:dio/dio.dart';
import '../core/constants/api_constants.dart';
import '../core/network/api_client.dart';
import '../core/storage/local_storage.dart';
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

class AuthNotifier extends StateNotifier<AuthState> {
  final ApiClient _client;
  final Completer<void> _restoreDone = Completer<void>();

  /// Completes when the persisted login has been restored (or found absent).
  /// The splash screen awaits this instead of guessing with a fixed timer —
  /// Android keystore reads can outlast a hardcoded delay and would otherwise
  /// log the user out on every cold start.
  Future<void> get ready => _restoreDone.future;

  AuthNotifier(this._client) : super(AuthState()) {
    checkAuth().whenComplete(() {
      if (!_restoreDone.isCompleted) _restoreDone.complete();
    });
  }

  Future<void> checkAuth() async {
    final token = await LocalStorageService.getAccessToken();
    if (token != null && token.isNotEmpty) {
      final userJson = await LocalStorageService.getUser();
      final bizJson = await LocalStorageService.getBusiness();
      if (userJson != null && bizJson != null) {
        state = state.copyWith(
          isAuthenticated: true,
          user: UserModel.fromJson(userJson),
          business: BusinessModel.fromJson(bizJson),
        );
      }
      // Refresh profile in background
      fetchProfile();
    }
  }

  Future<bool> login(String email, String password) async {
    state = state.copyWith(isLoading: true, errorMessage: null);
    try {
      final res = await _client.dio.post(
        ApiConstants.login,
        data: {'email': email.trim(), 'password': password},
      );
      if (res.statusCode == 200) {
        final access = res.data['tokens']['access'];
        final refresh = res.data['tokens']['refresh'];
        await LocalStorageService.saveTokens(access, refresh);

        final user = UserModel.fromJson(res.data['user']);
        final business = res.data['business'] != null
            ? BusinessModel.fromJson(res.data['business'])
            : null;

        await LocalStorageService.saveUser(user.toJson());
        if (business != null) {
          await LocalStorageService.saveBusiness(business.toJson());
        }

        state = state.copyWith(
          isLoading: false,
          isAuthenticated: true,
          user: user,
          business: business,
        );
        return true;
      }
    } catch (e) {
      String message = 'Connection error. Please try again.';
      if (e is DioException) {
        final status = e.response?.statusCode;
        final data = e.response?.data;
        if (status == 401) {
          message = (data is Map && data['error'] is String) ? data['error'] as String : 'Invalid email or password';
        } else if (data is Map && data['error'] is String) {
          message = data['error'] as String;
        } else if (e.type == DioExceptionType.connectionError || e.type == DioExceptionType.connectionTimeout) {
          message = 'Could not reach the server. Check your internet connection.';
        }
      }
      state = state.copyWith(
        isLoading: false,
        errorMessage: message,
      );
    }
    return false;
  }

  Future<bool> register({
    required String fullName,
    required String shopName,
    required String phone,
    required String email,
    required String password,
  }) async {
    state = state.copyWith(isLoading: true, errorMessage: null);
    try {
      final res = await _client.dio.post(
        ApiConstants.register,
        data: {
          'full_name': fullName.trim(),
          'shop_name': shopName.trim(),
          'phone': phone.trim(),
          'email': email.trim(),
          'password': password,
        },
      );
      if (res.statusCode == 201) {
        final access = res.data['tokens']['access'];
        final refresh = res.data['tokens']['refresh'];
        await LocalStorageService.saveTokens(access, refresh);

        final user = UserModel.fromJson(res.data['user']);
        final business = BusinessModel.fromJson(res.data['business']);

        await LocalStorageService.saveUser(user.toJson());
        await LocalStorageService.saveBusiness(business.toJson());

        state = state.copyWith(
          isLoading: false,
          isAuthenticated: true,
          user: user,
          business: business,
        );
        return true;
      }
    } catch (e) {
      // Show the server's own message (e.g. duplicate email, weak password)
      // when available; only fall back to a generic message on network errors.
      String message = 'Could not reach the server. Check your internet connection and try again.';
      if (e is DioException) {
        final data = e.response?.data;
        if (data is Map && data['error'] is String && (data['error'] as String).isNotEmpty) {
          message = data['error'] as String;
        }
      }
      state = state.copyWith(
        isLoading: false,
        errorMessage: message,
      );
    }
    return false;
  }

  Future<void> fetchProfile() async {
    try {
      final res = await _client.dio.get(ApiConstants.profile);
      if (res.statusCode == 200) {
        final user = UserModel.fromJson(res.data['user']);
        final business = res.data['business'] != null
            ? BusinessModel.fromJson(res.data['business'])
            : null;
        state = state.copyWith(user: user, business: business);
      }
    } catch (_) {}
  }

  Future<void> logout() async {
    await LocalStorageService.clearAuth();
    state = AuthState();
  }
}

final authProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  final client = ref.watch(apiClientProvider);
  return AuthNotifier(client);
});
