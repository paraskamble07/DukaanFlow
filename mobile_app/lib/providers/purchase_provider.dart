import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../core/constants/api_constants.dart';
import '../models/purchase_model.dart';
import 'auth_provider.dart';

/// Purchase history (Phase 11). Pass a product id to scope the list to a
/// single product; leave `productId` null for the whole shop.
final purchasesListProvider = FutureProvider.autoDispose
    .family<List<PurchaseModel>, int?>((ref, productId) async {
  final client = ref.watch(apiClientProvider);
  try {
    final res = await client.dio.get(
      ApiConstants.purchases,
      queryParameters: productId == null ? null : {'product': productId},
    );
    if (res.statusCode == 200) {
      final list =
          (res.data is List ? res.data : (res.data['results'] ?? [])) as List<dynamic>;
      return list
          .map((i) => PurchaseModel.fromJson(i as Map<String, dynamic>))
          .toList();
    }
  } catch (_) {}
  return [];
});
