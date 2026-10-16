import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../constants/api_constants.dart';
import '../network/api_client.dart';
import '../storage/local_storage.dart';
import '../../providers/auth_provider.dart';
import 'offline_sync_service.dart';

/// Server-reachability + queued-bill state shown to the user.
///
/// `isOnline` means the **ShopZen server is reachable** — not merely that
/// the radio is on — because an app behind a captive portal or a flaky
/// public Wi-Fi has a network but no backend. Connectivity is therefore
/// measured with a lightweight authenticated-free GET to `/api/health/`.
class SyncStatus {
  final bool isOnline;
  final bool isSyncing;
  final int pendingCount;
  final DateTime? lastSyncedAt;

  const SyncStatus({
    this.isOnline = false,
    this.isSyncing = false,
    this.pendingCount = 0,
    this.lastSyncedAt,
  });

  bool get hasPending => pendingCount > 0;

  SyncStatus copyWith({
    bool? isOnline,
    bool? isSyncing,
    int? pendingCount,
    DateTime? lastSyncedAt,
  }) {
    return SyncStatus(
      isOnline: isOnline ?? this.isOnline,
      isSyncing: isSyncing ?? this.isSyncing,
      pendingCount: pendingCount ?? this.pendingCount,
      lastSyncedAt: lastSyncedAt ?? this.lastSyncedAt,
    );
  }
}

class SyncStatusNotifier extends StateNotifier<SyncStatus> {
  final ApiClient _client;
  Timer? _timer;

  static const _checkInterval = Duration(seconds: 15);
  static const _pingTimeout = Duration(seconds: 5);

  SyncStatusNotifier(this._client) : super(const SyncStatus());

  /// Starts the periodic check. Safe to call repeatedly; the timer is
  /// only ever created once. `stop()` cancels it (e.g. on logout) and a
  /// later `start()` revives it.
  void start() {
    if (_timer != null) return;
    _timer = Timer.periodic(_checkInterval, (_) => refresh());
    refresh();
  }

  void stop() {
    _timer?.cancel();
    _timer = null;
  }

  /// One full check: recount the offline queue, probe the server, and
  /// push any queued bills when it answers.
  Future<void> refresh() async {
    if (_timer == null) return; // stopped (logged out)
    final queue = await LocalStorageService.getOfflineSalesQueue();
    final online = await _serverReachable();
    if (!mounted) return;

    if (!online) {
      state = state.copyWith(
        isOnline: false,
        isSyncing: false,
        pendingCount: queue.length,
      );
      return;
    }

    if (queue.isNotEmpty) {
      if (state.isSyncing) {
        state = state.copyWith(isOnline: true, pendingCount: queue.length);
        return;
      }
      state = state.copyWith(
        isOnline: true,
        isSyncing: true,
        pendingCount: queue.length,
      );
      // OfflineSyncService.syncNow is guarded against re-entrancy itself,
      // and drops bills the server rejects (stale stock, etc.).
      await OfflineSyncService.syncNow(_client);
      final remaining = await LocalStorageService.getOfflineSalesQueue();
      if (!mounted) return;
      state = SyncStatus(
        isOnline: true,
        isSyncing: false,
        pendingCount: remaining.length,
        lastSyncedAt: remaining.isEmpty
            ? DateTime.now()
            : (state.lastSyncedAt ?? DateTime.now()),
      );
    } else {
      state = SyncStatus(
        isOnline: true,
        isSyncing: false,
        pendingCount: 0,
        lastSyncedAt: state.lastSyncedAt ?? DateTime.now(),
      );
    }
  }

  Future<bool> _serverReachable() async {
    try {
      final res = await _client.dio.get(
        ApiConstants.health,
        options: Options(receiveTimeout: _pingTimeout, sendTimeout: _pingTimeout),
      );
      return res.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  @override
  void dispose() {
    stop();
    super.dispose();
  }
}

final syncStatusProvider =
    StateNotifierProvider<SyncStatusNotifier, SyncStatus>((ref) {
  return SyncStatusNotifier(ref.read(apiClientProvider));
});
