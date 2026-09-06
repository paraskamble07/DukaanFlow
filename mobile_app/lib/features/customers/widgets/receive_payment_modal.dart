import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../../core/constants/api_constants.dart';
import '../../../core/constants/app_colors.dart';
import '../../../providers/auth_provider.dart';
import '../../../providers/customer_provider.dart';

class ReceivePaymentModal extends ConsumerStatefulWidget {
  final int customerId;
  final String customerName;
  final double outstandingDue;

  const ReceivePaymentModal({
    super.key,
    required this.customerId,
    required this.customerName,
    required this.outstandingDue,
  });

  @override
  ConsumerState<ReceivePaymentModal> createState() => _ReceivePaymentModalState();
}

class _ReceivePaymentModalState extends ConsumerState<ReceivePaymentModal> {
  late final TextEditingController _amountController;
  final _refController = TextEditingController();
  String _paymentMethod = 'CASH';
  bool _isSubmitting = false;

  @override
  void initState() {
    super.initState();
    _amountController = TextEditingController(text: widget.outstandingDue.toStringAsFixed(0));
  }

  Future<void> _submitPayment() async {
    final amt = double.tryParse(_amountController.text) ?? 0.0;
    if (amt <= 0) return;

    setState(() => _isSubmitting = true);
    final client = ref.read(apiClientProvider);

    try {
      final res = await client.dio.post(
        ApiConstants.customerPayment,
        data: {
          'customer_id': widget.customerId,
          'amount': amt,
          'payment_method': _paymentMethod,
          'reference_number': _refController.text.trim(),
        },
      );

      if (res.statusCode == 201 && mounted) {
        ref.refresh(customerListProvider);
        ref.refresh(customerLedgerProvider(widget.customerId));
        Navigator.of(context).pop();

        final waUrl = res.data['whatsapp_receipt_url'] as String?;
        if (waUrl != null && waUrl.isNotEmpty) {
          showDialog(
            context: context,
            builder: (_) => AlertDialog(
              title: const Text('Payment Recorded!'),
              content: Text('Payment of ₹$amt recorded. Send WhatsApp receipt to customer?'),
              actions: [
                TextButton(onPressed: () => Navigator.of(context).pop(), child: const Text('Skip')),
                ElevatedButton.icon(
                  style: ElevatedButton.styleFrom(backgroundColor: AppColors.whatsapp, foregroundColor: Colors.white),
                  onPressed: () async {
                    Navigator.of(context).pop();
                    final uri = Uri.parse(waUrl);
                    if (await canLaunchUrl(uri)) await launchUrl(uri, mode: LaunchMode.externalApplication);
                  },
                  icon: const Icon(Icons.chat),
                  label: const Text('Send Receipt'),
                ),
              ],
            ),
          );
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error: $e')));
      }
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
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
              Text('Receive Payment: ${widget.customerName}', style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              IconButton(icon: const Icon(Icons.close), onPressed: () => Navigator.of(context).pop()),
            ],
          ),
          const Divider(),
          const SizedBox(height: 8),

          const Text('Amount Received (₹) *', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
          const SizedBox(height: 6),
          TextField(
            controller: _amountController,
            keyboardType: TextInputType.number,
            decoration: const InputDecoration(hintText: '0.00'),
          ),
          const SizedBox(height: 14),

          const Text('Payment Mode', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
          const SizedBox(height: 6),
          Wrap(
            spacing: 8,
            children: ['CASH', 'UPI', 'CARD', 'BANK'].map((m) {
              return ChoiceChip(
                label: Text(m),
                selected: _paymentMethod == m,
                onSelected: (_) => setState(() => _paymentMethod = m),
              );
            }).toList(),
          ),
          const SizedBox(height: 14),

          const Text('UPI Ref / UTR / Cheque (Optional)', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
          const SizedBox(height: 6),
          TextField(
            controller: _refController,
            decoration: const InputDecoration(hintText: 'e.g. 423188992100'),
          ),
          const SizedBox(height: 20),

          ElevatedButton(
            onPressed: _isSubmitting ? null : _submitPayment,
            child: _isSubmitting ? const CircularProgressIndicator() : const Text('Record Payment & Send Receipt'),
          ),
        ],
      ),
    );
  }
}
