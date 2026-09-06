class UserModel {
  final int id;
  final String username;
  final String email;
  final String firstName;
  final String lastName;
  final String? phone;
  final String role;
  final bool isShopZenAdmin;

  UserModel({
    required this.id,
    required this.username,
    required this.email,
    required this.firstName,
    required this.lastName,
    this.phone,
    required this.role,
    this.isShopZenAdmin = false,
  });

  factory UserModel.fromJson(Map<String, dynamic> json) {
    final profile = json['profile'] as Map<String, dynamic>?;
    return UserModel(
      id: json['id'] ?? 0,
      username: json['username'] ?? '',
      email: json['email'] ?? '',
      firstName: json['first_name'] ?? '',
      lastName: json['last_name'] ?? '',
      phone: profile?['phone'],
      role: profile?['role'] ?? 'OWNER',
      // Navigation hint only; the backend re-checks on every admin API call.
      isShopZenAdmin: json['is_shopzen_admin'] == true,
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'username': username,
    'email': email,
    'first_name': firstName,
    'last_name': lastName,
    'phone': phone,
    'role': role,
    'is_shopzen_admin': isShopZenAdmin,
  };
}
