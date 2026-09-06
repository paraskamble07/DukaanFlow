import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/constants/api_constants.dart';
import '../../models/product_model.dart';
import '../../providers/auth_provider.dart';
import '../../providers/product_provider.dart';

class ProductFormScreen extends ConsumerStatefulWidget {
  final ProductModel? product;

  const ProductFormScreen({super.key, this.product});

  @override
  ConsumerState<ProductFormScreen> createState() => _ProductFormScreenState();
}

class _ProductFormScreenState extends ConsumerState<ProductFormScreen> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _nameController;
  late final TextEditingController _brandController;
  late final TextEditingController _costController;
  late final TextEditingController _priceController;
  late final TextEditingController _stockController;
  late final TextEditingController _minStockController;
  late final TextEditingController _warrantyController;
  late final TextEditingController _barcodeController;
  bool _isImeiTracked = false;
  bool _isSubmitting = false;

  @override
  void initState() {
    super.initState();
    final p = widget.product;
    _nameController = TextEditingController(text: p?.name ?? '');
    _brandController = TextEditingController(text: p?.brand ?? '');
    _costController = TextEditingController(text: p?.purchasePrice.toString() ?? '');
    _priceController = TextEditingController(text: p?.sellingPrice.toString() ?? '');
    _stockController = TextEditingController(text: p?.stockQuantity.toString() ?? '1');
    _minStockController = TextEditingController(text: p?.minStock.toString() ?? '5');
    _warrantyController = TextEditingController(text: p?.warrantyMonths.toString() ?? '12');
    _barcodeController = TextEditingController(text: p?.barcode ?? '');
    _isImeiTracked = p?.isImeiTracked ?? false;
  }

  @override
  void dispose() {
    _nameController.dispose();
    _brandController.dispose();
    _costController.dispose();
    _priceController.dispose();
    _stockController.dispose();
    _minStockController.dispose();
    _warrantyController.dispose();
    _barcodeController.dispose();
    super.dispose();
  }

  Future<void> _saveProduct() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _isSubmitting = true);

    final client = ref.read(apiClientProvider);
    final payload = {
      'name': _nameController.text.trim(),
      'brand': _brandController.text.trim(),
      'purchase_price': double.tryParse(_costController.text) ?? 0.0,
      'selling_price': double.tryParse(_priceController.text) ?? 0.0,
      'stock_quantity': int.tryParse(_stockController.text) ?? 0,
      'min_stock': int.tryParse(_minStockController.text) ?? 5,
      'warranty_months': int.tryParse(_warrantyController.text) ?? 0,
      'barcode': _barcodeController.text.trim(),
      'is_imei_tracked': _isImeiTracked,
    };

    try {
      if (widget.product != null) {
        await client.dio.put('${ApiConstants.products}${widget.product!.id}/', data: payload);
      } else {
        await client.dio.post(ApiConstants.products, data: payload);
      }
      ref.refresh(productsListProvider);
      if (mounted) {
        Navigator.of(context).pop();
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Product saved successfully!')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error saving product: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(widget.product != null ? 'Edit Product' : 'Add New Product')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20.0),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('Product Name / Model *', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
              const SizedBox(height: 6),
              TextFormField(
                controller: _nameController,
                decoration: const InputDecoration(hintText: 'e.g. Samsung Galaxy A56 5G (8GB/128GB)'),
                validator: (v) => (v == null || v.isEmpty) ? 'Please enter name' : null,
              ),
              const SizedBox(height: 14),

              Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('Brand', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                        const SizedBox(height: 6),
                        TextFormField(
                          controller: _brandController,
                          decoration: const InputDecoration(hintText: 'e.g. Apple, Samsung'),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('Barcode / SKU', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                        const SizedBox(height: 6),
                        TextFormField(
                          controller: _barcodeController,
                          decoration: const InputDecoration(hintText: 'Scan or code'),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 14),

              Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('Cost Price (₹) *', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                        const SizedBox(height: 6),
                        TextFormField(
                          controller: _costController,
                          keyboardType: TextInputType.number,
                          decoration: const InputDecoration(hintText: '0.00'),
                          validator: (v) => (v == null || v.isEmpty) ? 'Enter cost' : null,
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('Selling MRP (₹) *', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                        const SizedBox(height: 6),
                        TextFormField(
                          controller: _priceController,
                          keyboardType: TextInputType.number,
                          decoration: const InputDecoration(hintText: '0.00'),
                          validator: (v) => (v == null || v.isEmpty) ? 'Enter price' : null,
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 14),

              Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('Initial Stock', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                        const SizedBox(height: 6),
                        TextFormField(
                          controller: _stockController,
                          keyboardType: TextInputType.number,
                          decoration: const InputDecoration(hintText: '1'),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('Low Stock Alert', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                        const SizedBox(height: 6),
                        TextFormField(
                          controller: _minStockController,
                          keyboardType: TextInputType.number,
                          decoration: const InputDecoration(hintText: '5'),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),

              SwitchListTile(
                contentPadding: EdgeInsets.zero,
                title: const Text('Track Serial / IMEI Numbers', style: TextStyle(fontWeight: FontWeight.bold)),
                subtitle: const Text('Enable for Smartphones and Laptops to track individual 15-digit IMEIs.'),
                value: _isImeiTracked,
                onChanged: (val) => setState(() => _isImeiTracked = val),
              ),
              const SizedBox(height: 24),

              ElevatedButton(
                onPressed: _isSubmitting ? null : _saveProduct,
                child: _isSubmitting ? const CircularProgressIndicator() : const Text('Save Product'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
