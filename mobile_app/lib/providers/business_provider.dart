import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../core/constants/api_constants.dart';
import '../models/expense_model.dart';
import '../models/sale_model.dart';
import '../models/supplier_model.dart';
import 'auth_provider.dart';

// ---------------------------------------------------------------
// Expenses
// ---------------------------------------------------------------
final expenseSearchProvider = StateProvider<String>((ref) => '');

final expenseListProvider = FutureProvider.autoDispose<List<ExpenseModel>>((ref) async {
  final client = ref.watch(apiClientProvider);
  final res = await client.dio.get(ApiConstants.expenses);
  if (res.statusCode == 200) {
    final list = (res.data is List ? res.data : (res.data['results'] ?? [])) as List<dynamic>;
    return list.map((i) => ExpenseModel.fromJson(i)).toList();
  }
  return [];
});

final expenseCategoriesProvider = FutureProvider.autoDispose<List<Map<String, dynamic>>>((ref) async {
  final client = ref.watch(apiClientProvider);
  final res = await client.dio.get(ApiConstants.expenseCategories);
  if (res.statusCode == 200) {
    final list = (res.data is List ? res.data : (res.data['results'] ?? [])) as List<dynamic>;
    return list.map((i) => i as Map<String, dynamic>).toList();
  }
  return [];
});

// ---------------------------------------------------------------
// Suppliers
// ---------------------------------------------------------------
final supplierSearchProvider = StateProvider<String>((ref) => '');

final supplierListProvider = FutureProvider.autoDispose<List<SupplierModel>>((ref) async {
  final client = ref.watch(apiClientProvider);
  final res = await client.dio.get(ApiConstants.suppliers);
  if (res.statusCode == 200) {
    final list = (res.data is List ? res.data : (res.data['results'] ?? [])) as List<dynamic>;
    return list.map((i) => SupplierModel.fromJson(i)).toList();
  }
  return [];
});

// ---------------------------------------------------------------
// Purchases
// ---------------------------------------------------------------
final purchaseListProvider = FutureProvider.autoDispose<List<Map<String, dynamic>>>((ref) async {
  final client = ref.watch(apiClientProvider);
  final res = await client.dio.get(ApiConstants.purchases);
  if (res.statusCode == 200) {
    final list = (res.data is List ? res.data : (res.data['results'] ?? [])) as List<dynamic>;
    return list.map((i) => i as Map<String, dynamic>).toList();
  }
  return [];
});

// ---------------------------------------------------------------
// Sales history (with status filter + search)
// ---------------------------------------------------------------
final saleStatusFilterProvider = StateProvider<String>((ref) => '');
final saleSearchQueryProvider = StateProvider<String>((ref) => '');

final salesListProvider = FutureProvider.autoDispose<List<SaleModel>>((ref) async {
  final client = ref.watch(apiClientProvider);
  final status = ref.watch(saleStatusFilterProvider);
  final q = ref.watch(saleSearchQueryProvider);

  final queryParams = <String, dynamic>{};
  if (status.isNotEmpty) queryParams['status'] = status;
  if (q.isNotEmpty) queryParams['q'] = q;

  final res = await client.dio.get(ApiConstants.sales, queryParameters: queryParams);
  if (res.statusCode == 200) {
    final list = (res.data is List ? res.data : (res.data['results'] ?? [])) as List<dynamic>;
    return list.map((i) => SaleModel.fromJson(i)).toList();
  }
  return [];
});

final saleDetailProvider = FutureProvider.autoDispose.family<SaleModel, int>((ref, saleId) async {
  final client = ref.watch(apiClientProvider);
  final res = await client.dio.get(ApiConstants.saleDetail(saleId));
  if (res.statusCode == 200) {
    return SaleModel.fromJson(res.data);
  }
  throw Exception('Failed to load sale details');
});

// ---------------------------------------------------------------
// Subscription (ShopZen Premium ₹30/month)
// ---------------------------------------------------------------
final subscriptionProvider = FutureProvider.autoDispose<Map<String, dynamic>>((ref) async {
  final client = ref.watch(apiClientProvider);
  final res = await client.dio.get(ApiConstants.subscriptionStatus);
  if (res.statusCode == 200) {
    return res.data as Map<String, dynamic>;
  }
  throw Exception('Failed to load subscription status');
});

// Payment config (QR image URL, UPI id, price) for the Premium screen.
final paymentConfigProvider = FutureProvider.autoDispose<Map<String, dynamic>>((ref) async {
  final client = ref.watch(apiClientProvider);
  final res = await client.dio.get(ApiConstants.subscriptionPaymentConfig);
  if (res.statusCode == 200) {
    return res.data as Map<String, dynamic>;
  }
  throw Exception('Failed to load payment config');
});

// Owner's own payment requests (pending history + rejection reasons).
final myPaymentRequestsProvider = FutureProvider.autoDispose<Map<String, dynamic>>((ref) async {
  final client = ref.watch(apiClientProvider);
  final res = await client.dio.get(ApiConstants.subscriptionMyRequests);
  if (res.statusCode == 200) {
    return res.data as Map<String, dynamic>;
  }
  throw Exception('Failed to load payment requests');
});

// ---------------------------------------------------------------
// Reports (all tenant-scoped, server-calculated)
// ---------------------------------------------------------------
final reportPeriodProvider = StateProvider<String>((ref) => 'this_month');

final profitLossReportProvider = FutureProvider.autoDispose<Map<String, dynamic>>((ref) async {
  final client = ref.watch(apiClientProvider);
  final period = ref.watch(reportPeriodProvider);
  final res = await client.dio.get(ApiConstants.reportProfitLoss, queryParameters: {'period': period});
  if (res.statusCode == 200) return res.data as Map<String, dynamic>;
  throw Exception('Failed to load profit & loss report');
});

final salesReportProvider = FutureProvider.autoDispose<Map<String, dynamic>>((ref) async {
  final client = ref.watch(apiClientProvider);
  final period = ref.watch(reportPeriodProvider);
  final res = await client.dio.get(ApiConstants.reportSales, queryParameters: {'period': period});
  if (res.statusCode == 200) return res.data as Map<String, dynamic>;
  throw Exception('Failed to load sales report');
});

final stockReportProvider = FutureProvider.autoDispose<Map<String, dynamic>>((ref) async {
  final client = ref.watch(apiClientProvider);
  final res = await client.dio.get(ApiConstants.reportStock);
  if (res.statusCode == 200) return res.data as Map<String, dynamic>;
  throw Exception('Failed to load stock report');
});

final khataReportProvider = FutureProvider.autoDispose<Map<String, dynamic>>((ref) async {
  final client = ref.watch(apiClientProvider);
  final res = await client.dio.get(ApiConstants.reportKhata);
  if (res.statusCode == 200) return res.data as Map<String, dynamic>;
  throw Exception('Failed to load khata report');
});

final expenseReportProvider = FutureProvider.autoDispose<Map<String, dynamic>>((ref) async {
  final client = ref.watch(apiClientProvider);
  final period = ref.watch(reportPeriodProvider);
  final res = await client.dio.get(ApiConstants.reportExpenses, queryParameters: {'period': period});
  if (res.statusCode == 200) return res.data as Map<String, dynamic>;
  throw Exception('Failed to load expense report');
});

final gstReportProvider = FutureProvider.autoDispose<Map<String, dynamic>>((ref) async {
  final client = ref.watch(apiClientProvider);
  final period = ref.watch(reportPeriodProvider);
  final res = await client.dio.get(ApiConstants.reportGst, queryParameters: {'period': period});
  if (res.statusCode == 200) return res.data as Map<String, dynamic>;
  throw Exception('Failed to load GST report');
});

final topProductsReportProvider = FutureProvider.autoDispose<Map<String, dynamic>>((ref) async {
  final client = ref.watch(apiClientProvider);
  final period = ref.watch(reportPeriodProvider);
  final res = await client.dio.get(ApiConstants.reportTopProducts, queryParameters: {'period': period});
  if (res.statusCode == 200) return res.data as Map<String, dynamic>;
  throw Exception('Failed to load top products');
});

final topCustomersReportProvider = FutureProvider.autoDispose<Map<String, dynamic>>((ref) async {
  final client = ref.watch(apiClientProvider);
  final period = ref.watch(reportPeriodProvider);
  final res = await client.dio.get(ApiConstants.reportTopCustomers, queryParameters: {'period': period});
  if (res.statusCode == 200) return res.data as Map<String, dynamic>;
  throw Exception('Failed to load top customers');
});
