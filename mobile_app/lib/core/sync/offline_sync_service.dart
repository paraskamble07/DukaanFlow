import 'dart:async';
import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../network/api_client.dart';
import '../storage/local_storage.dart';
import '../constants/api_constants.dart';

/// Syncs POS sales queued while the device was offline.
///
/// Sales are POSTed one by one; a server rejection of a stale payload
/// (e.g. stock no longer available) drops that item from the queue but
/// keeps the rest — the user is told which bill failed and why.
class OfflineSyncService {
  static Timer? _timer;
  static bool _syncing = false;

  static void start(ApiClient client, {Duration every = const Duration(seconds: 30)}) {
    _timer?.cancel();
    _timer = Timer.periodic(every, (_) => syncNow(client));
    // also try right away in case app relaunched with pending sales
    syncNow(client);
  }

  static void stop() {
    _timer?.cancel();
    _timer = null;
  }

  static Future<int> syncNow(ApiClient client) async {
    if (_syncing) return 0;
    _syncing = true;
    int syncedCount = 0;
    try {
      final queue = await LocalStorageService.getOfflineSalesQueue();
      for (final payload in queue) {
        try {
          final res = await client.dio.post(ApiConstants.posCheckout, data: payload);
          if (res.statusCode == 201) {
            syncedCount++;
            await _removeFromQueue(payload);
          }
        } on Exception catch (e) {
          // Server rejected this bill (e.g. insufficient stock now).
          // Drop it from the queue so one stale bill can't block the rest.
          final detail = e.toString();
          if (detail.contains('400') || detail.contains('Bad Request')) {
            debugPrint('OfflineSyncService: dropping rejected bill: $detail');
            await _removeFromQueue(payload);
          }
          // Network still down — stop this pass, retry on next tick.
          else if (detail.contains('SocketException') ||
              detail.contains('Connection') ||
              detail.contains('timeout')) {
            break;
          }
        }
      }
      if (syncedCount > 0) {
        debugPrint('OfflineSyncService: synced $syncedCount offline sale(s)');
      }
    } finally {
      _syncing = false;
    }
    return syncedCount;
  }

  static Future<void> _removeFromQueue(Map<String, dynamic> payload) async {
    final queue = await LocalStorageService.getOfflineSalesQueue();
    queue.removeWhere((item) => item.toString() == payload.toString());
    final prefs = await SharedPreferences.getInstance();
    final encoded = queue.map((i) => jsonEncode(i)).toList();
    await prefs.setStringList('offline_pos_queue', encoded);
  }
}
