import 'package:flutter/material.dart';
import '../../core/localization/app_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../core/constants/api_constants.dart';
import '../../core/constants/app_colors.dart';
import '../../core/utils/currency_formatter.dart';
import '../../models/supplier_model.dart';
import '../../providers/auth_provider.dart';
import '../../providers/business_provider.dart';
import '../purchases/purchase_form_screen.dart';

class SupplierDetailScreen extends ConsumerStatefulWidget {
  final SupplierModel supplier;
  const SupplierDetailScreen({super.key, required this.supplier});

  @override
  ConsumerState<SupplierDetailScreen> createState() => _SupplierDetailScreenState();
}

class _SupplierDetailScreenState extends ConsumerState<SupplierDetailScreen> {
  final _payAmountController = TextEditingController();
  String _payMethod = 'CASH';
  bool _isPaying = false;

  @override
  void dispose() {
    _payAmountController.dispose();
    super.dispose();
  }

  Future<void> _recordPayment() async {
    final amt = double.tryParse(_payAmountController.text);
    if (amt == null || amt <= 0) return;
    setState(() => _isPaying = true);

    final client = ref.read(apiClientProvider);
    try {
      final res = await client.dio.post(
        ApiConstants.supplierPayment,
        data: {
          'supplier_id': widget.supplier.id,
          'amount': amt,
          'payment_method': _payMethod,
        },
      );
      if (res.statusCode == 201 && mounted) {
        final l10n = AppLocalizations.of(context);
        ref.invalidate(supplierListProvider);
        Navigator.of(context).pop(); // close payment sheet
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("${l10n.translate('payment_of')}${CurrencyFormatter.format(amt)}${l10n.translate('recorded_payable')}${CurrencyFormatter.format(res.data['remaining_due'] ?? 0)}")),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(AppLocalizations.of(context).translate('could_not_record_supplier_payment'))),
        );
      }
    } finally {
      if (mounted) setState(() => _isPaying = false);
    }
  }

  void _showPaymentSheet() {
    _payAmountController.text = widget.supplier.outstandingDue > 0
        ? widget.supplier.outstandingDue.toStringAsFixed(0)
        : '';
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) => StatefulBuilder(
        builder: (context, setSheetState) {
          final l10n = AppLocalizations.of(context);
          return Padding(
          padding: EdgeInsets.only(
            bottom: MediaQuery.of(context).viewInsets.bottom + 20,
            left: 20, right: 20, top: 20,
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(l10n.translate('pay_supplier'), style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              const Divider(),
              const SizedBox(height: 8),
              Text(l10n.translate('amount_paid_label'), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
              const SizedBox(height: 6),
              TextField(
                controller: _payAmountController,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(hintText: '0.00'),
              ),
              const SizedBox(height: 14),
              Text(l10n.translate('payment_mode'), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
              const SizedBox(height: 6),
              Wrap(
                spacing: 8,
                children: ['CASH', 'UPI', 'BANK'].map((m) {
                  return ChoiceChip(
                    label: Text(m),
                    selected: _payMethod == m,
                    onSelected: (_) => setSheetState(() => _payMethod = m),
                  );
                }).toList(),
              ),
              const SizedBox(height: 20),
              ElevatedButton(
                onPressed: _isPaying ? null : _recordPayment,
                child: _isPaying
                    ? const SizedBox(height: 22, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                    : Text(l10n.translate('record_supplier_payment')),
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
    final l10n = AppLocalizations.of(context);
    final s = widget.supplier;
    return Scaffold(
      appBar: AppBar(title: Text(s.companyName, style: const TextStyle(fontSize: 17))),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                children: [
                  Row(
                    children: [
                      CircleAvatar(
                        radius: 28,
                        backgroundColor: AppColors.warning.withValues(alpha: 0.12),
                        child: Icon(Icons.local_shipping, color: AppColors.warning, size: 30),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(s.companyName, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.bold)),
                            if (s.name.isNotEmpty) Text(s.name, style: const TextStyle(fontSize: 13, color: AppColors.textSecondary)),
                          ],
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      Expanded(
                        child: OutlinedButton.icon(
                          onPressed: () async {
                            final uri = Uri(scheme: 'tel', path: s.phone);
                            if (await canLaunchUrl(uri)) await launchUrl(uri);
                          },
                          icon: const Icon(Icons.call, size: 18),
                          label: Text(l10n.translate('call')),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: OutlinedButton.icon(
                          onPressed: () => Navigator.of(context).push(
                            MaterialPageRoute(builder: (_) => PurchaseFormScreen(supplier: s)),
                          ),
                          icon: const Icon(Icons.add_shopping_cart, size: 18),
                          label: Text(l10n.translate('purchase')),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                children: [
                  _kvRow(l10n.translate('total_purchases'), CurrencyFormatter.format(s.totalPurchases), AppColors.primary),
                  _kvRow(l10n.translate('total_paid'), CurrencyFormatter.format(s.totalPaid), AppColors.success),
                  const Divider(),
                  _kvRow(
                    l10n.translate('outstanding_payable'),
                    CurrencyFormatter.format(s.outstandingDue),
                    s.outstandingDue > 0 ? AppColors.warning : AppColors.success,
                    bold: true,
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          if (s.outstandingDue > 0)
            ElevatedButton.icon(
              onPressed: _showPaymentSheet,
              icon: const Icon(Icons.payments_outlined),
              label: Text(l10n.translate('record_payment_to_supplier')),
            ),
          const SizedBox(height: 24),
          if (s.gstin != null && s.gstin!.isNotEmpty) _kvRow(l10n.translate('gstin_label'), s.gstin!, AppColors.textPrimary),
          if (s.email != null && s.email!.isNotEmpty) _kvRow(l10n.translate('email_label'), s.email!, AppColors.textPrimary),
          if (s.address != null && s.address!.isNotEmpty) _kvRow(l10n.translate('address_label'), s.address!, AppColors.textPrimary),
        ],
      ),
    );
  }

  Widget _kvRow(String label, String value, Color color, {bool bold = false}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(fontSize: 13, color: AppColors.textSecondary)),
          Text(
            value,
            style: TextStyle(fontSize: 14, fontWeight: bold ? FontWeight.bold : FontWeight.w600, color: color),
          ),
        ],
      ),
    );
  }
}
