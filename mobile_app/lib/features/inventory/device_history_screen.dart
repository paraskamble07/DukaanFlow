import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/constants/app_colors.dart';
import '../../core/localization/app_localizations.dart';
import '../../core/utils/currency_formatter.dart';
import '../../models/device_model.dart';
import '../../models/stock_movement_model.dart';
import '../../providers/inventory_provider.dart';

/// Full history of one IMEI-tracked unit (Phase 11): the device's status,
/// its warranty state exactly as the server computes it, and a timeline
/// assembled from real records (registration, stock movements, sale).
class DeviceHistoryScreen extends ConsumerWidget {
  final int deviceId;

  const DeviceHistoryScreen({super.key, required this.deviceId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final historyAsync = ref.watch(imeiDeviceHistoryProvider(deviceId));

    return Scaffold(
      appBar: AppBar(title: Text(l10n.translate('device_history_title'))),
      body: historyAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, _) => Center(
          child: Text('${l10n.translate('could_not_load_history')}$err',
              textAlign: TextAlign.center),
        ),
        data: (result) {
          if (result == null) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.phone_android_outlined,
                      size: 48, color: AppColors.textSecondary),
                  const SizedBox(height: 12),
                  Text(l10n.translate('imei_units_empty'),
                      textAlign: TextAlign.center),
                ],
              ),
            );
          }
          final device = result.device;
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              _DeviceHeader(l10n: l10n, imei: device.imei1, model: device.modelName, brand: device.brand),
              const SizedBox(height: 12),
              _StatusCard(l10n: l10n, result: result),
              const SizedBox(height: 16),
              Text(
                l10n.translate('device_timeline_title'),
                style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              if (result.timeline.isEmpty)
                Text(l10n.translate('device_timeline_empty'),
                    style: const TextStyle(color: AppColors.textSecondary))
              else
                ...result.timeline
                    .map((entry) => _TimelineTile(l10n: l10n, entry: entry)),
            ],
          );
        },
      ),
    );
  }
}

class _DeviceHeader extends StatelessWidget {
  final AppLocalizations l10n;
  final String imei;
  final String? model;
  final String? brand;

  const _DeviceHeader({required this.l10n, required this.imei, this.model, this.brand});

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.phone_android_rounded, color: AppColors.primary),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    [brand, model].whereType<String>().join(' • '),
                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                Text(l10n.translate('scan_imei'),
                    style: const TextStyle(color: AppColors.textSecondary)),
                const SizedBox(width: 8),
                SelectableText(imei,
                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _StatusCard extends StatelessWidget {
  final AppLocalizations l10n;
  final DeviceHistoryResult result;

  const _StatusCard({required this.l10n, required this.result});

  @override
  Widget build(BuildContext context) {
    final device = result.device;
    final hasSold = result.timeline.any((e) => e.isSale);

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                _StatusChip(status: device.status, display: device.statusDisplay),
                const SizedBox(width: 8),
                if (device.invoiceNumber != null)
                  Text('#${device.invoiceNumber}',
                      style: const TextStyle(
                          fontWeight: FontWeight.bold,
                          color: AppColors.primary)),
              ],
            ),
            const SizedBox(height: 12),
            if (hasSold && device.customerName != null) ...[
              Text(
                '${l10n.translate('sold_to')}${device.customerName}',
                style: const TextStyle(fontSize: 13),
              ),
              if (device.customerPhone != null)
                Text(device.customerPhone!,
                    style: const TextStyle(
                        fontSize: 12, color: AppColors.textSecondary)),
            ],
            const SizedBox(height: 12),
            _WarrantyRow(l10n: l10n, device: device),
            const SizedBox(height: 12),
            Row(
              children: [
                _InfoCell(
                  label: l10n.translate('unit_cost_label'),
                  value: CurrencyFormatter.format(device.purchasePrice),
                ),
                const SizedBox(width: 24),
                _InfoCell(
                  label: l10n.translate('selling_price_label'),
                  value: CurrencyFormatter.format(device.sellingPrice),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _StatusChip extends StatelessWidget {
  final String status;
  final String display;

  const _StatusChip({required this.status, required this.display});

  @override
  Widget build(BuildContext context) {
    final color = switch (status) {
      'IN_STOCK' => AppColors.success,
      'SOLD' => AppColors.primary,
      'RETURNED' => AppColors.warning,
      'DEFECTIVE' => AppColors.danger,
      _ => AppColors.textSecondary,
    };
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(display,
          style: TextStyle(
              color: color, fontWeight: FontWeight.bold, fontSize: 12)),
    );
  }
}

class _WarrantyRow extends StatelessWidget {
  final AppLocalizations l10n;
  final DeviceModel device;

  const _WarrantyRow({required this.l10n, required this.device});

  @override
  Widget build(BuildContext context) {
    final status = device.warrantyStatus;
    final days = device.warrantyDaysRemaining;

    final (label, color) = switch (status) {
      'ACTIVE' => (
          '${l10n.translate('warranty_active')}'
          '${days != null ? ' — $days${l10n.translate('warranty_days_remaining_suffix')}' : ''}',
          AppColors.success),
      'EXPIRED' => (
          '${l10n.translate('warranty_expired')}'
          '${days != null ? ' — ${days.abs()}${l10n.translate('warranty_days_ago_suffix')}' : ''}',
          AppColors.danger),
      _ => (l10n.translate('warranty_no_cover'), AppColors.textSecondary),
    };

    return Row(
      children: [
        const Icon(Icons.shield_outlined, size: 18, color: AppColors.primary),
        const SizedBox(width: 8),
        Expanded(
          child: Text(label,
              style:
                  TextStyle(fontSize: 13, color: color, fontWeight: FontWeight.w600)),
        ),
      ],
    );
  }
}

class _InfoCell extends StatelessWidget {
  final String label;
  final String value;

  const _InfoCell({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label,
            style: const TextStyle(fontSize: 11, color: AppColors.textSecondary)),
        Text(value,
            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
      ],
    );
  }
}

class _TimelineTile extends StatelessWidget {
  final AppLocalizations l10n;
  final DeviceHistoryEntry entry;

  const _TimelineTile({required this.l10n, required this.entry});

  @override
  Widget build(BuildContext context) {
    final icon = switch (entry.type) {
      'SALE' => Icons.shopping_cart_checkout_rounded,
      'PURCHASE' => Icons.inventory_rounded,
      'ADJUSTMENT' => Icons.tune_rounded,
      'RETURN' => Icons.undo_rounded,
      _ => Icons.app_registration_rounded,
    };
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        leading: Icon(icon, color: AppColors.primary, size: 22),
        title: Text(
          entry.typeDisplay.isNotEmpty
              ? entry.typeDisplay
              : entry.type,
          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (entry.reference != null)
              Text('${l10n.translate('invoice_hash')}${entry.reference}',
                  style: const TextStyle(fontSize: 11, color: AppColors.textSecondary)),
            if (entry.note != null)
              Text(entry.note!,
                  style: const TextStyle(fontSize: 11, color: AppColors.textSecondary)),
            Text(
              entry.date ?? '',
              style: const TextStyle(fontSize: 10, color: AppColors.textSecondary),
            ),
          ],
        ),
      ),
    );
  }
}
