import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/constants/app_colors.dart';
import '../../core/localization/app_localizations.dart';
import '../../core/utils/currency_formatter.dart';
import '../../models/purchase_model.dart';
import '../../providers/purchase_provider.dart';
import 'purchase_form_screen.dart';

/// Shop-wide purchase history (Phase 11): every bill from a supplier with
/// its items, due amount still owned and payment mode. Every amount shown
/// comes from the server payload.
class PurchaseHistoryScreen extends ConsumerWidget {
  /// Scope the list to a single product's restocks (from product detail).
  final int? productId;

  const PurchaseHistoryScreen({super.key, this.productId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final purchasesAsync = ref.watch(purchasesListProvider(productId));

    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.translate('purchase_history_screen_title')),
        actions: [
          IconButton(
            icon: const Icon(Icons.add),
            tooltip: l10n.translate('new_purchase'),
            onPressed: () => Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => const PurchaseFormScreen()),
            ),
          ),
        ],
      ),
      body: purchasesAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, _) => Center(
          child: Text(
              '${AppLocalizations.of(context).translate('error_loading_products')}$err',
              textAlign: TextAlign.center),
        ),
        data: (purchases) {
          if (purchases.isEmpty) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Text(
                  l10n.translate('purchases_empty'),
                  textAlign: TextAlign.center,
                  style: const TextStyle(color: AppColors.textSecondary),
                ),
              ),
            );
          }
          return ListView.separated(
            padding: const EdgeInsets.all(12),
            itemCount: purchases.length,
            separatorBuilder: (_, __) => const SizedBox(height: 8),
            itemBuilder: (context, index) =>
                _PurchaseCard(l10n: l10n, purchase: purchases[index]),
          );
        },
      ),
    );
  }
}

class _PurchaseCard extends StatelessWidget {
  final AppLocalizations l10n;
  final PurchaseModel purchase;

  const _PurchaseCard({required this.l10n, required this.purchase});

  @override
  Widget build(BuildContext context) {
    final due = purchase.dueAmount;
    return Card(
      child: ExpansionTile(
        tilePadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 4),
        title: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '${l10n.translate('invoice_hash')}${purchase.invoiceNumber}',
                    style: const TextStyle(
                        fontWeight: FontWeight.bold, fontSize: 13),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    [
                      purchase.supplierName ?? '-',
                      _formatDate(purchase.purchaseDate),
                    ].join(' | '),
                    style: const TextStyle(
                        fontSize: 11, color: AppColors.textSecondary),
                  ),
                ],
              ),
            ),
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(
                  CurrencyFormatter.format(purchase.totalAmount),
                  style: const TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 14,
                      color: AppColors.primary),
                ),
                if (due > 0)
                  Text(
                    '${l10n.translate('due_label')}${CurrencyFormatter.format(due)}',
                    style: const TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.bold,
                        color: AppColors.danger),
                  ),
              ],
            ),
          ],
        ),
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(14, 0, 14, 12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                ...purchase.items.map((item) => Padding(
                      padding: const EdgeInsets.symmetric(vertical: 3),
                      child: Row(
                        children: [
                          Expanded(
                            child: Text(
                              '${item.productName} × ${item.quantity}',
                              style: const TextStyle(fontSize: 12),
                            ),
                          ),
                          Text(
                            CurrencyFormatter.format(item.totalCost),
                            style: const TextStyle(
                                fontSize: 12,
                                fontWeight: FontWeight.w600,
                                color: AppColors.textSecondary),
                          ),
                        ],
                      ),
                    )),
                const SizedBox(height: 6),
                Text(
                  '${l10n.translate('paid_amount')}${CurrencyFormatter.format(purchase.paidAmount)}'
                  ' (${purchase.paymentMethod})',
                  style: const TextStyle(
                      fontSize: 11, color: AppColors.textSecondary),
                ),
                if (purchase.notes != null && purchase.notes!.isNotEmpty)
                  Padding(
                    padding: const EdgeInsets.only(top: 4),
                    child: Text(purchase.notes!,
                        style: const TextStyle(
                            fontSize: 11, color: AppColors.textSecondary)),
                  ),
              ],
            ),
          ),
        ],
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
