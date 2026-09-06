import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/constants/api_constants.dart';
import '../../core/constants/app_colors.dart';
import '../../core/utils/currency_formatter.dart';
import '../../models/product_model.dart';
import '../../models/supplier_model.dart';
import '../../providers/auth_provider.dart';
import '../../providers/business_provider.dart';
import '../../providers/product_provider.dart';

class PurchaseFormScreen extends ConsumerStatefulWidget {
  final SupplierModel? supplier;
  const PurchaseFormScreen({super.key, this.supplier});

  @override
  ConsumerState<PurchaseFormScreen> createState() => _PurchaseFormScreenState();
}

class _PurchaseLine {
  ProductModel product;
  final qtyController = TextEditingController(text: '1');
  final costController = TextEditingController();

  _PurchaseLine(this.product) {
    costController.text = product.purchasePrice.toStringAsFixed(0);
  }
}

class _PurchaseFormScreenState extends ConsumerState<PurchaseFormScreen> {
  final _billController = TextEditingController();
  final _notesController = TextEditingController();
  SupplierModel? _supplier;
  String _paymentMethod = 'CASH';
  final _paidController = TextEditingController();
  final List<_PurchaseLine> _lines = [];
  bool _isSubmitting = false;

  double get _total => _lines.fold(
        0.0,
        (sum, l) => sum + ((double.tryParse(l.costController.text) ?? 0) * (int.tryParse(l.qtyController.text) ?? 0)),
      );

  @override
  void initState() {
    super.initState();
    _supplier = widget.supplier;
    if (_supplier != null) {
      _paidController.text = '0';
    }
  }

  @override
  void dispose() {
    _billController.dispose();
    _notesController.dispose();
    _paidController.dispose();
    for (final l in _lines) {
      l.qtyController.dispose();
      l.costController.dispose();
    }
    super.dispose();
  }

  Future<void> _addProduct() async {
    final productsAsync = await ref.read(productsListProvider.future);
    if (!mounted) return;

    final selected = await showModalBottomSheet<ProductModel>(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) => DraggableScrollableSheet(
        initialChildSize: 0.75,
        maxChildSize: 0.9,
        minChildSize: 0.5,
        expand: false,
        builder: (ctx, scrollController) => Column(
          children: [
            const Padding(
              padding: EdgeInsets.all(16),
              child: Text('Select Product to Purchase', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
            ),
            const Divider(height: 1),
            Expanded(
              child: ListView.builder(
                controller: scrollController,
                itemCount: productsAsync.length,
                itemBuilder: (ctx, i) => ListTile(
                  title: Text(productsAsync[i].name, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold)),
                  subtitle: Text(
                    'Current stock: ${productsAsync[i].stockQuantity}',
                    style: const TextStyle(fontSize: 12),
                  ),
                  trailing: Text(
                    CurrencyFormatter.format(productsAsync[i].purchasePrice),
                    style: const TextStyle(fontSize: 13),
                  ),
                  onTap: () => Navigator.of(ctx).pop(productsAsync[i]),
                ),
              ),
            ),
          ],
        ),
      ),
    );

    if (selected != null) {
      setState(() => _lines.add(_PurchaseLine(selected)));
    }
  }

  Future<void> _submit() async {
    if (_supplier == null || _lines.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please select a supplier and at least one product.')),
      );
      return;
    }

    for (final l in _lines) {
      final qty = int.tryParse(l.qtyController.text) ?? 0;
      final cost = double.tryParse(l.costController.text) ?? 0;
      if (qty <= 0 || cost <= 0) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Every purchase line needs a positive quantity and unit cost.')),
        );
        return;
      }
    }

    setState(() => _isSubmitting = true);
    final client = ref.read(apiClientProvider);

    try {
      final res = await client.dio.post(
        ApiConstants.purchases,
        data: {
          'supplier_id': _supplier!.id,
          'invoice_number': _billController.text.trim(),
          'payment_method': _paymentMethod,
          'paid_amount': double.tryParse(_paidController.text) ?? 0,
          'notes': _notesController.text.trim(),
          'items': _lines.map((l) => {
                'product_id': l.product.id,
                'quantity': int.tryParse(l.qtyController.text) ?? 0,
                'unit_cost': double.tryParse(l.costController.text) ?? 0,
              }).toList(),
        },
      );
      if (res.statusCode == 201 && mounted) {
        ref.refresh(productsListProvider);
        ref.refresh(purchaseListProvider);
        ref.refresh(supplierListProvider);
        Navigator.of(context).pop();
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Purchase recorded. Stock updated (+${_lines.length} lines).')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Could not record purchase. Please try again.')),
        );
      }
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final suppliersAsync = ref.watch(supplierListProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('New Purchase Entry')),
      bottomNavigationBar: SafeArea(
        child: Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: Theme.of(context).cardColor,
            boxShadow: const [BoxShadow(color: Colors.black12, blurRadius: 4, offset: Offset(0, -2))],
          ),
          child: Row(
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Text('Purchase Total', style: TextStyle(fontSize: 11, color: AppColors.textSecondary)),
                  Text(
                    CurrencyFormatter.format(_total),
                    style: const TextStyle(fontSize: 17, fontWeight: FontWeight.bold, color: AppColors.primary),
                  ),
                ],
              ),
              const SizedBox(width: 16),
              Expanded(
                child: ElevatedButton.icon(
                  onPressed: _isSubmitting ? null : _submit,
                  icon: const Icon(Icons.inventory),
                  label: _isSubmitting ? const Text('Saving...') : const Text('Save & Increase Stock'),
                ),
              ),
            ],
          ),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Supplier selector
            suppliersAsync.when(
              loading: () => const LinearProgressIndicator(),
              error: (_, __) => const Text('Could not load suppliers.'),
              data: (suppliers) => DropdownButtonFormField<SupplierModel>(
                value: _supplier,
                isExpanded: true,
                decoration: const InputDecoration(labelText: 'Supplier / Distributor *'),
                items: suppliers
                    .map((s) => DropdownMenuItem(value: s, child: Text(s.companyName, overflow: TextOverflow.ellipsis)))
                    .toList(),
                onChanged: (s) => setState(() => _supplier = s),
              ),
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _billController,
              decoration: const InputDecoration(labelText: 'Supplier Bill / Invoice No (Optional)'),
            ),
            const SizedBox(height: 20),

            // Items
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text('PRODUCTS', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppColors.textSecondary, letterSpacing: 1)),
                TextButton.icon(
                  onPressed: _addProduct,
                  icon: const Icon(Icons.add, size: 18),
                  label: const Text('Add Product'),
                ),
              ],
            ),
            ..._lines.asMap().entries.map(
                  (entry) => Card(
                    child: Padding(
                      padding: const EdgeInsets.all(12),
                      child: Column(
                        children: [
                          Row(
                            children: [
                              Expanded(
                                child: Text(
                                  entry.value.product.name,
                                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                                ),
                              ),
                              IconButton(
                                icon: const Icon(Icons.close, size: 18, color: AppColors.danger),
                                onPressed: () => setState(() => _lines.removeAt(entry.key)),
                              ),
                            ],
                          ),
                          const SizedBox(height: 8),
                          Row(
                            children: [
                              Expanded(
                                child: TextField(
                                  controller: entry.value.qtyController,
                                  keyboardType: TextInputType.number,
                                  decoration: const InputDecoration(labelText: 'Qty', isDense: true),
                                  onChanged: (_) => setState(() {}),
                                ),
                              ),
                              const SizedBox(width: 12),
                              Expanded(
                                child: TextField(
                                  controller: entry.value.costController,
                                  keyboardType: TextInputType.number,
                                  decoration: const InputDecoration(labelText: 'Unit Cost ₹', isDense: true),
                                  onChanged: (_) => setState(() {}),
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ),
                ),

            const SizedBox(height: 20),
            const Text('Payment', style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              children: ['CASH', 'UPI', 'BANK', 'CREDIT'].map((m) {
                return ChoiceChip(
                  label: Text(m == 'CREDIT' ? 'Khata (Pay Later)' : m),
                  selected: _paymentMethod == m,
                  onSelected: (_) => setState(() => _paymentMethod = m),
                );
              }).toList(),
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _paidController,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(labelText: 'Amount Paid Now (₹)', hintText: '0'),
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _notesController,
              maxLines: 2,
              decoration: const InputDecoration(labelText: 'Notes (Optional)'),
            ),
          ],
        ),
      ),
    );
  }
}
