import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/constants/api_constants.dart';
import '../core/network/api_client.dart';
import 'auth_provider.dart';

/// One row of the authoritative server-side due list.
class DueCustomer {
  final int customerId;
  final String name;
  final String phone;
  final String outstanding; // server recomputed; string keeps decimals exact
  final String? dueDate;
  final String status; // OVERDUE | DUE_SOON | DUE
  final String? lastChannel;
  final String? lastAt;
  final int reminderCount;
  final String whatsappUrl;
  final String smsBody;

  DueCustomer({
    required this.customerId,
    required this.name,
    required this.phone,
    required this.outstanding,
    this.dueDate,
    required this.status,
    this.lastChannel,
    this.lastAt,
    required this.reminderCount,
    required this.whatsappUrl,
    required this.smsBody,
  });

  factory DueCustomer.fromJson(Map<String, dynamic> json, {String? whatsappUrl, String? smsBody}) {
    final last = json['last_reminder'] as Map<String, dynamic>?;
    return DueCustomer(
      customerId: json['customer_id'] as int,
      name: json['name'] as String,
      phone: json['phone'] as String? ?? '',
      outstanding: (json['outstanding'] ?? '0').toString(),
      dueDate: json['due_date'] as String?,
      status: json['status'] as String? ?? 'DUE',
      lastChannel: last?['channel'] as String?,
      lastAt: last?['at'] as String?,
      reminderCount: (json['reminder_count'] ?? 0) as int,
      whatsappUrl: whatsappUrl ?? '',
      smsBody: smsBody ?? '',
    );
  }
}

class ReminderListState {
  final bool isLoading;
  final List<DueCustomer> dueList;
  final int creditDays;
  final String? error;

  ReminderListState({
    this.isLoading = false,
    this.dueList = const [],
    this.creditDays = 30,
    this.error,
  });

  ReminderListState copyWith({
    bool? isLoading,
    List<DueCustomer>? dueList,
    int? creditDays,
    String? error,
  }) {
    return ReminderListState(
      isLoading: isLoading ?? this.isLoading,
      dueList: dueList ?? this.dueList,
      creditDays: creditDays ?? this.creditDays,
      error: error,
    );
  }
}

class ReminderNotifier extends StateNotifier<ReminderListState> {
  final ApiClient _client;

  ReminderNotifier(this._client) : super(ReminderListState()) {
    load();
  }

  Future<void> load() async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final res = await _client.dio.get(ApiConstants.remindersDueList);
      final list = (res.data['results'] as List).map<DueCustomer>((row) {
        final json = row as Map<String, dynamic>;
        return DueCustomer.fromJson(
          json,
          whatsappUrl: json['whatsapp_url'] as String? ?? '',
          smsBody: json['sms_body'] as String? ?? '',
        );
      }).toList();
      state = ReminderListState(
        isLoading: false,
        dueList: list,
        creditDays: res.data['credit_days'] ?? 30,
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: 'Could not load due customers. Check your connection.',
      );
    }
  }
}

final reminderProvider =
    StateNotifierProvider<ReminderNotifier, ReminderListState>((ref) {
  return ReminderNotifier(ref.read(apiClientProvider));
});

/// Reminder history (most recent 100 for the shop).
final reminderHistoryProvider =
    FutureProvider.autoDispose<List<Map<String, dynamic>>>((ref) async {
  final client = ref.watch(apiClientProvider);
  final res = await client.dio.get(ApiConstants.remindersHistory);
  final data = res.data;
  if (data is Map && data['results'] is List) {
    return (data['results'] as List).cast<Map<String, dynamic>>();
  }
  return [];
});
