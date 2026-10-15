import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/constants/api_constants.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/utils/currency_formatter.dart';
import '../../../models/customer_model.dart';
import '../../../providers/auth_provider.dart';
import 'receive_payment_modal.dart';

/// Collect-amount dialog: shows the **server-generated** UPI QR for a
/// customer's current outstanding.
///
/// IMPORTANT (master prompt, Phase 6): scanning this QR only opens the
/// customer's UPI app with a pre-filled request. It is NEVER treated as a
/// payment — the payment enters the books only after an authorized user
/// records it (the "Record Received Payment" button below), which is
/// validated server-side.
class UpiQrDialog extends ConsumerStatefulWidget {
  final CustomerModel customer;
  final double outstandingDue;

  const UpiQrDialog({
    super.key,
    required this.customer,
    required this.outstandingDue,
  });

  @override
  ConsumerState<UpiQrDialog> createState() => _UpiQrDialogState();
}

class _UpiQrDialogState extends ConsumerState<UpiQrDialog> {
  bool _loading = true;
  String? _error;
  Uint8List? _qrBytes;
  String _amountText = '';
  String _upiId = '';

  @override
  void initState() {
    super.initState();
    _loadQr();
  }

  Future<void> _loadQr() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final client = ref.read(apiClientProvider);
      final res = await client.dio.get(
        ApiConstants.customerUpiQr(widget.customer.id),
      );
      final data = res.data is Map ? res.data as Map<String, dynamic> : <String, dynamic>{};
      final b64 = data['qr_png_base64'] as String? ?? '';
      _qrBytes = base64Decode(b64);
      _amountText = data['amount']?.toString() ?? '0.00';
      _upiId = data['upi_id']?.toString() ?? '';
    } catch (e) {
      String msg = 'Could not load UPI QR.';
      if (e.toString().contains('400')) {
        msg = 'No UPI ID configured for this shop. The owner can add one in '
              'Settings → Shop Profile (UPI ID).';
      }
      _error = msg;
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _recordPayment() {
    Navigator.of(context).pop();
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (_) => ReceivePaymentModal(
        customerId: widget.customer.id,
        customerName: widget.customer.name,
        outstandingDue: double.tryParse(_amountText) ?? widget.outstandingDue,
        defaultMethodUpi: true,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text('Collect ₹ from ${widget.customer.name}'),
      content: SizedBox(
        width: double.maxFinite,
        child: _loading
            ? const Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  SizedBox(height: 16),
                  CircularProgressIndicator(),
                  SizedBox(height: 12),
                  Text('Generating UPI QR…', style: TextStyle(fontSize: 12)),
                ],
              )
            : _error != null
                ? Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.error_outline, color: AppColors.danger, size: 40),
                      const SizedBox(height: 12),
                      Text(_error!, textAlign: TextAlign.center,
                          style: const TextStyle(fontSize: 13)),
                    ],
                  )
                : Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      if (_qrBytes != null)
                        Container(
                          padding: const EdgeInsets.all(8),
                          decoration: BoxDecoration(
                            border: Border.all(color: AppColors.borderLight),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Image.memory(_qrBytes!, width: 220, height: 220),
                        ),
                      const SizedBox(height: 12),
                      Text(
                        CurrencyFormatter.format(double.tryParse(_amountText) ?? 0),
                        style: const TextStyle(
                            fontSize: 20, fontWeight: FontWeight.bold, color: AppColors.primary),
                      ),
                      const SizedBox(height: 4),
                      Text(_upiId,
                          style: const TextStyle(fontSize: 12, color: AppColors.textSecondary)),
                      const SizedBox(height: 12),
                      Container(
                        padding: const EdgeInsets.all(10),
                        decoration: BoxDecoration(
                          color: const Color(0xFFFFFBEB),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: const Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Icon(Icons.info_outline, size: 16, color: Colors.orange),
                            SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                'Scanning this QR only requests the payment in the '
                                'customer\'s UPI app. Record the payment here only '
                                'after you have actually received it.',
                                style: TextStyle(fontSize: 11.5),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('Close'),
        ),
        if (_error == null && !_loading)
          FilledButton.icon(
            onPressed: _recordPayment,
            icon: const Icon(Icons.check_circle_outline, size: 18),
            label: const Text('Record Received Payment'),
          ),
      ],
    );
  }
}
