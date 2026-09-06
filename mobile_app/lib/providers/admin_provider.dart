import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../core/constants/api_constants.dart';
import 'auth_provider.dart';

/// ShopZen Admin data. Every backend endpoint re-verifies the admin role
/// server-side (IsShopZenAdmin); these providers just fetch what it returns.

final adminDashboardProvider = FutureProvider.autoDispose<Map<String, dynamic>>((ref) async {
  final client = ref.watch(apiClientProvider);
  final res = await client.dio.get(ApiConstants.adminDashboard);
  if (res.data is Map<String, dynamic>) return res.data;
  throw Exception('Unexpected response');
});

/// Status filter for the payment request list: PENDING / APPROVED / REJECTED.
final adminPayStatusProvider = StateProvider<String>((ref) => 'PENDING');

final adminPaymentRequestsProvider =
    FutureProvider.autoDispose<List<Map<String, dynamic>>>((ref) async {
  final client = ref.watch(apiClientProvider);
  final status = ref.watch(adminPayStatusProvider);
  final q = ref.watch(adminPaySearchProvider);
  final res = await client.dio.get(
    ApiConstants.adminPaymentRequests,
    queryParameters: {
      'status': status,
      if (q.isNotEmpty) 'q': q,
    },
  );
  // Server wraps the list in {'requests': [...]}
  final data = res.data;
  if (data is Map && data['requests'] is List) {
    return (data['requests'] as List).cast<Map<String, dynamic>>();
  }
  if (data is List) return data.cast<Map<String, dynamic>>();
  return [];
});

/// UTR search across payment requests (server-side q search).
final adminPaySearchProvider = StateProvider<String>((ref) => '');
