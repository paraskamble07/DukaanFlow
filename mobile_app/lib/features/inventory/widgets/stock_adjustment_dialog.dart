import 'package:flutter/material.dart';
import '../../../core/constants/api_constants.dart';
import '../../../core/localization/app_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../providers/auth_provider.dart';
import '../../../providers/product_provider.dart';

class StockAdjustmentDialog extends ConsumerStatefulWidget {
  final int productId;
  final String productName;
  final int currentStock;

  const StockAdjustmentDialog({
    super.key,
    required this.productId,
    required this.productName,
    required this.currentStock,
  });

  @override
  ConsumerState<StockAdjustmentDialog> createState() => _StockAdjustmentDialogState();
}

class _StockAdjustmentDialogState extends ConsumerState<StockAdjustmentDialog> {
  String _action = 'INCREASE';
  int _quantity = 1;
  String _reason = 'Audit Correction';
  final _notesController = TextEditingController();
  bool _isSubmitting = false;

  final _reasons = [
    ('Audit Correction', 'reason_audit'),
    ('Damaged / Defective', 'reason_damaged'),
    ('Missing / Lost', 'reason_missing'),
    ('Customer Return', 'reason_return'),
    ('Supplier Inward', 'reason_inward'),
  ];

  Future<void> _submitAdjustment() async {
    setState(() => _isSubmitting = true);
    final client = ref.read(apiClientProvider);

    try {
      final res = await client.dio.post(
        ApiConstants.stockAdjust,
        data: {
          'product_id': widget.productId,
          'action': _action,
          'quantity': _quantity,
          'reason': _reason,
          'notes': _notesController.text.trim(),
        },
      );

      if (res.statusCode == 200 && mounted) {
        ref.invalidate(productsListProvider);
        Navigator.of(context).pop(true);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(res.data['message'] ?? AppLocalizations.of(context).translate('stock_adjusted_success'))),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("${AppLocalizations.of(context).translate('error_prefix')}${e.toString()}")),
        );
      }
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text("${AppLocalizations.of(context).translate('adjust_stock_for')}${widget.productName}", style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text("${AppLocalizations.of(context).translate('current_stock_units')}${widget.currentStock}${AppLocalizations.of(context).translate('units_suffix')}", style: const TextStyle(fontWeight: FontWeight.bold)),
          const SizedBox(height: 12),
          Row(
            children: [
              ChoiceChip(
                label: Text(AppLocalizations.of(context).translate('add_stock')),
                selected: _action == 'INCREASE',
                onSelected: (_) => setState(() => _action = 'INCREASE'),
              ),
              const SizedBox(width: 8),
              ChoiceChip(
                label: Text(AppLocalizations.of(context).translate('deduct_stock')),
                selected: _action == 'DECREASE',
                onSelected: (_) => setState(() => _action = 'DECREASE'),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(AppLocalizations.of(context).translate('quantity'), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
          Row(
            children: [
              IconButton(
                icon: const Icon(Icons.remove_circle_outline),
                onPressed: _quantity > 1 ? () => setState(() => _quantity--) : null,
              ),
              Text('$_quantity', style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              IconButton(
                icon: const Icon(Icons.add_circle_outline),
                onPressed: () => setState(() => _quantity++),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(AppLocalizations.of(context).translate('reason'), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
          DropdownButton<String>(
            value: _reason,
            isExpanded: true,
            items: _reasons.map((r) => DropdownMenuItem(value: r.$1, child: Text(AppLocalizations.of(context).translate(r.$2)))).toList(),
            onChanged: (v) => setState(() => _reason = v!),
          ),
        ],
      ),
      actions: [
        TextButton(onPressed: () => Navigator.of(context).pop(), child: Text(AppLocalizations.of(context).translate('cancel'))),
        ElevatedButton(
          onPressed: _isSubmitting ? null : _submitAdjustment,
          child: _isSubmitting ? const CircularProgressIndicator() : Text(AppLocalizations.of(context).translate('confirm')),
        ),
      ],
    );
  }
}
