class SupplierModel {
  final int id;
  final String companyName;
  final String name;
  final String phone;
  final String? email;
  final String? address;
  final String? gstin;
  final String? notes;
  final double totalPurchases;
  final double totalPaid;
  final double outstandingDue;

  SupplierModel({
    required this.id,
    required this.companyName,
    required this.name,
    required this.phone,
    this.email,
    this.address,
    this.gstin,
    this.notes,
    this.totalPurchases = 0.0,
    this.totalPaid = 0.0,
    this.outstandingDue = 0.0,
  });

  factory SupplierModel.fromJson(Map<String, dynamic> json) {
    return SupplierModel(
      id: json['id'] ?? 0,
      companyName: json['company_name'] ?? '',
      name: json['name'] ?? '',
      phone: json['phone'] ?? '',
      email: json['email'],
      address: json['address'],
      gstin: json['gstin'],
      notes: json['notes'],
      totalPurchases: double.tryParse(json['total_purchases']?.toString() ?? '0') ?? 0.0,
      totalPaid: double.tryParse(json['total_paid']?.toString() ?? '0') ?? 0.0,
      outstandingDue: double.tryParse(json['outstanding_due']?.toString() ?? '0') ?? 0.0,
    );
  }
}
