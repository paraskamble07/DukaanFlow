/// A staff login of the shop. Grants live on `permissions`; every module
/// gate is re-enforced by the backend per request, so this model is only a
/// reflection for the owner to manage their team.
class StaffModel {
  final int id;
  final String email;
  final String firstName;
  final String? phone;
  final List<String> permissions;
  final bool isActive;
  final DateTime createdAt;

  StaffModel({
    required this.id,
    required this.email,
    this.firstName = '',
    this.phone,
    this.permissions = const [],
    this.isActive = true,
    required this.createdAt,
  });

  factory StaffModel.fromJson(Map<String, dynamic> json) {
    return StaffModel(
      id: json['id'] ?? 0,
      email: json['email'] ?? '',
      firstName: (json['first_name'] ?? '').toString(),
      phone: json['phone']?.toString(),
      permissions: (json['permissions'] as List<dynamic>?)
              ?.map((p) => p.toString())
              .toList() ??
          const [],
      isActive: json['is_active'] ?? true,
      createdAt: DateTime.tryParse(json['created_at'] ?? '') ?? DateTime.now(),
    );
  }
}
