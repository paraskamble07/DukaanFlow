double _num(dynamic v) {
  if (v == null) return 0.0;
  if (v is num) return v.toDouble();
  return double.tryParse(v.toString()) ?? 0.0;
}

/// One restock line of a product's purchase history (Phase 11). Amounts
/// are the server's own computed values — never recalculated by the app.
class ProductPurchaseModel {
  final int id;
  final String? invoiceNumber;
  final String? supplierName;
  final String? purchaseDate;
  final int quantity;
  final double unitCost;
  final double totalCost;

  ProductPurchaseModel({
    required this.id,
    this.invoiceNumber,
    this.supplierName,
    this.purchaseDate,
    required this.quantity,
    required this.unitCost,
    required this.totalCost,
  });

  factory ProductPurchaseModel.fromJson(Map<String, dynamic> json) {
    return ProductPurchaseModel(
      id: json['id'] ?? 0,
      invoiceNumber: json['invoice_number'],
      supplierName: json['supplier_name'],
      purchaseDate: json['purchase_date'],
      quantity: json['quantity'] ?? 0,
      unitCost: (json['unit_cost'] as num?)?.toDouble() ?? 0.0,
      totalCost: (json['total_cost'] as num?)?.toDouble() ?? 0.0,
    );
  }
}

class PurchaseLineItemModel {
  final int id;
  final int? productId;
  final String productName;
  final int quantity;
  final double unitCost;
  final double totalCost;

  PurchaseLineItemModel({
    required this.id,
    this.productId,
    required this.productName,
    required this.quantity,
    required this.unitCost,
    required this.totalCost,
  });

  factory PurchaseLineItemModel.fromJson(Map<String, dynamic> json) {
    return PurchaseLineItemModel(
      id: json['id'] ?? 0,
      productId: json['product'],
      productName: json['product_name'] ?? '',
      quantity: json['quantity'] ?? 0,
      // DRF emits DecimalField as a string ("11000.00").
      unitCost: _num(json['unit_cost']),
      totalCost: _num(json['total_cost']),
    );
  }
}

class PurchaseModel {
  final int id;
  final int? supplierId;
  final String? supplierName;
  final String invoiceNumber;
  final String purchaseDate;
  final double totalAmount;
  final double paidAmount;
  final double dueAmount;
  final String paymentMethod;
  final String? notes;
  final List<PurchaseLineItemModel> items;

  PurchaseModel({
    required this.id,
    this.supplierId,
    this.supplierName,
    required this.invoiceNumber,
    required this.purchaseDate,
    required this.totalAmount,
    required this.paidAmount,
    required this.dueAmount,
    required this.paymentMethod,
    this.notes,
    required this.items,
  });

  factory PurchaseModel.fromJson(Map<String, dynamic> json) {
    return PurchaseModel(
      id: json['id'] ?? 0,
      supplierId: json['supplier'],
      supplierName: json['supplier_name'],
      invoiceNumber: json['invoice_number'] ?? '',
      purchaseDate: json['purchase_date'] ?? '',
      totalAmount: _num(json['total_amount']),
      paidAmount: _num(json['paid_amount']),
      dueAmount: _num(json['due_amount']),
      paymentMethod: json['payment_method'] ?? 'CASH',
      notes: json['notes'],
      items: ((json['items'] as List<dynamic>?) ?? const [])
          .map((i) => PurchaseLineItemModel.fromJson(i as Map<String, dynamic>))
          .toList(),
    );
  }
}
