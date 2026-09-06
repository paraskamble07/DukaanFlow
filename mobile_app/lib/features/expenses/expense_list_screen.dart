import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/constants/app_colors.dart';
import '../../core/utils/currency_formatter.dart';
import '../../models/expense_model.dart';
import '../../providers/business_provider.dart';
import '../../shared_widgets/empty_state_view.dart';
import 'expense_form_screen.dart';

class ExpenseListScreen extends ConsumerWidget {
  const ExpenseListScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final expensesAsync = ref.watch(expenseListProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Expenses'),
        actions: [
          IconButton(
            icon: const Icon(Icons.add_circle),
            tooltip: 'Add Expense',
            onPressed: () => Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => const ExpenseFormScreen()),
            ),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () async => ref.refresh(expenseListProvider),
        child: expensesAsync.when(
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (err, _) => Center(child: Text('Could not load expenses: $err')),
          data: (expenses) {
            if (expenses.isEmpty) {
              return EmptyStateView(
                icon: Icons.receipt_long_outlined,
                title: 'No Expenses Recorded',
                description: 'Track shop rent, electricity, salary and other costs to know your true profit.',
                actionLabel: 'Add Expense',
                onAction: () => Navigator.of(context).push(
                  MaterialPageRoute(builder: (_) => const ExpenseFormScreen()),
                ),
              );
            }

            double total = 0;
            for (final e in expenses) {
              total += e.amount;
            }

            return ListView.separated(
              padding: const EdgeInsets.all(12),
              itemCount: expenses.length + 1,
              separatorBuilder: (_, __) => const SizedBox(height: 8),
              itemBuilder: (context, index) {
                if (index == 0) {
                  return Card(
                    color: AppColors.primary.withOpacity(0.06),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                      side: const BorderSide(color: AppColors.primary, width: 1),
                    ),
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          const Text('Total Expenses (recent)', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                          Text(
                            CurrencyFormatter.format(total),
                            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: AppColors.primary),
                          ),
                        ],
                      ),
                    ),
                  );
                }
                return _ExpenseTile(expense: expenses[index - 1]);
              },
            );
          },
        ),
      ),
    );
  }
}

class _ExpenseTile extends StatelessWidget {
  final ExpenseModel expense;
  const _ExpenseTile({required this.expense});

  IconData get _categoryIcon {
    final name = (expense.categoryName ?? '').toLowerCase();
    if (name.contains('rent')) return Icons.home_work_outlined;
    if (name.contains('electricity')) return Icons.bolt;
    if (name.contains('salary')) return Icons.badge_outlined;
    if (name.contains('transport')) return Icons.local_shipping_outlined;
    if (name.contains('internet')) return Icons.wifi;
    return Icons.receipt_outlined;
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
        leading: Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: AppColors.warning.withOpacity(0.12),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Icon(_categoryIcon, color: AppColors.warning, size: 22),
        ),
        title: Text(expense.title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
        subtitle: Text(
          '${expense.categoryName ?? 'Uncategorised'} • ${expense.paymentMethodDisplay} • ${expense.expenseDate.length >= 10 ? expense.expenseDate.substring(0, 10) : expense.expenseDate}',
          style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
        ),
        trailing: Text(
          CurrencyFormatter.format(expense.amount),
          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: AppColors.danger),
        ),
      ),
    );
  }
}
