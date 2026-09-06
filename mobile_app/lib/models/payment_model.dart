class PaymentModel {
  final int id;
  final String paymentType;
  final String paymentTypeDisplay;
  final int? customerId;
  final String? customerName;
  final int? supplierId;
  final String? supplierName;
  final double amount;
  final String paymentMethod;
  final String paymentMethodDisplay;
  final String paymentDate;
  final String? referenceNumber;
  final String? notes;

  PaymentModel({
    required this.id,
    required this.paymentType,
    required this.paymentTypeDisplay,
    this.customerId,
    this.customerName,
    this.supplierId,
    this.supplierName,
    required this.amount,
    required this.paymentMethod,
    required this.paymentMethodDisplay,
    required this.paymentDate,
    this.referenceNumber,
    this.notes,
  });

  factory PaymentModel.fromJson(Map<String, dynamic> json) {
    return PaymentModel(
      id: json['id'] ?? 0,
      paymentType: json['payment_type'] ?? 'CUSTOMER_PAYMENT',
      paymentTypeDisplay: json['payment_type_display'] ?? '',
      customerId: json['customer'],
      customerName: json['customer_name'],
      supplierId: json['supplier'],
      supplierName: json['supplier_name'],
      amount: double.tryParse(json['amount']?.toString() ?? '0') ?? 0.0,
      paymentMethod: json['payment_method'] ?? 'CASH',
      paymentMethodDisplay: json['payment_method_display'] ?? 'Cash',
      paymentDate: json['payment_date'] ?? '',
      referenceNumber: json['reference_number'],
      notes: json['notes'],
    );
  }
}
