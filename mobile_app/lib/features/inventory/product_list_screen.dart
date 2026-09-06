import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/constants/app_colors.dart';
import '../../core/utils/currency_formatter.dart';
import '../../providers/product_provider.dart';
import '../../shared_widgets/empty_state_view.dart';
import 'product_form_screen.dart';
import 'widgets/stock_adjustment_dialog.dart';
import 'imei_scanner_screen.dart';

class ProductListScreen extends ConsumerWidget {
  const ProductListScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final productsAsync = ref.watch(productsListProvider);
    final filter = ref.watch(productFilterProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Products & Stock'),
        actions: [
          IconButton(
            icon: const Icon(Icons.qr_code_scanner),
            tooltip: 'Barcode Scanner',
            onPressed: () => Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => const ImeiScannerScreen()),
            ),
          ),
          IconButton(
            icon: const Icon(Icons.add),
            tooltip: 'Add Product',
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
                hintText: 'Search product, brand, SKU or barcode...',
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
                  label: const Text('All Products'),
                  selected: filter.stockStatus == null,
                  onSelected: (_) => ref.read(productFilterProvider.notifier).state =
                      ref.read(productFilterProvider).copyWith(stockStatus: null),
                ),
                const SizedBox(width: 8),
                FilterChip(
                  label: const Text('Low Stock ⚠️'),
                  selected: filter.stockStatus == 'low',
                  onSelected: (_) => ref.read(productFilterProvider.notifier).state =
                      ref.read(productFilterProvider).copyWith(stockStatus: 'low'),
                ),
                const SizedBox(width: 8),
                FilterChip(
                  label: const Text('Out of Stock ❌'),
                  selected: filter.stockStatus == 'out',
                  onSelected: (_) => ref.read(productFilterProvider.notifier).state =
                      ref.read(productFilterProvider).copyWith(stockStatus: 'out'),
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
                error: (err, _) => Center(child: Text('Error loading products: $err')),
                data: (products) {
                  if (products.isEmpty) {
                    return EmptyStateView(
                      icon: Icons.inventory_2_outlined,
                      title: 'No Products Found',
                      description: 'Start by adding your mobile phones, chargers, and accessories.',
                      actionLabel: 'Add First Product',
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
                            MaterialPageRoute(builder: (_) => ProductFormScreen(product: p)),
                          ),
                          child: Padding(
                            padding: const EdgeInsets.all(12.0),
                            child: Row(
                              children: [
                                CircleAvatar(
                                  radius: 22,
                                  backgroundColor: AppColors.primary.withOpacity(0.08),
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
                                        'Cost: ${CurrencyFormatter.format(p.purchasePrice)} | Margin: ${p.profitMargin}%',
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
                                                color: AppColors.primary.withOpacity(0.1),
                                                borderRadius: BorderRadius.circular(4),
                                              ),
                                              child: const Text('IMEI Tracked', style: TextStyle(fontSize: 10, color: AppColors.primary, fontWeight: FontWeight.bold)),
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
                                            ? AppColors.danger.withOpacity(0.12)
                                            : (p.isLowStock ? AppColors.warning.withOpacity(0.12) : AppColors.success.withOpacity(0.12)),
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
                                      tooltip: 'Adjust Stock',
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
        ],
      ),
    );
  }
}
