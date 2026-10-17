import 'package:flutter/material.dart';
import '../../../core/localization/app_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:dio/dio.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../../core/constants/api_constants.dart';
import '../../../core/constants/app_colors.dart';
import '../../../providers/auth_provider.dart';
import '../../../providers/customer_provider.dart';

class ReceivePaymentModal extends ConsumerStatefulWidget {
  final int customerId;
  final String customerName;
  final double outstandingDue;
  final bool defaultMethodUpi;

  const ReceivePaymentModal({
    super.key,
    required this.customerId,
    required this.customerName,
    required this.outstandingDue,
    this.defaultMethodUpi = false,
  });

  @override
  ConsumerState<ReceivePaymentModal> createState() => _ReceivePaymentModalState();
}

class _ReceivePaymentModalState extends ConsumerState<ReceivePaymentModal> {
  late final TextEditingController _amountController;
  final _refController = TextEditingController();
  late String _paymentMethod;
  bool _isSubmitting = false;

  @override
  void initState() {
    super.initState();
    _paymentMethod = widget.defaultMethodUpi ? 'UPI' : 'CASH';
    // Exact prefill: rounding the due up here (toStringAsFixed(0)) would
    // hand the user an amount the server then rejects as an overpayment
    // whenever the due carries paise (e.g. due 6,549.50 -> prefill 6,550).
    final due = widget.outstandingDue;
    _amountController = TextEditingController(
      text: due == due.roundToDouble()
          ? due.toStringAsFixed(0)
          : due.toStringAsFixed(2),
    );
  }

  Future<void> _submitPayment() async {
    final l10n = AppLocalizations.of(context);
    final amt = double.tryParse(_amountController.text) ?? 0.0;
    // A blank/cleared field used to no-op silently on tap — tell the user
    // why nothing is happening instead.
    if (amt <= 0) {
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text(l10n.translate('enter_valid_amount'))));
      return;
    }

    setState(() => _isSubmitting = true);
    final client = ref.read(apiClientProvider);

    try {
      final res = await client.dio.post(
        ApiConstants.customerPayment,
        data: {
          'customer_id': widget.customerId,
          // Send an exact 2-decimal string, never a raw double: a JSON
          // float can arrive as 0.30000000000000004 and the server's
          // overpayment guard would trip on money that is actually correct.
          'amount': amt.toStringAsFixed(2),
          'payment_method': _paymentMethod,
          'reference_number': _refController.text.trim(),
        },
      );

      if (res.statusCode == 201 && mounted) {
        ref.invalidate(customerListProvider);
        ref.invalidate(customerLedgerProvider(widget.customerId));
        Navigator.of(context).pop();

        final waUrl = res.data['whatsapp_receipt_url'] as String?;
        if (waUrl != null && waUrl.isNotEmpty) {
          showDialog(
            context: context,
            builder: (_) => AlertDialog(
              title: Text(l10n.translate('payment_recorded_title')),
              content: Text("${l10n.translate('payment_of_amt')}$amt${l10n.translate('recorded_send_receipt')}"),
              actions: [
                TextButton(onPressed: () => Navigator.of(context).pop(), child: Text(l10n.translate('skip'))),
                ElevatedButton.icon(
                  style: ElevatedButton.styleFrom(backgroundColor: AppColors.whatsapp, foregroundColor: Colors.white),
                  onPressed: () async {
                    Navigator.of(context).pop();
                    final uri = Uri.parse(waUrl);
                    if (await canLaunchUrl(uri)) await launchUrl(uri, mode: LaunchMode.externalApplication);
                  },
                  icon: const Icon(Icons.chat),
                  label: Text(l10n.translate('send_receipt')),
                ),
              ],
            ),
          );
        }
      }
    } on DioException catch (e) {
      if (mounted) {
        // Surface the backend's own reason (e.g. overpayment rejection)
        // instead of a raw status blob.
        final serverError = e.response?.data;
        final msg = (serverError is Map && serverError['error'] is String)
            ? serverError['error'] as String
            : l10n.translate('could_not_record_payment_retry');
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text("${l10n.translate('could_not_record_payment')}$e")));
      }
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
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
              Text("${l10n.translate('receive_payment_for')}${widget.customerName}", style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              IconButton(icon: const Icon(Icons.close), onPressed: () => Navigator.of(context).pop()),
            ],
          ),
          const Divider(),
          const SizedBox(height: 8),

          Text(l10n.translate('amount_received'), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
          const SizedBox(height: 6),
          TextField(
            controller: _amountController,
            keyboardType: TextInputType.number,
            decoration: const InputDecoration(hintText: '0.00'),
          ),
          const SizedBox(height: 14),

          Text(l10n.translate('payment_mode'), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
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

          Text(l10n.translate('upi_ref_optional'), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
          const SizedBox(height: 6),
          TextField(
            controller: _refController,
            decoration: InputDecoration(hintText: AppLocalizations.of(context).translate('utr_hint')),
          ),
          const SizedBox(height: 20),

          ElevatedButton(
            onPressed: _isSubmitting ? null : _submitPayment,
            child: _isSubmitting ? const CircularProgressIndicator() : Text(l10n.translate('record_payment_receipt')),
          ),
        ],
      ),
    );
  }
}
