import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/constants/app_colors.dart';
import '../core/localization/app_localizations.dart';
import '../core/sync/sync_status_provider.dart';

/// Shows the shop's offline/sync state wherever it is mounted
/// (dashboard and POS for now).
///
/// - offline with queued bills  -> amber banner "Offline — N bill(s)
///   saved locally" with a Retry action
/// - offline, nothing queued    -> subtle amber "you are offline" bar
/// - online, syncing            -> progress bar "Syncing N bill(s)…"
/// - online, everything synced  -> renders nothing
///
/// The banner never claims a bill was delivered: while a queued bill is
/// being POSTed the state is "syncing", and only the server's 201 removes
/// it from the queue (see OfflineSyncService).
class SyncStatusBanner extends ConsumerWidget {
  const SyncStatusBanner({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final status = ref.watch(syncStatusProvider.select((s) => SyncSnapshot(
          isOnline: s.isOnline,
          isSyncing: s.isSyncing,
          pendingCount: s.pendingCount,
        )));
    final l10n = AppLocalizations.of(context);

    if (!status.isOnline) {
      final message = status.pendingCount > 0
          ? "${l10n.translate('sync_offline_queued_prefix')}${status.pendingCount}${l10n.translate('sync_offline_queued_suffix')}"
          : l10n.translate('sync_offline');
      return Material(
        color: const Color(0xFFFDF3E3),
        child: InkWell(
          onTap: () => ref.read(syncStatusProvider.notifier).refresh(),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 9),
            child: Row(
              children: [
                const Icon(Icons.wifi_off_rounded, size: 18, color: AppColors.warning),
                const SizedBox(width: 9),
                Expanded(
                  child: Text(
                    message,
                    style: const TextStyle(fontSize: 12.5, color: Color(0xFF8A5A00)),
                  ),
                ),
                Text(
                  l10n.translate('sync_retry_now'),
                  style: const TextStyle(
                      fontSize: 12.5, fontWeight: FontWeight.bold, color: AppColors.primary),
                ),
              ],
            ),
          ),
        ),
      );
    }

    if (status.isSyncing && status.pendingCount > 0) {
      return Material(
        color: const Color(0xFFE8F0FE),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
          child: Row(
            children: [
              const SizedBox(
                height: 14,
                width: 14,
                child: CircularProgressIndicator(strokeWidth: 2, color: AppColors.primary),
              ),
              const SizedBox(width: 10),
              Text(
                "${l10n.translate('sync_in_progress_prefix')}${status.pendingCount}${l10n.translate('sync_in_progress_suffix')}",
                style: const TextStyle(fontSize: 12.5, color: Color(0xFF1B4FA8)),
              ),
            ],
          ),
        ),
      );
    }

    return const SizedBox.shrink();
  }
}

/// Selected projection of [SyncStatus] so the widget only rebuilds on
/// fields it actually renders.
class SyncSnapshot {
  final bool isOnline;
  final bool isSyncing;
  final int pendingCount;

  const SyncSnapshot({
    required this.isOnline,
    required this.isSyncing,
    required this.pendingCount,
  });

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is SyncSnapshot &&
          other.isOnline == isOnline &&
          other.isSyncing == isSyncing &&
          other.pendingCount == pendingCount);

  @override
  int get hashCode => Object.hash(isOnline, isSyncing, pendingCount);
}
