import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../core/constants/app_colors.dart';
import '../../core/utils/currency_formatter.dart';
import '../../providers/auth_provider.dart';
import '../../providers/business_provider.dart';
import '../../models/sale_model.dart';

class SaleDetailScreen extends ConsumerWidget {
  final int saleId;
  const SaleDetailScreen({super.key, required this.saleId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final saleAsync = ref.watch(saleDetailProvider(saleId));
    final business = ref.watch(authProvider).business;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Invoice Details'),
        actions: [
          saleAsync.when(
            data: (sale) => IconButton(
              icon: const Icon(Icons.share, color: AppColors.whatsapp),
              tooltip: 'Share Invoice',
              onPressed: () => _shareInvoice(context, sale, business?.name ?? 'our shop'),
            ),
            loading: () => const SizedBox.shrink(),
            error: (_, __) => const SizedBox.shrink(),
          ),
        ],
      ),
      body: saleAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, _) => Center(child: Text('Could not load sale: $err')),
        data: (sale) => Column(
          children: [
            Expanded(
              child: RefreshIndicator(
                onRefresh: () async => ref.refresh(saleDetailProvider(saleId)),
                child: ListView(
                  padding: const EdgeInsets.all(16),
                  children: [
                    // Invoice header card
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      sale.invoiceNumber,
                                      style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: AppColors.primary),
                                    ),
                                    Text(
                                      sale.saleDate.length >= 10 ? sale.saleDate.substring(0, 10) : sale.saleDate,
                                      style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
                                    ),
                                  ],
                                ),
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                                  decoration: BoxDecoration(
                                    color: sale.dueAmount > 0 ? AppColors.warning.withOpacity(0.12) : AppColors.success.withOpacity(0.12),
                                    borderRadius: BorderRadius.circular(20),
                                  ),
                                  child: Text(
                                    sale.dueAmount > 0 ? 'Khata Due' : 'Fully Paid',
                                    style: TextStyle(
                                      fontSize: 12,
                                      fontWeight: FontWeight.bold,
                                      color: sale.dueAmount > 0 ? AppColors.warning : AppColors.success,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                            const Divider(height: 24),
                            _row('Customer', sale.customerName),
                            if (sale.customerPhone.isNotEmpty) _row('Phone', sale.customerPhone),
                            _row('Payment Mode', sale.paymentMethodDisplay),
                            if (sale.notes != null && sale.notes!.isNotEmpty) _row('Notes', sale.notes!),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),

                    // Line items
                    const Text('ITEMS', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppColors.textSecondary, letterSpacing: 1)),
                    const SizedBox(height: 8),
                    ...sale.items.map((item) => Card(
                          child: Padding(
                            padding: const EdgeInsets.all(14),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                  children: [
                                    Expanded(
                                      child: Text(
                                        '${item.productName}${item.productBrand != null && item.productBrand!.isNotEmpty ? ' (${item.productBrand})' : ''}',
                                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                                      ),
                                    ),
                                    Text(
                                      CurrencyFormatter.format(item.totalPrice),
                                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 4),
                                Text(
                                  'Qty: ${item.quantity} × ${CurrencyFormatter.format(item.unitPrice)}'
                                  '${item.discount > 0 ? ' − Discount ${CurrencyFormatter.format(item.discount)}' : ''}',
                                  style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
                                ),
                                if (item.imeiNumbers != null && item.imeiNumbers!.isNotEmpty)
                                  Text(
                                    item.imeiNumbers!,
                                    style: const TextStyle(fontSize: 11, color: AppColors.info),
                                  ),
                                if (item.warrantyMonths > 0)
                                  Text(
                                    'Warranty: ${item.warrantyMonths} months',
                                    style: const TextStyle(fontSize: 11, color: AppColors.success),
                                  ),
                              ],
                            ),
                          ),
                        )),

                    const SizedBox(height: 16),
                    // Totals
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          children: [
                            _amountRow('Subtotal', sale.subtotal),
                            if (sale.discount > 0) _amountRow('Discount', -sale.discount),
                            if (sale.taxAmount > 0) _amountRow('GST', sale.taxAmount),
                            const Divider(),
                            _amountRow('Grand Total', sale.totalAmount, isBold: true),
                            _amountRow('Paid', sale.paidAmount, color: AppColors.success),
                            if (sale.dueAmount > 0)
                              _amountRow('Balance Due (Khata)', sale.dueAmount, color: AppColors.danger, isBold: true),
                            const Divider(),
                            _amountRow('Gross Profit', sale.grossProfit, color: AppColors.primary),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _row(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 3),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 110,
            child: Text(label, style: const TextStyle(fontSize: 13, color: AppColors.textSecondary)),
          ),
          Expanded(
            child: Text(value, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
          ),
        ],
      ),
    );
  }

  Widget _amountRow(String label, double value, {bool isBold = false, Color? color}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: TextStyle(fontSize: isBold ? 15 : 13, fontWeight: isBold ? FontWeight.bold : FontWeight.normal)),
          Text(
            CurrencyFormatter.format(value),
            style: TextStyle(
              fontSize: isBold ? 16 : 13,
              fontWeight: isBold ? FontWeight.bold : FontWeight.normal,
              color: color,
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _shareInvoice(BuildContext context, SaleModel sale, String shopName) async {
    final cleanPhone = sale.customerPhone.replaceAll(RegExp(r'[^0-9]'), '');
    // Walk-in placeholder / invalid numbers cannot receive WhatsApp messages.
    if (cleanPhone.isEmpty || cleanPhone == '0000000000') {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('No real customer phone number on this bill.')),
      );
      return;
    }
    final phone10 = cleanPhone.length == 10 ? '91$cleanPhone' : cleanPhone;

    final msg = StringBuffer()
      ..writeln('Namaste ${sale.customerName},')
      ..writeln()
      ..writeln('Invoice #${sale.invoiceNumber} from *$shopName*:')
      ..writeln('Total: ₹${sale.totalAmount.toStringAsFixed(2)}')
      ..writeln('Paid: ₹${sale.paidAmount.toStringAsFixed(2)}');
    if (sale.dueAmount > 0) {
      msg.writeln('Due: ₹${sale.dueAmount.toStringAsFixed(2)}');
    }
    msg
      ..writeln('Date: ${sale.saleDate.length >= 10 ? sale.saleDate.substring(0, 10) : sale.saleDate}')
      ..writeln()
      ..writeln('Thank you for shopping with us!');

    final waUrl = 'https://wa.me/$phone10?text=${Uri.encodeComponent(msg.toString())}';
    final uri = Uri.parse(waUrl);
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    } else if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Could not launch WhatsApp.')),
      );
    }
  }
}
