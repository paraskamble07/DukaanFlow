import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/constants/api_constants.dart';
import 'auth_provider.dart';

/// One actionable notification group, e.g. "Khata payments to collect".
class NotificationGroup {
  final String id;
  final String type;
  final String title;
  final String body;
  final String severity;
  final int count;
  final double? total;
  final List<Map<String, dynamic>> items;

  NotificationGroup({
    required this.id,
    required this.type,
    required this.title,
    required this.body,
    this.severity = 'info',
    this.count = 0,
    this.total,
    this.items = const [],
  });

  factory NotificationGroup.fromJson(Map<String, dynamic> json) {
    return NotificationGroup(
      id: json['id'] ?? '',
      type: json['type'] ?? '',
      title: json['title'] ?? '',
      body: json['body'] ?? '',
      severity: json['severity'] ?? 'info',
      count: json['count'] ?? 0,
      total: (json['total'] as num?)?.toDouble(),
      items: (json['items'] as List<dynamic>?)
              ?.map((i) => i as Map<String, dynamic>)
              .toList() ??
          const [],
    );
  }
}

/// Derived, read-only attention list. Nothing is stored — every read
/// recomputes from the live books on the server.
final notificationsProvider =
    FutureProvider.autoDispose<List<NotificationGroup>>((ref) async {
  final client = ref.watch(apiClientProvider);
  final res = await client.dio.get(ApiConstants.notifications);
  if (res.statusCode == 200) {
    final results = res.data['results'] as List<dynamic>? ?? [];
    return results
        .map((m) => NotificationGroup.fromJson(m as Map<String, dynamic>))
        .toList();
  }
  return [];
});
