import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../core/constants/api_constants.dart';
import '../models/device_model.dart';
import 'auth_provider.dart';

final imeiSearchQueryProvider = StateProvider<String>((ref) => '');

final imeiDevicesListProvider = FutureProvider.autoDispose<List<DeviceModel>>((ref) async {
  final client = ref.watch(apiClientProvider);
  final q = ref.watch(imeiSearchQueryProvider);
  final queryParams = q.isNotEmpty ? {'q': q} : null;

  final res = await client.dio.get(ApiConstants.imeiDevices, queryParameters: queryParams);
  if (res.statusCode == 200) {
    final list = (res.data is List ? res.data : (res.data['results'] ?? [])) as List<dynamic>;
    return list.map((i) => DeviceModel.fromJson(i)).toList();
  }
  return [];
});

final imeiLookupProvider = FutureProvider.autoDispose.family<DeviceModel?, String>((ref, imei) async {
  if (imei.trim().isEmpty) return null;
  final client = ref.watch(apiClientProvider);
  try {
    final res = await client.dio.get(ApiConstants.imeiLookup, queryParameters: {'imei': imei.trim()});
    if (res.statusCode == 200 && res.data['found'] == true) {
      return DeviceModel.fromJson(res.data['device']);
    }
  } catch (_) {}
  return null;
});
