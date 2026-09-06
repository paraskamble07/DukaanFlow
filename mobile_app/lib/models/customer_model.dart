class CustomerModel {
  final int id;
  final String name;
  final String phone;
  final String? email;
  final String? address;
  final String? notes;
  final double creditLimit;
  final double totalSales;
  final double totalPaid;
  final double outstandingDue;
  final String? whatsappReminderUrl;

  CustomerModel({
    required this.id,
    required this.name,
    required this.phone,
    this.email,
    this.address,
    this.notes,
    this.creditLimit = 0.0,
    this.totalSales = 0.0,
    this.totalPaid = 0.0,
    this.outstandingDue = 0.0,
    this.whatsappReminderUrl,
  });

  factory CustomerModel.fromJson(Map<String, dynamic> json) {
    return CustomerModel(
      id: json['id'] ?? 0,
      name: json['name'] ?? '',
      phone: json['phone'] ?? '',
      email: json['email'],
      address: json['address'],
      notes: json['notes'],
      creditLimit: double.tryParse(json['credit_limit']?.toString() ?? '0') ?? 0.0,
      totalSales: double.tryParse(json['total_sales']?.toString() ?? '0') ?? 0.0,
      totalPaid: double.tryParse(json['total_paid']?.toString() ?? '0') ?? 0.0,
      outstandingDue: double.tryParse(json['outstanding_due']?.toString() ?? '0') ?? 0.0,
      whatsappReminderUrl: json['whatsapp_reminder_url'],
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'name': name,
    'phone': phone,
    'email': email,
    'address': address,
    'notes': notes,
    'credit_limit': creditLimit,
  };
}
