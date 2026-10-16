import 'device_model.dart';
import 'product_model.dart';
import 'purchase_model.dart';
import 'stock_movement_model.dart';

/// Enriched product payload from `GET /api/products/<id>/` (Phase 11): the
/// product row itself plus its stock movements, purchase history, registered
/// IMEI units and the server's dead-stock verdict.
class ProductDetailData {
  final ProductModel product;
  final List<StockMovementModel> movements;
  final List<ProductPurchaseModel> purchaseHistory;
  final List<DeviceModel> devices;
  final String? lastSaleDate;
  final bool isDeadStock;

  ProductDetailData({
    required this.product,
    required this.movements,
    required this.purchaseHistory,
    required this.devices,
    this.lastSaleDate,
    this.isDeadStock = false,
  });

  factory ProductDetailData.fromJson(Map<String, dynamic> json) {
    return ProductDetailData(
      product: ProductModel.fromJson(json),
      movements: ((json['movements'] as List<dynamic>?) ?? const [])
          .map((m) => StockMovementModel.fromJson(m as Map<String, dynamic>))
          .toList(),
      purchaseHistory: ((json['purchase_history'] as List<dynamic>?) ?? const [])
          .map((p) => ProductPurchaseModel.fromJson(p as Map<String, dynamic>))
          .toList(),
      devices: ((json['devices'] as List<dynamic>?) ?? const [])
          .map((d) => DeviceModel.fromJson(d as Map<String, dynamic>))
          .toList(),
      lastSaleDate: json['last_sale_date']?.toString(),
      isDeadStock: json['is_dead_stock'] ?? false,
    );
  }
}
