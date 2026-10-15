import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/constants/app_colors.dart';
import '../../core/localization/app_localizations.dart';
import '../../core/utils/currency_formatter.dart';
import '../../providers/business_provider.dart';
import '../../shared_widgets/empty_state_view.dart';
import 'supplier_form_screen.dart';
import 'supplier_detail_screen.dart';

class SupplierListScreen extends ConsumerWidget {
  const SupplierListScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final suppliersAsync = ref.watch(supplierListProvider);
    final query = ref.watch(supplierSearchProvider);

    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.translate('suppliers')),
        actions: [
          IconButton(
            icon: const Icon(Icons.local_shipping),
            tooltip: l10n.translate('add_supplier'),
            onPressed: () => Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => const SupplierFormScreen()),
            ),
          ),
        ],
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(12),
            child: TextField(
              decoration: InputDecoration(
                hintText: l10n.translate('search_supplier'),
                prefixIcon: Icon(Icons.search),
                isDense: true,
              ),
              onChanged: (q) => ref.read(supplierSearchProvider.notifier).state = q,
            ),
          ),
          Expanded(
            child: RefreshIndicator(
              onRefresh: () async => ref.refresh(supplierListProvider),
              child: suppliersAsync.when(
                loading: () => const Center(child: CircularProgressIndicator()),
                error: (err, _) => Center(child: Text('${l10n.translate('could_not_load_suppliers')}$err')),
                data: (suppliers) {
                  final filtered = query.isEmpty
                      ? suppliers
                      : suppliers
                          .where((s) =>
                              s.companyName.toLowerCase().contains(query.toLowerCase()) ||
                              s.phone.contains(query))
                          .toList();

                  if (filtered.isEmpty) {
                    return EmptyStateView(
                      icon: Icons.local_shipping_outlined,
                      title: l10n.translate('no_suppliers_title'),
                      description: l10n.translate('no_suppliers_desc'),
                      actionLabel: l10n.translate('add_supplier'),
                      onAction: () => Navigator.of(context).push(
                        MaterialPageRoute(builder: (_) => const SupplierFormScreen()),
                      ),
                    );
                  }

                  return ListView.separated(
                    padding: const EdgeInsets.all(12),
                    itemCount: filtered.length,
                    separatorBuilder: (_, __) => const SizedBox(height: 8),
                    itemBuilder: (context, index) {
                      final s = filtered[index];
                      return Card(
                        child: ListTile(
                          contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                          onTap: () => Navigator.of(context).push(
                            MaterialPageRoute(builder: (_) => SupplierDetailScreen(supplier: s)),
                          ),
                          leading: CircleAvatar(
                            backgroundColor: AppColors.warning.withValues(alpha: 0.12),
                            child: Icon(Icons.local_shipping, color: AppColors.warning, size: 22),
                          ),
                          title: Text(s.companyName, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                          subtitle: Text(
                            s.name.isNotEmpty ? '${s.name} • ${s.phone}' : s.phone,
                            style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
                          ),
                          trailing: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            crossAxisAlignment: CrossAxisAlignment.end,
                            children: [
                              Text(
                                s.outstandingDue > 0 ? "${l10n.translate('payable_label')}${CurrencyFormatter.format(s.outstandingDue)}" : l10n.translate('settled'),
                                style: TextStyle(
                                  fontSize: 13,
                                  fontWeight: FontWeight.bold,
                                  color: s.outstandingDue > 0 ? AppColors.warning : AppColors.success,
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
