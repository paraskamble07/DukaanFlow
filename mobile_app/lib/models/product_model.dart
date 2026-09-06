class ProductModel {
  final int id;
  final String name;
  final String? brand;
  final int? categoryId;
  final String? categoryName;
  final String? sku;
  final String? barcode;
  final double purchasePrice;
  final double sellingPrice;
  final int stockQuantity;
  final int minStock;
  final int warrantyMonths;
  final bool isImeiTracked;
  final int? supplierId;
  final String? supplierName;
  final String? imageUrl;
  final String? description;
  final bool isLowStock;
  final bool isOutOfStock;
  final double profitMargin;

  ProductModel({
    required this.id,
    required this.name,
    this.brand,
    this.categoryId,
    this.categoryName,
    this.sku,
    this.barcode,
    required this.purchasePrice,
    required this.sellingPrice,
    required this.stockQuantity,
    this.minStock = 5,
    this.warrantyMonths = 0,
    this.isImeiTracked = false,
    this.supplierId,
    this.supplierName,
    this.imageUrl,
    this.description,
    this.isLowStock = false,
    this.isOutOfStock = false,
    this.profitMargin = 0.0,
  });

  factory ProductModel.fromJson(Map<String, dynamic> json) {
    return ProductModel(
      id: json['id'] ?? 0,
      name: json['name'] ?? '',
      brand: json['brand'],
      categoryId: json['category'],
      categoryName: json['category_name'],
      sku: json['sku'],
      barcode: json['barcode'],
      purchasePrice: double.tryParse(json['purchase_price']?.toString() ?? '0') ?? 0.0,
      sellingPrice: double.tryParse(json['selling_price']?.toString() ?? '0') ?? 0.0,
      stockQuantity: json['stock_quantity'] ?? 0,
      minStock: json['min_stock'] ?? 5,
      warrantyMonths: json['warranty_months'] ?? 0,
      isImeiTracked: json['is_imei_tracked'] ?? false,
      supplierId: json['supplier'],
      supplierName: json['supplier_name'],
      imageUrl: json['image_url'],
      description: json['description'],
      isLowStock: json['is_low_stock'] ?? false,
      isOutOfStock: json['is_out_of_stock'] ?? false,
      profitMargin: double.tryParse(json['profit_margin']?.toString() ?? '0') ?? 0.0,
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'name': name,
    'brand': brand,
    'category': categoryId,
    'category_name': categoryName,
    'sku': sku,
    'barcode': barcode,
    'purchase_price': purchasePrice,
    'selling_price': sellingPrice,
    'stock_quantity': stockQuantity,
    'min_stock': minStock,
    'warranty_months': warrantyMonths,
    'is_imei_tracked': isImeiTracked,
    'supplier': supplierId,
    'supplier_name': supplierName,
    'image_url': imageUrl,
    'description': description,
    'is_low_stock': isLowStock,
    'is_out_of_stock': isOutOfStock,
    'profit_margin': profitMargin,
  };
}
