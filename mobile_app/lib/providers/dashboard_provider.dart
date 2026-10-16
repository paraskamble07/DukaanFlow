import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../core/constants/api_constants.dart';
import '../models/dashboard_model.dart';
import 'auth_provider.dart';

/// Last successfully fetched dashboard snapshot (Phase 9 — offline mode).
/// Written by [dashboardProvider] on every successful load and rendered by the
/// dashboard screen when a refresh fails because the device is offline.
/// autoDispose: it is cleared as soon as the dashboard stops watching, so one
/// shop's numbers can never leak into a new session after logout.
final lastDashboardSnapshotProvider =
    StateProvider.autoDispose<DashboardModel?>((ref) => null);

final dashboardProvider = FutureProvider.autoDispose<DashboardModel>((ref) async {
  final client = ref.watch(apiClientProvider);
  final res = await client.dio.get(ApiConstants.dashboard);
  if (res.statusCode == 200) {
    final model = DashboardModel.fromJson(res.data);
    // Keep the offline cache fresh with every successful fetch.
    ref.read(lastDashboardSnapshotProvider.notifier).state = model;
    return model;
  }
  throw Exception('Failed to load dashboard statistics');
});
