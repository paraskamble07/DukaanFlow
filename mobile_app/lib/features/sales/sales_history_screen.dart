import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/constants/app_colors.dart';
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
    final salesAsync = ref.watch(salesListProvider);
    final statusFilter = ref.watch(saleStatusFilterProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Sales & Invoices'),
        actions: [
          IconButton(
            icon: const Icon(Icons.point_of_sale_rounded),
            tooltip: 'New Sale',
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
              decoration: const InputDecoration(
                hintText: 'Search invoice number or customer...',
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
                _statusChip(ref, '', 'All Bills', statusFilter),
                const SizedBox(width: 8),
                _statusChip(ref, 'PAID', 'Paid ✅', statusFilter),
                const SizedBox(width: 8),
                _statusChip(ref, 'PARTIAL', 'Khata Due ⚠️', statusFilter),
                const SizedBox(width: 8),
                _statusChip(ref, 'UNPAID', 'Unpaid', statusFilter),
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
                      Text('Could not load sales: $err', textAlign: TextAlign.center),
                      const SizedBox(height: 8),
                      ElevatedButton(
                        onPressed: () => ref.refresh(salesListProvider),
                        child: const Text('Retry'),
                      ),
                    ],
                  ),
                ),
                data: (sales) {
                  if (sales.isEmpty) {
                    return EmptyStateView(
                      icon: Icons.receipt_long_outlined,
                      title: 'No Sales Yet',
                      description: 'Create your first bill to see it here with invoice history.',
                      actionLabel: 'Create Sale',
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
                            Text('${sales.length} bills', style: const TextStyle(fontSize: 12, color: AppColors.textSecondary)),
                            Text(
                              'Total: ${CurrencyFormatter.format(dayTotal)}',
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
          backgroundColor: _statusColor(sale.paymentStatus).withOpacity(0.12),
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
                'Due: ${CurrencyFormatter.format(sale.dueAmount)}',
                style: const TextStyle(fontSize: 11, color: AppColors.danger, fontWeight: FontWeight.bold),
              ),
          ],
        ),
      ),
    );
  }
}
