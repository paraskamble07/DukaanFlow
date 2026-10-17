import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/constants/api_constants.dart';
import '../models/staff_model.dart';
import 'auth_provider.dart';

final staffListProvider =
    FutureProvider.autoDispose<List<StaffModel>>((ref) async {
  final client = ref.watch(apiClientProvider);
  final res = await client.dio.get(ApiConstants.staff);
  if (res.statusCode == 200) {
    final results = res.data['results'] as List<dynamic>? ?? [];
    return results
        .map((m) => StaffModel.fromJson(m as Map<String, dynamic>))
        .toList();
  }
  return [];
});

/// The modules the backend allows granting (from the same response).
final allowedModulesProvider =
    FutureProvider.autoDispose<List<String>>((ref) async {
  final client = ref.watch(apiClientProvider);
  final res = await client.dio.get(ApiConstants.staff);
  if (res.statusCode == 200) {
    final modules = res.data['allowed_modules'] as List<dynamic>? ?? [];
    return modules.map((m) => m.toString()).toList();
  }
  return const ['sales', 'customers', 'payments', 'products', 'inventory'];
});

class StaffEditResult {
  final bool success;
  final String message;
  StaffEditResult(this.success, this.message);
}

/// Create / re-grant / deactivate staff. Errors surface as messages the UI
/// shows directly (e.g. duplicate email, short password).
Future<StaffEditResult> createStaff(
  WidgetRef ref, {
  required String email,
  required String password,
  required String firstName,
  required String phone,
  required List<String> permissions,
}) async {
  try {
    final client = ref.read(apiClientProvider);
    final res = await client.dio.post(ApiConstants.staff, data: {
      'email': email,
      'password': password,
      'first_name': firstName,
      'phone': phone,
      'permissions': permissions,
    });
    if (res.statusCode == 201) {
      ref.invalidate(staffListProvider);
      return StaffEditResult(true, 'Staff member added.');
    }
    return StaffEditResult(false, 'Could not add the staff member.');
  } catch (e) {
    return StaffEditResult(false, _explain(e, 'Could not add the staff member.'));
  }
}

Future<StaffEditResult> updateStaffGrants(
  WidgetRef ref,
  int staffId,
  List<String> permissions,
) async {
  try {
    final client = ref.read(apiClientProvider);
    final res = await client.dio.patch(
      ApiConstants.staffDetail(staffId),
      data: {'permissions': permissions},
    );
    if (res.statusCode == 200) {
      ref.invalidate(staffListProvider);
      return StaffEditResult(true, 'Access updated.');
    }
    return StaffEditResult(false, 'Could not update access.');
  } catch (e) {
    return StaffEditResult(false, _explain(e, 'Could not update access.'));
  }
}

Future<StaffEditResult> toggleStaffActive(
  WidgetRef ref,
  int staffId,
  bool reactivate,
) async {
  try {
    final client = ref.read(apiClientProvider);
    if (reactivate) {
      final res = await client.dio.patch(
        ApiConstants.staffDetail(staffId),
        data: {'reactivate': true},
      );
      if (res.statusCode == 200) {
        ref.invalidate(staffListProvider);
        return StaffEditResult(true, 'Login re-enabled.');
      }
    } else {
      final res = await client.dio.delete(ApiConstants.staffDetail(staffId));
      if (res.statusCode == 200) {
        ref.invalidate(staffListProvider);
        return StaffEditResult(true, 'Login disabled. History kept.');
      }
    }
    return StaffEditResult(false, 'Could not change the login.');
  } catch (e) {
    return StaffEditResult(false, _explain(e, 'Could not change the login.'));
  }
}

String _explain(Object e, String fallback) {
  try {
    final res = (e as dynamic).response;
    final data = res?.data;
    if (data is Map && data['error'] is String) return data['error'];
  } catch (_) {}
  return fallback;
}
