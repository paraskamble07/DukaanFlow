class BusinessModel {
  final int id;
  final String name;
  final String ownerName;
  final String phone;
  final String email;
  final String? address;
  final String? city;
  final String? state;
  final String? pincode;
  final String? gstin;
  final String? logoUrl;
  final String invoicePrefix;
  final String invoiceFooter;
  final String planTier;
  final Map<String, dynamic>? planInfo;

  BusinessModel({
    required this.id,
    required this.name,
    required this.ownerName,
    required this.phone,
    required this.email,
    this.address,
    this.city,
    this.state,
    this.pincode,
    this.gstin,
    this.logoUrl,
    required this.invoicePrefix,
    required this.invoiceFooter,
    required this.planTier,
    this.planInfo,
  });

  factory BusinessModel.fromJson(Map<String, dynamic> json) {
    return BusinessModel(
      id: json['id'] ?? 0,
      name: json['name'] ?? '',
      ownerName: json['owner_name'] ?? '',
      phone: json['phone'] ?? '',
      email: json['email'] ?? '',
      address: json['address'],
      city: json['city'],
      state: json['state'],
      pincode: json['pincode'],
      gstin: json['gstin'],
      logoUrl: json['logo_url'],
      invoicePrefix: json['invoice_prefix'] ?? 'INV-',
      invoiceFooter: json['invoice_footer'] ?? '',
      planTier: json['plan_tier'] ?? 'FREE',
      planInfo: json['plan_info'] as Map<String, dynamic>?,
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'name': name,
    'owner_name': ownerName,
    'phone': phone,
    'email': email,
    'address': address,
    'city': city,
    'state': state,
    'pincode': pincode,
    'gstin': gstin,
    'logo_url': logoUrl,
    'invoice_prefix': invoicePrefix,
    'invoice_footer': invoiceFooter,
    'plan_tier': planTier,
    'plan_info': planInfo,
  };
}
