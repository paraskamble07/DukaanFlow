import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/constants/app_colors.dart';
import '../../core/utils/currency_formatter.dart';
import '../../providers/customer_provider.dart';
import '../../shared_widgets/empty_state_view.dart';
import '../../shared_widgets/whatsapp_button.dart';
import 'customer_detail_screen.dart';
import 'customer_form_screen.dart';

class CustomerListScreen extends ConsumerWidget {
  const CustomerListScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final customersAsync = ref.watch(customerListProvider);
    final dueFilter = ref.watch(customerDueFilterProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Customers & Digital Khata'),
        actions: [
          IconButton(
            icon: const Icon(Icons.person_add),
            tooltip: 'Add Customer',
            onPressed: () => Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => const CustomerFormScreen()),
            ),
          ),
        ],
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(12.0),
            child: TextField(
              decoration: const InputDecoration(
                hintText: 'Search customer name or phone...',
                prefixIcon: Icon(Icons.search),
                isDense: true,
                contentPadding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              ),
              onChanged: (q) => ref.read(customerSearchProvider.notifier).state = q,
            ),
          ),
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 12),
            child: Row(
              children: [
                FilterChip(
                  label: const Text('All Customers'),
                  selected: dueFilter.isEmpty,
                  onSelected: (_) => ref.read(customerDueFilterProvider.notifier).state = '',
                ),
                const SizedBox(width: 8),
                FilterChip(
                  label: const Text('Pending Udhar (Due) ⚠️'),
                  selected: dueFilter == 'yes',
                  onSelected: (_) => ref.read(customerDueFilterProvider.notifier).state = 'yes',
                ),
                const SizedBox(width: 8),
                FilterChip(
                  label: const Text('Cleared Accounts ✅'),
                  selected: dueFilter == 'cleared',
                  onSelected: (_) => ref.read(customerDueFilterProvider.notifier).state = 'cleared',
                ),
              ],
            ),
          ),
          const SizedBox(height: 8),

          Expanded(
            child: RefreshIndicator(
              onRefresh: () async => ref.refresh(customerListProvider),
              child: customersAsync.when(
                loading: () => const Center(child: CircularProgressIndicator()),
                error: (err, _) => Center(child: Text('Error: $err')),
                data: (customers) {
                  if (customers.isEmpty) {
                    return EmptyStateView(
                      icon: Icons.people_outline,
                      title: 'No Customers Found',
                      description: 'Add your regular customers to maintain credit (Khata) balances.',
                      actionLabel: 'Add Customer',
                      onAction: () => Navigator.of(context).push(
                        MaterialPageRoute(builder: (_) => const CustomerFormScreen()),
                      ),
                    );
                  }

                  return ListView.separated(
                    padding: const EdgeInsets.all(12),
                    itemCount: customers.length,
                    separatorBuilder: (_, __) => const SizedBox(height: 8),
                    itemBuilder: (context, index) {
                      final c = customers[index];
                      return Card(
                        child: ListTile(
                          contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                          onTap: () => Navigator.of(context).push(
                            MaterialPageRoute(builder: (_) => CustomerDetailScreen(customer: c)),
                          ),
                          leading: CircleAvatar(
                            backgroundColor: AppColors.primary.withOpacity(0.1),
                            child: Text(
                              c.name.isNotEmpty ? c.name[0].toUpperCase() : 'C',
                              style: const TextStyle(fontWeight: FontWeight.bold, color: AppColors.primary),
                            ),
                          ),
                          title: Text(c.name, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                          subtitle: Text(c.phone, style: const TextStyle(fontSize: 12, color: AppColors.textSecondary)),
                          trailing: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            crossAxisAlignment: CrossAxisAlignment.end,
                            children: [
                              Text(
                                c.outstandingDue > 0 ? 'Due: ${CurrencyFormatter.format(c.outstandingDue)}' : 'Cleared',
                                style: TextStyle(
                                  fontSize: 13,
                                  fontWeight: FontWeight.bold,
                                  color: c.outstandingDue > 0 ? AppColors.danger : AppColors.success,
                                ),
                              ),
                              if (c.outstandingDue > 0 && c.whatsappReminderUrl != null)
                                Padding(
                                  padding: const EdgeInsets.only(top: 4.0),
                                  child: WhatsAppButton(
                                    url: c.whatsappReminderUrl,
                                    label: 'Remind',
                                    isCompact: true,
                                  ),
                                ),
                            ],
                          ),
                        ),
                      );
                    },
                  );
                },
              ),
            ),
          ),
        ],
      ),
    );
  }
}
