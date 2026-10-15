import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/constants/app_colors.dart';
import '../../core/localization/app_localizations.dart';
import '../../core/utils/currency_formatter.dart';
import '../../providers/business_provider.dart';
import '../../shared_widgets/empty_state_view.dart';
import '../../models/sale_model.dart';
import 'sale_detail_screen.dart';
import '../pos/pos_screen.dart';

class SalesHistoryScreen extends ConsumerWidget {
  const SalesHistoryScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final salesAsync = ref.watch(salesListProvider);
    final statusFilter = ref.watch(saleStatusFilterProvider);

    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.translate('sales_invoices')),
        actions: [
          IconButton(
            icon: const Icon(Icons.point_of_sale_rounded),
            tooltip: l10n.translate('new_sale'),
            onPressed: () => Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => const PosScreen()),
            ),
          ),
        ],
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            child: TextField(
              decoration: InputDecoration(
                hintText: l10n.translate('search_invoice_customer'),
                prefixIcon: Icon(Icons.search),
                isDense: true,
              ),
              onChanged: (q) => ref.read(saleSearchQueryProvider.notifier).state = q,
            ),
          ),
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 12),
            child: Row(
              children: [
                _statusChip(ref, '', l10n.translate('all_bills'), statusFilter),
                const SizedBox(width: 8),
                _statusChip(ref, 'PAID', l10n.translate('paid'), statusFilter),
                const SizedBox(width: 8),
                _statusChip(ref, 'PARTIAL', l10n.translate('khata_due'), statusFilter),
                const SizedBox(width: 8),
                _statusChip(ref, 'UNPAID', l10n.translate('unpaid'), statusFilter),
              ],
            ),
          ),
          const SizedBox(height: 8),
          Expanded(
            child: RefreshIndicator(
              onRefresh: () async => ref.refresh(salesListProvider),
              child: salesAsync.when(
                loading: () => const Center(child: CircularProgressIndicator()),
                error: (err, _) => Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text('${l10n.translate('could_not_load_sales')}$err', textAlign: TextAlign.center),
                      const SizedBox(height: 8),
                      ElevatedButton(
                        onPressed: () => ref.refresh(salesListProvider),
                        child: Text(l10n.translate('retry')),
                      ),
                    ],
                  ),
                ),
                data: (sales) {
                  if (sales.isEmpty) {
                    return EmptyStateView(
                      icon: Icons.receipt_long_outlined,
                      title: l10n.translate('no_sales_title'),
                      description: l10n.translate('no_sales_desc'),
                      actionLabel: l10n.translate('create_sale'),
                      onAction: () => Navigator.of(context).push(
                        MaterialPageRoute(builder: (_) => const PosScreen()),
                      ),
                    );
                  }

                  double dayTotal = 0;
                  for (final s in sales) {
                    dayTotal += s.totalAmount;
                  }

                  return Column(
                    children: [
                      Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 16),
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text('${sales.length} ${l10n.translate('bills')}', style: const TextStyle(fontSize: 12, color: AppColors.textSecondary)),
                            Text(
                              "${l10n.translate('total_colon')}${CurrencyFormatter.format(dayTotal)}",
                              style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: AppColors.primary),
                            ),
                          ],
                        ),
                      ),
                      Expanded(
                        child: ListView.separated(
                          padding: const EdgeInsets.all(12),
                          itemCount: sales.length,
                          separatorBuilder: (_, __) => const SizedBox(height: 8),
                          itemBuilder: (context, index) => _SaleTile(sale: sales[index]),
                        ),
                      ),
                    ],
                  );
                },
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _statusChip(WidgetRef ref, String value, String label, String current) {
    return FilterChip(
      label: Text(label),
      selected: current == value,
      onSelected: (_) => ref.read(saleStatusFilterProvider.notifier).state = value,
    );
  }
}

class _SaleTile extends StatelessWidget {
  final SaleModel sale;
  const _SaleTile({required this.sale});

  Color _statusColor(String status) {
    switch (status) {
      case 'PAID':
        return AppColors.success;
      case 'PARTIAL':
        return AppColors.warning;
      default:
        return AppColors.danger;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
        onTap: () => Navigator.of(context).push(
          MaterialPageRoute(builder: (_) => SaleDetailScreen(saleId: sale.id)),
        ),
        leading: CircleAvatar(
          backgroundColor: _statusColor(sale.paymentStatus).withValues(alpha: 0.12),
          child: Icon(
            sale.paymentStatus == 'PAID' ? Icons.check_circle : Icons.schedule,
            color: _statusColor(sale.paymentStatus),
            size: 22,
          ),
        ),
        title: Text(
          '${sale.invoiceNumber} • ${sale.customerName}',
          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
        ),
        subtitle: Text(
          '${sale.saleDate.length >= 10 ? sale.saleDate.substring(0, 10) : sale.saleDate} • ${sale.items.length} items • ${sale.paymentMethodDisplay}',
          style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
        ),
        trailing: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Text(
              CurrencyFormatter.format(sale.totalAmount),
              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
            ),
            if (sale.dueAmount > 0)
              Text(
                "${AppLocalizations.of(context).translate('due_label')}${CurrencyFormatter.format(sale.dueAmount)}",
                style: const TextStyle(fontSize: 11, color: AppColors.danger, fontWeight: FontWeight.bold),
              ),
          ],
        ),
      ),
    );
  }
}
