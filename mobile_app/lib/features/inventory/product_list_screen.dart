import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/constants/app_colors.dart';
import '../../core/localization/app_localizations.dart';
import '../../core/ads/ad_banner.dart';
import '../../core/utils/currency_formatter.dart';
import '../../providers/product_provider.dart';
import '../../shared_widgets/empty_state_view.dart';
import 'product_detail_screen.dart';
import 'product_form_screen.dart';
import 'widgets/stock_adjustment_dialog.dart';
import 'imei_scanner_screen.dart';

class ProductListScreen extends ConsumerWidget {
  const ProductListScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final productsAsync = ref.watch(productsListProvider);
    final filter = ref.watch(productFilterProvider);

    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.translate('inventory')),
        actions: [
          IconButton(
            icon: const Icon(Icons.qr_code_scanner),
            tooltip: AppLocalizations.of(context).translate('barcode_scanner'),
            onPressed: () => Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => const ImeiScannerScreen()),
            ),
          ),
          IconButton(
            icon: const Icon(Icons.add),
            tooltip: AppLocalizations.of(context).translate('add_product'),
            onPressed: () => Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => const ProductFormScreen()),
            ),
          ),
        ],
      ),
      body: Column(
        children: [
          // Search & Filter Header
          Padding(
            padding: const EdgeInsets.all(12.0),
            child: TextField(
              decoration: InputDecoration(
                hintText: l10n.translate('search'),
                prefixIcon: const Icon(Icons.search),
                isDense: true,
                contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                suffixIcon: filter.query.isNotEmpty
                    ? IconButton(
                        icon: const Icon(Icons.clear),
                        onPressed: () => ref.read(productFilterProvider.notifier).state =
                            ref.read(productFilterProvider).copyWith(query: ''),
                      )
                    : null,
              ),
              onChanged: (q) => ref.read(productFilterProvider.notifier).state =
                  ref.read(productFilterProvider).copyWith(query: q),
            ),
          ),

          // Stock Filter Chips
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 12),
            child: Row(
              children: [
                FilterChip(
                  label: Text(l10n.translate('inventory')),
                  selected: filter.stockStatus == null,
                  onSelected: (_) => ref.read(productFilterProvider.notifier).state =
                      ref.read(productFilterProvider).copyWith(stockStatus: null),
                ),
                const SizedBox(width: 8),
                FilterChip(
                  label: Text(l10n.translate('low_stock_alert')),
                  selected: filter.stockStatus == 'low',
                  onSelected: (_) => ref.read(productFilterProvider.notifier).state =
                      ref.read(productFilterProvider).copyWith(stockStatus: 'low'),
                ),
                const SizedBox(width: 8),
                FilterChip(
                  label: Text(l10n.translate('out_of_stock')),
                  selected: filter.stockStatus == 'out',
                  onSelected: (_) => ref.read(productFilterProvider.notifier).state =
                      ref.read(productFilterProvider).copyWith(stockStatus: 'out'),
                ),
                const SizedBox(width: 8),
                FilterChip(
                  label: Text(l10n.translate('dead_stock')),
                  selected: filter.stockStatus == 'dead',
                  onSelected: (_) => ref.read(productFilterProvider.notifier).state =
                      ref.read(productFilterProvider).copyWith(stockStatus: 'dead'),
                ),
              ],
            ),
          ),
          const SizedBox(height: 8),

          // Products List
          Expanded(
            child: RefreshIndicator(
              onRefresh: () async => ref.refresh(productsListProvider),
              child: productsAsync.when(
                loading: () => const Center(child: CircularProgressIndicator()),
                error: (err, _) => Center(child: Text("${AppLocalizations.of(context).translate('error_loading_products')}$err")),
                data: (products) {
                  if (products.isEmpty) {
                    return EmptyStateView(
                      icon: Icons.inventory_2_outlined,
                      title: l10n.translate('no_data'),
                      description: l10n.translate('no_products_desc'),
                      actionLabel: l10n.translate('add_first_product'),
                      onAction: () => Navigator.of(context).push(
                        MaterialPageRoute(builder: (_) => const ProductFormScreen()),
                      ),
                    );
                  }

                  return ListView.separated(
                    padding: const EdgeInsets.all(12),
                    itemCount: products.length,
                    separatorBuilder: (_, __) => const SizedBox(height: 8),
                    itemBuilder: (context, index) {
                      final p = products[index];
                      return Card(
                        child: InkWell(
                          borderRadius: BorderRadius.circular(12),
                          onTap: () => Navigator.of(context).push(
                            MaterialPageRoute(
                                builder: (_) => ProductDetailScreen(productId: p.id)),
                          ),
                          child: Padding(
                            padding: const EdgeInsets.all(12.0),
                            child: Row(
                              children: [
                                CircleAvatar(
                                  radius: 22,
                                  backgroundColor: AppColors.primary.withValues(alpha: 0.08),
                                  child: Icon(
                                    p.isImeiTracked ? Icons.phone_android_rounded : Icons.headphones_rounded,
                                    color: AppColors.primary,
                                  ),
                                ),
                                const SizedBox(width: 12),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        p.name,
                                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                                        maxLines: 1,
                                        overflow: TextOverflow.ellipsis,
                                      ),
                                      const SizedBox(height: 2),
                                      Text(
                                        "${l10n.translate('cost_colon')}${CurrencyFormatter.format(p.purchasePrice)} | ${l10n.translate('margin_colon')}${p.profitMargin}%",
                                        style: const TextStyle(fontSize: 11, color: AppColors.textSecondary),
                                      ),
                                      const SizedBox(height: 4),
                                      Row(
                                        children: [
                                          Text(
                                            CurrencyFormatter.format(p.sellingPrice),
                                            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: AppColors.primary),
                                          ),
                                          const SizedBox(width: 8),
                                          if (p.isImeiTracked)
                                            Container(
                                              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                              decoration: BoxDecoration(
                                                color: AppColors.primary.withValues(alpha: 0.1),
                                                borderRadius: BorderRadius.circular(4),
                                              ),
                                              child: Text(AppLocalizations.of(context).translate('imei_tracked'), style: const TextStyle(fontSize: 10, color: AppColors.primary, fontWeight: FontWeight.bold)),
                                            ),
                                        ],
                                      ),
                                    ],
                                  ),
                                ),
                                Column(
                                  crossAxisAlignment: CrossAxisAlignment.end,
                                  children: [
                                    Container(
                                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                      decoration: BoxDecoration(
                                        color: p.isOutOfStock
                                            ? AppColors.danger.withValues(alpha: 0.12)
                                            : (p.isLowStock ? AppColors.warning.withValues(alpha: 0.12) : AppColors.success.withValues(alpha: 0.12)),
                                        borderRadius: BorderRadius.circular(6),
                                      ),
                                      child: Text(
                                        '${p.stockQuantity} in stock',
                                        style: TextStyle(
                                          fontSize: 12,
                                          fontWeight: FontWeight.bold,
                                          color: p.isOutOfStock ? AppColors.danger : (p.isLowStock ? AppColors.warning : AppColors.success),
                                        ),
                                      ),
                                    ),
                                    const SizedBox(height: 6),
                                    IconButton(
                                      icon: const Icon(Icons.edit_calendar_outlined, size: 18),
                                      tooltip: AppLocalizations.of(context).translate('adjust_stock'),
                                      onPressed: () => showDialog(
                                        context: context,
                                        builder: (_) => StockAdjustmentDialog(
                                          productId: p.id,
                                          productName: p.name,
                                          currentStock: p.stockQuantity,
                                        ),
                                      ),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                          ),
                        ),
                      );
                    },
                  );
                },
              ),
            ),
          ),
          const AdBanner(),
        ],
      ),
    );
  }
}
