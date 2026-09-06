import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../core/constants/api_constants.dart';
import '../models/dashboard_model.dart';
import 'auth_provider.dart';

final dashboardProvider = FutureProvider.autoDispose<DashboardModel>((ref) async {
  final client = ref.watch(apiClientProvider);
  final res = await client.dio.get(ApiConstants.dashboard);
  if (res.statusCode == 200) {
    return DashboardModel.fromJson(res.data);
  }
  throw Exception('Failed to load dashboard statistics');
});
