class DeviceModel {
  final int id;
  final int productId;
  final String productName;
  final String imei1;
  final String? imei2;
  final String? serialNumber;
  final String? modelName;
  final String? brand;
  final double purchasePrice;
  final double sellingPrice;
  final String status;
  final String statusDisplay;
  final int? customerId;
  final String? customerName;
  final String? customerPhone;
  final String? saleDate;
  final String? warrantyExpiryDate;
  final String? invoiceNumber;
  final String? notes;

  DeviceModel({
    required this.id,
    required this.productId,
    required this.productName,
    required this.imei1,
    this.imei2,
    this.serialNumber,
    this.modelName,
    this.brand,
    required this.purchasePrice,
    required this.sellingPrice,
    required this.status,
    required this.statusDisplay,
    this.customerId,
    this.customerName,
    this.customerPhone,
    this.saleDate,
    this.warrantyExpiryDate,
    this.invoiceNumber,
    this.notes,
  });

  factory DeviceModel.fromJson(Map<String, dynamic> json) {
    return DeviceModel(
      id: json['id'] ?? 0,
      productId: json['product'] ?? 0,
      productName: json['product_name'] ?? '',
      imei1: json['imei_1'] ?? '',
      imei2: json['imei_2'],
      serialNumber: json['serial_number'],
      modelName: json['model_name'],
      brand: json['brand'],
      purchasePrice: double.tryParse(json['purchase_price']?.toString() ?? '0') ?? 0.0,
      sellingPrice: double.tryParse(json['selling_price']?.toString() ?? '0') ?? 0.0,
      status: json['status'] ?? 'IN_STOCK',
      statusDisplay: json['status_display'] ?? 'In Stock',
      customerId: json['customer'],
      customerName: json['customer_name'],
      customerPhone: json['customer_phone'],
      saleDate: json['sale_date'],
      warrantyExpiryDate: json['warranty_expiry_date'],
      invoiceNumber: json['invoice_number'],
      notes: json['notes'],
    );
  }
}
