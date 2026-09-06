import 'product_model.dart';
import 'sale_model.dart';

class DashboardTodayModel {
  final String date;
  final double sales;
  final int salesCount;
  final double grossProfit;
  final double netProfit;
  final double expenses;

  DashboardTodayModel({
    required this.date,
    required this.sales,
    required this.salesCount,
    required this.grossProfit,
    required this.netProfit,
    required this.expenses,
  });

  factory DashboardTodayModel.fromJson(Map<String, dynamic> json) {
    return DashboardTodayModel(
      date: json['date'] ?? '',
      sales: double.tryParse(json['sales']?.toString() ?? '0') ?? 0.0,
      salesCount: json['sales_count'] ?? 0,
      grossProfit: double.tryParse(json['gross_profit']?.toString() ?? '0') ?? 0.0,
      netProfit: double.tryParse(json['net_profit']?.toString() ?? '0') ?? 0.0,
      expenses: double.tryParse(json['expenses']?.toString() ?? '0') ?? 0.0,
    );
  }
}

class DashboardModel {
  final DashboardTodayModel today;
  final double totalReceivable;
  final double totalPayable;
  final int totalProducts;
  final int lowStockCount;
  final List<ProductModel> lowStockItems;
  final List<String> chartLabels;
  final List<double> chartSales;
  final List<double> chartExpenses;
  final List<SaleModel> recentSales;
  final List<Map<String, dynamic>> topPendingKhata;

  DashboardModel({
    required this.today,
    required this.totalReceivable,
    required this.totalPayable,
    required this.totalProducts,
    required this.lowStockCount,
    this.lowStockItems = const [],
    this.chartLabels = const [],
    this.chartSales = const [],
    this.chartExpenses = const [],
    this.recentSales = const [],
    this.topPendingKhata = const [],
  });

  factory DashboardModel.fromJson(Map<String, dynamic> json) {
    final rawLowStock = json['inventory']?['low_stock_items'] as List<dynamic>? ?? [];
    final rawRecentSales = json['recent_sales'] as List<dynamic>? ?? [];
    final rawChartSales = json['charts']?['sales'] as List<dynamic>? ?? [];
    final rawChartExpenses = json['charts']?['expenses'] as List<dynamic>? ?? [];
    final rawLabels = json['charts']?['labels'] as List<dynamic>? ?? [];
    final rawKhata = json['top_pending_khata'] as List<dynamic>? ?? [];

    return DashboardModel(
      today: DashboardTodayModel.fromJson(json['today'] ?? {}),
      totalReceivable: double.tryParse(json['receivables']?['total_receivable']?.toString() ?? '0') ?? 0.0,
      totalPayable: double.tryParse(json['receivables']?['total_payable']?.toString() ?? '0') ?? 0.0,
      totalProducts: json['inventory']?['total_products'] ?? 0,
      lowStockCount: json['inventory']?['low_stock_count'] ?? 0,
      lowStockItems: rawLowStock.map((i) => ProductModel.fromJson(i)).toList(),
      chartLabels: rawLabels.map((l) => l.toString()).toList(),
      chartSales: rawChartSales.map((s) => double.tryParse(s.toString()) ?? 0.0).toList(),
      chartExpenses: rawChartExpenses.map((e) => double.tryParse(e.toString()) ?? 0.0).toList(),
      recentSales: rawRecentSales.map((s) => SaleModel.fromJson(s)).toList(),
      topPendingKhata: rawKhata.map((k) => k as Map<String, dynamic>).toList(),
    );
  }
}
