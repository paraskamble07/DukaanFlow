import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/constants/app_colors.dart';
import '../../core/localization/app_localizations.dart';
import '../../core/network/api_error.dart';
import '../../core/utils/currency_formatter.dart';
import '../../providers/notifications_provider.dart';

/// NotificationCenter — everything the shop needs to act on right now.
/// Every group is recomputed server-side from the live books; tapping a
/// group jumps to the screen that resolves it.
class NotificationsScreen extends ConsumerWidget {
  const NotificationsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final async = ref.watch(notificationsProvider);

    return Scaffold(
      appBar: AppBar(title: Text(l10n.translate('notifications'))),
      body: RefreshIndicator(
        onRefresh: () async => ref.refresh(notificationsProvider),
        child: async.when(
          loading: () => ListView(
            physics: const AlwaysScrollableScrollPhysics(),
            children: const [
              SizedBox(height: 200),
              Center(child: CircularProgressIndicator()),
            ],
          ),
          error: (err, _) => ListView(
            physics: const AlwaysScrollableScrollPhysics(),
            children: [
              const SizedBox(height: 120),
              Center(
                child: Text(apiErrorMessage(err, l10n),
                    textAlign: TextAlign.center),
              ),
            ],
          ),
          data: (groups) {
            if (groups.isEmpty) {
              return ListView(
                physics: const AlwaysScrollableScrollPhysics(),
                children: [
                  const SizedBox(height: 140),
                  Icon(Icons.check_circle_outline_rounded,
                      size: 64, color: AppColors.success.withValues(alpha: 0.6)),
                  const SizedBox(height: 16),
                  Center(
                    child: Text(
                      l10n.translate('all_caught_up'),
                      textAlign: TextAlign.center,
                      style: const TextStyle(
                          fontSize: 15, fontWeight: FontWeight.w600),
                    ),
                  ),
                  const SizedBox(height: 8),
                  Center(
                    child: Text(
                      l10n.translate('all_caught_up_sub'),
                      textAlign: TextAlign.center,
                      style: const TextStyle(
                          fontSize: 12.5, color: AppColors.textSecondary),
                    ),
                  ),
                ],
              );
            }
            return ListView(
              padding: const EdgeInsets.all(16),
              children: groups.map((g) => _GroupCard(group: g)).toList(),
            );
          },
        ),
      ),
    );
  }
}

class _GroupCard extends ConsumerWidget {
  final NotificationGroup group;
  const _GroupCard({required this.group});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final isWarning = group.severity == 'warning';
    final icon = switch (group.type) {
      'KHATA_DUE' => Icons.payments_outlined,
      'LOW_STOCK' => Icons.inventory_2_outlined,
      'SUPPLIER_DUE' => Icons.local_shipping_outlined,
      _ => Icons.notifications_outlined,
    };

    return Card(
      shape: RoundedRectangleBorder(
        side: BorderSide(
          color: isWarning
              ? AppColors.warning.withValues(alpha: 0.5)
              : AppColors.info.withValues(alpha: 0.35),
          width: 1.2,
        ),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(icon,
                    color: isWarning ? AppColors.warning : AppColors.info,
                    size: 24),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    group.title,
                    style: const TextStyle(
                        fontWeight: FontWeight.bold, fontSize: 14.5),
                  ),
                ),
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
                  decoration: BoxDecoration(
                    color: (isWarning ? AppColors.warning : AppColors.info)
                        .withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Text(
                    '${group.count}',
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                      color: isWarning ? AppColors.warning : AppColors.info,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              group.body,
              style: const TextStyle(
                  fontSize: 12.5, color: AppColors.textSecondary),
            ),
            if (group.items.isNotEmpty) ...[
              const SizedBox(height: 10),
              ...group.items.map((item) {
                final name = item['name']?.toString() ?? '';
                final due = item['outstanding_due'];
                final stock = item['stock_quantity'];
                final min = item['min_stock'];
                final trailing = due != null
                    ? CurrencyFormatter.format(
                        double.tryParse(due.toString()) ?? 0)
                    : (stock != null
                        ? '$stock / ${min ?? 0} ${l10n.translate('in_stock_short')}'
                        : null);
                return Padding(
                  padding: const EdgeInsets.symmetric(vertical: 3),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Expanded(
                        child: Text(name,
                            style: const TextStyle(fontSize: 12.5),
                            overflow: TextOverflow.ellipsis),
                      ),
                      if (trailing != null)
                        Text(
                          trailing,
                          style: TextStyle(
                            fontSize: 12.5,
                            fontWeight: FontWeight.bold,
                            color: due != null
                                ? AppColors.danger
                                : AppColors.warning,
                          ),
                        ),
                    ],
                  ),
                );
              }),
            ],
          ],
        ),
      ),
    );
  }
}
