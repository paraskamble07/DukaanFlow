import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../core/constants/api_constants.dart';
import '../models/product_model.dart';
import 'auth_provider.dart';

class ProductFilterState {
  final String query;
  final int? categoryId;
  final String? stockStatus;

  ProductFilterState({this.query = '', this.categoryId, this.stockStatus});

  ProductFilterState copyWith({String? query, int? categoryId, String? stockStatus}) {
    return ProductFilterState(
      query: query ?? this.query,
      categoryId: categoryId ?? this.categoryId,
      stockStatus: stockStatus ?? this.stockStatus,
    );
  }
}

final productFilterProvider = StateProvider<ProductFilterState>((ref) => ProductFilterState());

final productsListProvider = FutureProvider.autoDispose<List<ProductModel>>((ref) async {
  final client = ref.watch(apiClientProvider);
  final filter = ref.watch(productFilterProvider);

  final queryParams = <String, dynamic>{};
  if (filter.query.isNotEmpty) queryParams['q'] = filter.query;
  if (filter.categoryId != null) queryParams['category'] = filter.categoryId;
  if (filter.stockStatus != null) queryParams['stock'] = filter.stockStatus;

  final res = await client.dio.get(
    ApiConstants.products,
    queryParameters: queryParams,
  );

  if (res.statusCode == 200) {
    final list = (res.data is List ? res.data : (res.data['results'] ?? [])) as List<dynamic>;
    return list.map((i) => ProductModel.fromJson(i)).toList();
  }
  return [];
});

final categoriesProvider = FutureProvider.autoDispose<List<Map<String, dynamic>>>((ref) async {
  final client = ref.watch(apiClientProvider);
  final res = await client.dio.get(ApiConstants.categories);
  if (res.statusCode == 200) {
    final list = (res.data is List ? res.data : (res.data['results'] ?? [])) as List<dynamic>;
    return list.map((i) => i as Map<String, dynamic>).toList();
  }
  return [];
});
