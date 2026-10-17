import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/constants/app_colors.dart';
import '../../core/localization/app_localizations.dart';
import '../../core/utils/currency_formatter.dart';
import '../../providers/pos_provider.dart';
import '../../providers/product_provider.dart';
import '../../providers/customer_provider.dart';
import '../../shared_widgets/sync_status_banner.dart';
import '../inventory/imei_scanner_screen.dart';
import 'widgets/cart_item_tile.dart';
import 'widgets/sale_success_dialog.dart';

class PosScreen extends ConsumerStatefulWidget {
  const PosScreen({super.key});

  @override
  ConsumerState<PosScreen> createState() => _PosScreenState();
}

class _PosScreenState extends ConsumerState<PosScreen> {
  final TextEditingController _searchController = TextEditingController();
  final TextEditingController _discountController = TextEditingController(text: '0');
  final TextEditingController _paidController = TextEditingController();

  @override
  void dispose() {
    _searchController.dispose();
    _discountController.dispose();
    _paidController.dispose();
    super.dispose();
  }

  void _showCheckoutSheet() {
    final posState = ref.read(posProvider);
    _paidController.text = posState.paidAmount.toStringAsFixed(0);

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) => Consumer(
        builder: (context, ref, _) {
          final state = ref.watch(posProvider);
          final l10n = AppLocalizations.of(context);
          return Padding(
            padding: EdgeInsets.only(
              bottom: MediaQuery.of(context).viewInsets.bottom + 20,
              left: 20,
              right: 20,
              top: 20,
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(l10n.translate('complete_sale_payment'), style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                    IconButton(icon: const Icon(Icons.close), onPressed: () => Navigator.of(context).pop()),
                  ],
                ),
                const Divider(),
                const SizedBox(height: 8),

                // Payment Method Selector Chips
                Text(l10n.translate('payment_mode'), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                const SizedBox(height: 8),
                Wrap(
                  spacing: 8,
                  children: ['CASH', 'UPI', 'CARD', 'CREDIT'].map((method) {
                    final isSelected = state.paymentMethod == method;
                    return ChoiceChip(
                      label: Text(method == 'CREDIT' ? l10n.translate('khata_udhar') : method),
                      selected: isSelected,
                      onSelected: (_) => ref.read(posProvider.notifier).setPaymentMethod(method),
                    );
                  }).toList(),
                ),
                const SizedBox(height: 16),

                Row(
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(l10n.translate('discount'), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                          const SizedBox(height: 4),
                          TextField(
                            controller: _discountController,
                            keyboardType: TextInputType.number,
                            decoration: const InputDecoration(hintText: '0'),
                            onChanged: (v) => ref.read(posProvider.notifier).setExtraDiscount(double.tryParse(v) ?? 0.0),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(l10n.translate('paid_amount'), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                          const SizedBox(height: 4),
                          TextField(
                            controller: _paidController,
                            keyboardType: TextInputType.number,
                            decoration: const InputDecoration(hintText: '0.00'),
                            onChanged: (v) => ref.read(posProvider.notifier).setPaidAmount(double.tryParse(v) ?? 0.0),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),

                // Financial Summary
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Theme.of(context).colorScheme.surface,
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Column(
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text('${l10n.translate('grand_total')}:'),
                          Text(CurrencyFormatter.format(state.grandTotal), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: AppColors.primary)),
                        ],
                      ),
                      const SizedBox(height: 4),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text('${l10n.translate('due_amount')}:'),
                          Text(
                            CurrencyFormatter.format(state.dueAmount),
                            style: TextStyle(
                              fontWeight: FontWeight.bold,
                              fontSize: 14,
                              color: state.dueAmount > 0 ? AppColors.danger : AppColors.success,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 20),

                ElevatedButton(
                  onPressed: state.isSubmitting
                      ? null
                      : () async {
                          final res = await ref.read(posProvider.notifier).checkout();
                          if (!context.mounted) return;
                          if (res != null) {
                            Navigator.of(context).pop(); // Close sheet
                            showDialog(
                              context: context,
                              barrierDismissible: false,
                              builder: (_) => SaleSuccessDialog(saleData: res),
                            );
                          } else if (ref.read(posProvider).offlineQueued) {
                            // Bill saved to the offline queue: same flow as
                            // success, but with the offline notice.
                            Navigator.of(context).pop(); // Close sheet
                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(
                                content: Row(
                                  children: [
                                    const Icon(Icons.wifi_off_rounded,
                                        color: Colors.white, size: 18),
                                    const SizedBox(width: 10),
                                    Expanded(
                                        child: Text(l10n.translate('offline_sale_queued'))),
                                  ],
                                ),
                                duration: const Duration(seconds: 6),
                              ),
                            );
                          }
                        },
                  child: state.isSubmitting
                      ? const CircularProgressIndicator(color: Colors.white)
                      : Text(l10n.translate('generate_invoice')),
                ),
                if (state.error != null)
                  Padding(
                    padding: const EdgeInsets.only(top: 10),
                    child: Row(
                      children: [
                        const Icon(Icons.error_outline, size: 16, color: AppColors.danger),
                        const SizedBox(width: 6),
                        Expanded(
                          child: Text(
                            state.error!,
                            style: const TextStyle(fontSize: 12, color: AppColors.danger),
                          ),
                        ),
                      ],
                    ),
                  ),
              ],
            ),
          );
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final posState = ref.watch(posProvider);
    final productsAsync = ref.watch(productsListProvider);
    final l10n = AppLocalizations.of(context);
    final customersAsync = ref.watch(customerListProvider);

    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.translate('pos_counter_sale')),
        actions: [
          IconButton(
            icon: const Icon(Icons.qr_code_scanner),
            tooltip: l10n.translate('scan_barcode'),
            onPressed: () => Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => const ImeiScannerScreen()),
            ),
          ),
          if (posState.items.isNotEmpty)
            IconButton(
              icon: const Icon(Icons.delete_sweep_outlined),
              tooltip: l10n.translate('clear_cart'),
              onPressed: () => ref.read(posProvider.notifier).clearCart(),
            ),
        ],
      ),
      body: Column(
        children: [
          // Offline / pending-sync indicator
          const SyncStatusBanner(),
          // Customer Selection Header
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            // Theme surface, not Colors.white: this app has a dark theme
            // (Settings → Theme), where a hard white bar would be a
            // glaring mismatch.
            color: Theme.of(context).colorScheme.surface,
            child: Row(
              children: [
                const Icon(Icons.person_outline, size: 20, color: AppColors.primary),
                const SizedBox(width: 8),
                Expanded(
                  child: customersAsync.when(
                    data: (customers) => DropdownButtonHideUnderline(
                      child: DropdownButton<int?>(
                        value: posState.selectedCustomerId,
                        hint: Text(l10n.translate('walk_in_customer'), style: const TextStyle(fontSize: 14)),
                        isExpanded: true,
                        items: [
                          DropdownMenuItem(value: null, child: Text(l10n.translate('walk_in_customer'))),
                          ...customers.map((c) => DropdownMenuItem(
                            value: c.id,
                            child: Text('${c.name} (${c.phone})', style: const TextStyle(fontSize: 14)),
                          )),
                        ],
                        onChanged: (id) {
                          final cust = customers.where((c) => c.id == id).firstOrNull;
                          ref.read(posProvider.notifier).setCustomer(id, cust?.name, cust?.phone);
                        },
                      ),
                    ),
                    loading: () => Text(l10n.translate('loading_customers')),
                    error: (_, __) => Text(l10n.translate('walk_in_customer_short')),
                  ),
                ),
              ],
            ),
          ),
          const Divider(height: 1),

          // Cart List Area
          Expanded(
            child: posState.items.isEmpty
                ? Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.shopping_cart_outlined, size: 64, color: AppColors.textSecondary.withValues(alpha: 0.4)),
                        const SizedBox(height: 12),
                        Text(l10n.translate('cart_empty'), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                        Text(l10n.translate('select_products'), style: const TextStyle(color: AppColors.textSecondary, fontSize: 13)),
                      ],
                    ),
                  )
                : ListView.builder(
                    padding: const EdgeInsets.all(12),
                    itemCount: posState.items.length,
                    itemBuilder: (context, index) {
                      return CartItemTile(
                        item: posState.items[index],
                        index: index,
                        onQuantityChanged: (qty) => ref.read(posProvider.notifier).updateQuantity(index, qty),
                        onRemove: () => ref.read(posProvider.notifier).removeFromCart(index),
                      );
                    },
                  ),
          ),

          // Product Quick Picker Sheet (Bottom Half)
          Container(
            height: 220,
            decoration: BoxDecoration(
              // Same dark-mode fix as the customer selector above.
              color: Theme.of(context).colorScheme.surface,
              boxShadow: const [BoxShadow(color: Colors.black12, blurRadius: 4, offset: Offset(0, -2))],
            ),
            child: Column(
              children: [
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  child: TextField(
                    controller: _searchController,
                    decoration: InputDecoration(
                      hintText: l10n.translate('search_products'),
                      prefixIcon: Icon(Icons.search, size: 20),
                      isDense: true,
                      contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                    ),
                    onChanged: (q) => ref.read(productFilterProvider.notifier).state =
                        ref.read(productFilterProvider).copyWith(query: q),
                  ),
                ),
                Expanded(
                  child: productsAsync.when(
                    data: (products) => ListView.separated(
                      padding: const EdgeInsets.symmetric(horizontal: 12),
                      scrollDirection: Axis.horizontal,
                      itemCount: products.length,
                      separatorBuilder: (_, __) => const SizedBox(width: 8),
                      itemBuilder: (context, index) {
                        final p = products[index];
                        return InkWell(
                          onTap: () => ref.read(posProvider.notifier).addToCart(p),
                          child: Container(
                            width: 130,
                            padding: const EdgeInsets.all(8),
                            decoration: BoxDecoration(
                              color: Theme.of(context).colorScheme.surface,
                              borderRadius: BorderRadius.circular(8),
                              border: Border.all(color: Theme.of(context).dividerColor),
                            ),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(p.name, maxLines: 2, overflow: TextOverflow.ellipsis, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
                                const Spacer(),
                                Text(CurrencyFormatter.format(p.sellingPrice), style: const TextStyle(fontWeight: FontWeight.bold, color: AppColors.primary, fontSize: 13)),
                                Text('${p.stockQuantity} ${l10n.translate('in_stock')}', style: const TextStyle(fontSize: 10, color: AppColors.textSecondary)),
                              ],
                            ),
                          ),
                        );
                      },
                    ),
                    loading: () => const Center(child: CircularProgressIndicator()),
                    error: (err, _) => Center(child: Text("${l10n.translate('error_prefix')}$err")),
                  ),
                ),
                // Bottom Checkout Button Bar
                Container(
                  padding: const EdgeInsets.all(12),
                  child: Row(
                    children: [
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(l10n.translate('total_payable'), style: const TextStyle(fontSize: 11, color: AppColors.textSecondary)),
                          Text(
                            CurrencyFormatter.format(posState.grandTotal),
                            style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: AppColors.primary),
                          ),
                        ],
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: ElevatedButton.icon(
                          onPressed: posState.items.isEmpty ? null : _showCheckoutSheet,
                          icon: const Icon(Icons.arrow_forward),
                          label: Text(l10n.translate('proceed_to_bill')),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
