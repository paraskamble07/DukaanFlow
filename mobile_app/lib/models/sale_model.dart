class SaleItemModel {
  final int id;
  final int productId;
  final String productName;
  final String? productBrand;
  final int quantity;
  final double unitPrice;
  final double discount;
  final double totalPrice;
  final String? imeiNumbers;
  final int warrantyMonths;

  SaleItemModel({
    required this.id,
    required this.productId,
    required this.productName,
    this.productBrand,
    required this.quantity,
    required this.unitPrice,
    this.discount = 0.0,
    required this.totalPrice,
    this.imeiNumbers,
    this.warrantyMonths = 0,
  });

  factory SaleItemModel.fromJson(Map<String, dynamic> json) {
    return SaleItemModel(
      id: json['id'] ?? 0,
      productId: json['product'] ?? 0,
      productName: json['product_name'] ?? '',
      productBrand: json['product_brand'],
      quantity: json['quantity'] ?? 1,
      unitPrice: double.tryParse(json['unit_price']?.toString() ?? '0') ?? 0.0,
      discount: double.tryParse(json['discount']?.toString() ?? '0') ?? 0.0,
      totalPrice: double.tryParse(json['total_price']?.toString() ?? '0') ?? 0.0,
      imeiNumbers: json['imei_numbers'],
      warrantyMonths: json['warranty_months'] ?? 0,
    );
  }
}

class SaleModel {
  final int id;
  final int customerId;
  final String customerName;
  final String customerPhone;
  final String invoiceNumber;
  final double subtotal;
  final double discount;
  final double taxAmount;
  final double totalAmount;
  final double paidAmount;
  final double dueAmount;
  final String paymentStatus;
  final String paymentStatusDisplay;
  final String paymentMethod;
  final String paymentMethodDisplay;
  final String saleDate;
  final String? notes;
  final List<SaleItemModel> items;
  final double grossProfit;

  SaleModel({
    required this.id,
    required this.customerId,
    required this.customerName,
    required this.customerPhone,
    required this.invoiceNumber,
    required this.subtotal,
    this.discount = 0.0,
    this.taxAmount = 0.0,
    required this.totalAmount,
    required this.paidAmount,
    required this.dueAmount,
    required this.paymentStatus,
    required this.paymentStatusDisplay,
    required this.paymentMethod,
    required this.paymentMethodDisplay,
    required this.saleDate,
    this.notes,
    this.items = const [],
    this.grossProfit = 0.0,
  });

  factory SaleModel.fromJson(Map<String, dynamic> json) {
    final rawItems = json['items'] as List<dynamic>? ?? [];
    return SaleModel(
      id: json['id'] ?? 0,
      customerId: json['customer'] ?? 0,
      customerName: json['customer_name'] ?? 'Walk-in Customer',
      customerPhone: json['customer_phone'] ?? '',
      invoiceNumber: json['invoice_number'] ?? '',
      subtotal: double.tryParse(json['subtotal']?.toString() ?? '0') ?? 0.0,
      discount: double.tryParse(json['discount']?.toString() ?? '0') ?? 0.0,
      taxAmount: double.tryParse(json['tax_amount']?.toString() ?? '0') ?? 0.0,
      totalAmount: double.tryParse(json['total_amount']?.toString() ?? '0') ?? 0.0,
      paidAmount: double.tryParse(json['paid_amount']?.toString() ?? '0') ?? 0.0,
      dueAmount: double.tryParse(json['due_amount']?.toString() ?? '0') ?? 0.0,
      paymentStatus: json['payment_status'] ?? 'PAID',
      paymentStatusDisplay: json['payment_status_display'] ?? 'Paid',
      paymentMethod: json['payment_method'] ?? 'CASH',
      paymentMethodDisplay: json['payment_method_display'] ?? 'Cash',
      saleDate: json['sale_date'] ?? '',
      notes: json['notes'],
      items: rawItems.map((i) => SaleItemModel.fromJson(i)).toList(),
      grossProfit: double.tryParse(json['gross_profit']?.toString() ?? '0') ?? 0.0,
    );
  }
}
