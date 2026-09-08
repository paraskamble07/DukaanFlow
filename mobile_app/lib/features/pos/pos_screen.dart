import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/constants/app_colors.dart';
import '../../core/utils/currency_formatter.dart';
import '../../providers/pos_provider.dart';
import '../../providers/product_provider.dart';
import '../../providers/customer_provider.dart';
import '../../models/product_model.dart';
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
                    const Text('Complete Sale & Payment', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                    IconButton(icon: const Icon(Icons.close), onPressed: () => Navigator.of(context).pop()),
                  ],
                ),
                const Divider(),
                const SizedBox(height: 8),

                // Payment Method Selector Chips
                const Text('Payment Mode', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                const SizedBox(height: 8),
                Wrap(
                  spacing: 8,
                  children: ['CASH', 'UPI', 'CARD', 'CREDIT'].map((method) {
                    final isSelected = state.paymentMethod == method;
                    return ChoiceChip(
                      label: Text(method == 'CREDIT' ? 'Khata (Udhar)' : method),
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
                          const Text('Discount (₹)', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
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
                          const Text('Paid Amount (₹)', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
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
                    color: AppColors.backgroundLight,
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Column(
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          const Text('Grand Total:'),
                          Text(CurrencyFormatter.format(state.grandTotal), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: AppColors.primary)),
                        ],
                      ),
                      const SizedBox(height: 4),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          const Text('Balance Due:'),
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
                          final notifier = ref.read(posProvider.notifier);
                          final wasEmpty = ref.read(posProvider).items.isEmpty;
                          final res = await notifier.checkout();
                          if (!context.mounted) return;
                          if (res != null) {
                            Navigator.of(context).pop(); // Close sheet
                            showDialog(
                              context: context,
                              barrierDismissible: false,
                              builder: (_) => SaleSuccessDialog(saleData: res),
                            );
                          } else if (!wasEmpty &&
                              ref.read(posProvider).items.isEmpty) {
                            // Cart went from non-empty to empty without a
                            // success dialog → the bill was queued offline.
                            Navigator.of(context).pop(); // Close sheet
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(
                                content: Text(
                                  'No internet — bill saved on this phone. It will upload automatically when online.',
                                ),
                                duration: Duration(seconds: 4),
                              ),
                            );
                          } else if (ref.read(posProvider).error != null) {
                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(
                                content: Text(ref.read(posProvider).error!),
                              ),
                            );
                          }
                        },
                  child: state.isSubmitting
                      ? const CircularProgressIndicator(color: Colors.white)
                      : const Text('Generate Invoice & Bill'),
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
    final customersAsync = ref.watch(customerListProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('POS Counter Sale'),
        actions: [
          IconButton(
            icon: const Icon(Icons.qr_code_scanner),
            tooltip: 'Scan Barcode',
            onPressed: () => Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => const ImeiScannerScreen()),
            ),
          ),
          if (posState.items.isNotEmpty)
            IconButton(
              icon: const Icon(Icons.delete_sweep_outlined),
              tooltip: 'Clear Cart',
              onPressed: () => ref.read(posProvider.notifier).clearCart(),
            ),
        ],
      ),
      body: Column(
        children: [
          // Customer Selection Header
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            color: Colors.white,
            child: Row(
              children: [
                const Icon(Icons.person_outline, size: 20, color: AppColors.primary),
                const SizedBox(width: 8),
                Expanded(
                  child: customersAsync.when(
                    data: (customers) => DropdownButtonHideUnderline(
                      child: DropdownButton<int?>(
                        value: posState.selectedCustomerId,
                        hint: const Text('Walk-in / Cash Customer', style: TextStyle(fontSize: 14)),
                        isExpanded: true,
                        items: [
                          const DropdownMenuItem(value: null, child: Text('Walk-in / Cash Customer')),
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
                    loading: () => const Text('Loading customers...'),
                    error: (_, __) => const Text('Walk-in Customer'),
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
                        Icon(Icons.shopping_cart_outlined, size: 64, color: AppColors.textSecondary.withOpacity(0.4)),
                        const SizedBox(height: 12),
                        const Text('Cart is empty', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                        const Text('Select products from catalog below to add.', style: TextStyle(color: AppColors.textSecondary, fontSize: 13)),
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
            decoration: const BoxDecoration(
              color: Colors.white,
              boxShadow: [BoxShadow(color: Colors.black12, blurRadius: 4, offset: Offset(0, -2))],
            ),
            child: Column(
              children: [
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  child: TextField(
                    controller: _searchController,
                    decoration: const InputDecoration(
                      hintText: 'Search phones, chargers, accessories...',
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
                              color: AppColors.backgroundLight,
                              borderRadius: BorderRadius.circular(8),
                              border: Border.all(color: AppColors.borderLight),
                            ),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(p.name, maxLines: 2, overflow: TextOverflow.ellipsis, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
                                const Spacer(),
                                Text(CurrencyFormatter.format(p.sellingPrice), style: const TextStyle(fontWeight: FontWeight.bold, color: AppColors.primary, fontSize: 13)),
                                Text('${p.stockQuantity} in stock', style: const TextStyle(fontSize: 10, color: AppColors.textSecondary)),
                              ],
                            ),
                          ),
                        );
                      },
                    ),
                    loading: () => const Center(child: CircularProgressIndicator()),
                    error: (err, _) => Center(child: Text('Error: $err')),
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
                          const Text('Total Payable', style: TextStyle(fontSize: 11, color: AppColors.textSecondary)),
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
                          label: const Text('Proceed to Bill'),
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
