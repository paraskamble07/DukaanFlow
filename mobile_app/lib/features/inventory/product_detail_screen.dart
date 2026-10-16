import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/constants/app_colors.dart';
import '../../core/localization/app_localizations.dart';
import '../../core/utils/currency_formatter.dart';
import '../../models/product_detail_model.dart';
import '../../models/purchase_model.dart';
import '../../models/stock_movement_model.dart';
import '../../providers/product_provider.dart';
import 'device_history_screen.dart';
import 'product_form_screen.dart';

/// One product with its full history (Phase 11): stock status (incl. the
/// server's dead-stock verdict), purchase history, stock movements and the
/// registered IMEI units. All values come from the server payload —
/// nothing is recomputed or invented client-side.
class ProductDetailScreen extends ConsumerWidget {
  final int productId;

  const ProductDetailScreen({super.key, required this.productId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final detailAsync = ref.watch(productDetailProvider(productId));

    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.translate('product_detail_title')),
        actions: [
          detailAsync.maybeWhen(
            data: (detail) => detail == null
                ? const SizedBox.shrink()
                : IconButton(
                    icon: const Icon(Icons.edit_outlined),
                    tooltip: l10n.translate('edit_product'),
                    onPressed: () => Navigator.of(context).push(
                      MaterialPageRoute(
                        builder: (_) => ProductFormScreen(product: detail.product),
                      ),
                    ),
                  ),
            orElse: () => const SizedBox.shrink(),
          ),
        ],
      ),
      body: detailAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, _) => Center(
          child: Text('${l10n.translate('could_not_load_dashboard')}$err',
              textAlign: TextAlign.center),
        ),
        data: (detail) {
          if (detail == null) {
            return Center(
              child: Text(l10n.translate('imei_units_empty'),
                  textAlign: TextAlign.center),
            );
          }
          return RefreshIndicator(
            onRefresh: () async => ref.invalidate(productDetailProvider(productId)),
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                _ProductHeader(l10n: l10n, detail: detail),
                const SizedBox(height: 16),
                Text(l10n.translate('purchase_history'),
                    style: sectionTitle),
                const SizedBox(height: 8),
                if (detail.purchaseHistory.isEmpty)
                  _EmptyNote(l10n.translate('purchase_history_empty'))
                else
                  ...detail.purchaseHistory.map((p) => _PurchaseTile(l10n: l10n, purchase: p)),
                const SizedBox(height: 16),
                Text(l10n.translate('stock_movements'),
                    style: sectionTitle),
                const SizedBox(height: 8),
                if (detail.movements.isEmpty)
                  _EmptyNote(l10n.translate('stock_movements_empty'))
                else
                  ...detail.movements.map((m) => _MovementTile(l10n: l10n, movement: m)),
                if (detail.product.isImeiTracked) ...[
                  const SizedBox(height: 16),
                  Text(l10n.translate('imei_units'), style: sectionTitle),
                  const SizedBox(height: 8),
                  if (detail.devices.isEmpty)
                    _EmptyNote(l10n.translate('imei_units_empty'))
                  else
                    ...detail.devices.map((d) => _DeviceRow(
                          l10n: l10n,
                          imei: d.imei1,
                          status: d.status,
                          statusDisplay: d.statusDisplay,
                          warrantyStatus: d.warrantyStatus,
                          daysRemaining: d.warrantyDaysRemaining,
                          onTap: () => Navigator.of(context).push(
                            MaterialPageRoute(
                              builder: (_) =>
                                  DeviceHistoryScreen(deviceId: d.id),
                            ),
                          ),
                        )),
                ],
              ],
            ),
          );
        },
      ),
    );
  }
}

const sectionTitle =
    TextStyle(fontSize: 15, fontWeight: FontWeight.bold);

class _EmptyNote extends StatelessWidget {
  final String text;
  const _EmptyNote(this.text);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 4),
      child: Text(text, style: const TextStyle(color: AppColors.textSecondary)),
    );
  }
}

class _ProductHeader extends StatelessWidget {
  final AppLocalizations l10n;
  final ProductDetailData detail;

  const _ProductHeader({required this.l10n, required this.detail});

  @override
  Widget build(BuildContext context) {
    final p = detail.product;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(p.name,
                style: const TextStyle(
                    fontSize: 17, fontWeight: FontWeight.bold)),
            if (p.brand != null) ...[
              const SizedBox(height: 2),
              Text(p.brand!,
                  style: const TextStyle(color: AppColors.textSecondary)),
            ],
            const SizedBox(height: 10),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                _Chip(
                  label: '${p.stockQuantity} ${l10n.translate('stock')}',
                  color: p.isOutOfStock
                      ? AppColors.danger
                      : (p.isLowStock ? AppColors.warning : AppColors.success),
                ),
                if (p.isImeiTracked)
                  const _Chip(label: 'IMEI', color: AppColors.primary),
                if (detail.isDeadStock)
                  _Chip(
                    label: l10n.translate('dead_stock_flag'),
                    color: AppColors.danger,
                    filled: false,
                  ),
              ],
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                _InfoCell(
                  label: l10n.translate('cost_colon'),
                  value: CurrencyFormatter.format(p.purchasePrice),
                ),
                const SizedBox(width: 24),
                _InfoCell(
                  label: l10n.translate('selling_price_label'),
                  value: CurrencyFormatter.format(p.sellingPrice),
                ),
                const SizedBox(width: 24),
                _InfoCell(
                  label: l10n.translate('total_cost_label'),
                  value: CurrencyFormatter.format(
                      p.purchasePrice * p.stockQuantity),
                ),
              ],
            ),
            if (p.warrantyMonths > 0) ...[
              const SizedBox(height: 8),
              Text(
                '${l10n.translate('warranty_expiry_label')}'
                '${p.warrantyMonths} ${l10n.translate('months')}',
                style: const TextStyle(
                    fontSize: 12, color: AppColors.textSecondary),
              ),
            ],
            const SizedBox(height: 8),
            Text(
              detail.lastSaleDate != null
                  ? '${l10n.translate('last_sold_on')}'
                      '${_formatDate(detail.lastSaleDate!)}'
                  : '${l10n.translate('last_sold_on')}${l10n.translate('never_sold')}',
              style: const TextStyle(
                  fontSize: 12, color: AppColors.textSecondary),
            ),
          ],
        ),
      ),
    );
  }
}

String _formatDate(String iso) {
  final dt = DateTime.tryParse(iso)?.toLocal();
  if (dt == null) return iso;
  return '${dt.day.toString().padLeft(2, '0')}-'
      '${dt.month.toString().padLeft(2, '0')}-'
      '${dt.year}';
}

class _Chip extends StatelessWidget {
  final String label;
  final Color color;
  final bool filled;

  const _Chip({required this.label, required this.color, this.filled = true});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: filled ? color.withValues(alpha: 0.12) : Colors.transparent,
        border: filled ? null : Border.all(color: color, width: 1),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(label,
          style: TextStyle(
              color: color, fontWeight: FontWeight.bold, fontSize: 11)),
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

class _PurchaseTile extends StatelessWidget {
  final AppLocalizations l10n;
  final ProductPurchaseModel purchase;

  const _PurchaseTile({required this.l10n, required this.purchase});

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        leading:
            const Icon(Icons.local_shipping_outlined, color: AppColors.primary),
        title: Text(
          '${l10n.translate('invoice_hash')}${purchase.invoiceNumber ?? '-'}'
          ' × ${purchase.quantity}',
          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
        ),
        subtitle: Text(
          [
            purchase.supplierName,
            '${l10n.translate('unit_cost_label')}: ${CurrencyFormatter.format(purchase.unitCost)}',
            '${l10n.translate('total_cost_label')}: ${CurrencyFormatter.format(purchase.totalCost)}',
          ].join(' | '),
          style: const TextStyle(fontSize: 11, color: AppColors.textSecondary),
        ),
        trailing: Text(
          _formatDate(purchase.purchaseDate ?? ''),
          style: const TextStyle(fontSize: 11, color: AppColors.textSecondary),
        ),
      ),
    );
  }
}

class _MovementTile extends StatelessWidget {
  final AppLocalizations l10n;
  final StockMovementModel movement;

  const _MovementTile({required this.l10n, required this.movement});

  @override
  Widget build(BuildContext context) {
    final isPositive = movement.newStock >= movement.previousStock;
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        leading: Icon(
          isPositive ? Icons.arrow_upward_rounded : Icons.arrow_downward_rounded,
          color: isPositive ? AppColors.success : AppColors.danger,
          size: 20,
        ),
        title: Text(
          movement.movementTypeDisplay.isNotEmpty
              ? movement.movementTypeDisplay
              : movement.movementType,
          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (movement.notes != null)
              Text(movement.notes!,
                  style: const TextStyle(
                      fontSize: 11, color: AppColors.textSecondary)),
            Text(
              '${movement.previousStock} → ${movement.newStock}'
              '${movement.deviceImei != null ? ' (IMEI: ${movement.deviceImei})' : ''}',
              style: const TextStyle(
                  fontSize: 11, color: AppColors.textSecondary),
            ),
            Text(_formatDate(movement.createdAt),
                style: const TextStyle(
                    fontSize: 10, color: AppColors.textSecondary)),
          ],
        ),
      ),
    );
  }
}

class _DeviceRow extends StatelessWidget {
  final AppLocalizations l10n;
  final String imei;
  final String status;
  final String statusDisplay;
  final String warrantyStatus;
  final int? daysRemaining;
  final VoidCallback onTap;

  const _DeviceRow({
    required this.l10n,
    required this.imei,
    required this.status,
    required this.statusDisplay,
    required this.warrantyStatus,
    this.daysRemaining,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final warrantyLabel = switch (warrantyStatus) {
      'ACTIVE' => daysRemaining != null
          ? '$daysRemaining${l10n.translate('warranty_days_remaining_suffix')}'
          : l10n.translate('warranty_active'),
      'EXPIRED' => daysRemaining != null
          ? '${daysRemaining!.abs()}${l10n.translate('warranty_days_ago_suffix')}'
          : l10n.translate('warranty_expired'),
      _ => l10n.translate('warranty_no_cover'),
    };
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
          child: Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(imei,
                        style: const TextStyle(
                            fontWeight: FontWeight.bold, fontSize: 13)),
                    const SizedBox(height: 2),
                    Text(
                      '$statusDisplay · $warrantyLabel',
                      style: const TextStyle(
                          fontSize: 11, color: AppColors.textSecondary),
                    ),
                  ],
                ),
              ),
              Text(l10n.translate('view_device_history'),
                  style: const TextStyle(
                      color: AppColors.primary,
                      fontSize: 12,
                      fontWeight: FontWeight.bold)),
              const Icon(Icons.chevron_right_rounded, color: AppColors.primary),
            ],
          ),
        ),
      ),
    );
  }
}
