import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../core/constants/api_constants.dart';
import '../models/customer_model.dart';
import 'auth_provider.dart';

final customerSearchProvider = StateProvider<String>((ref) => '');
final customerDueFilterProvider = StateProvider<String>((ref) => '');

final customerListProvider = FutureProvider.autoDispose<List<CustomerModel>>((ref) async {
  final client = ref.watch(apiClientProvider);
  final q = ref.watch(customerSearchProvider);
  final due = ref.watch(customerDueFilterProvider);

  final queryParams = <String, dynamic>{};
  if (q.isNotEmpty) queryParams['q'] = q;
  if (due.isNotEmpty) queryParams['due'] = due;

  final res = await client.dio.get(ApiConstants.customers, queryParameters: queryParams);
  if (res.statusCode == 200) {
    final list = (res.data is List ? res.data : (res.data['results'] ?? [])) as List<dynamic>;
    return list.map((i) => CustomerModel.fromJson(i)).toList();
  }
  return [];
});

final customerLedgerProvider = FutureProvider.autoDispose.family<Map<String, dynamic>, int>((ref, customerId) async {
  final client = ref.watch(apiClientProvider);
  final res = await client.dio.get(ApiConstants.customerLedger(customerId));
  if (res.statusCode == 200) {
    return res.data as Map<String, dynamic>;
  }
  throw Exception('Failed to load customer ledger');
});
