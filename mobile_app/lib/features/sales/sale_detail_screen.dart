import 'package:flutter/material.dart';
import '../../core/localization/app_localizations.dart';
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
    final l10n = AppLocalizations.of(context);
    final saleAsync = ref.watch(saleDetailProvider(saleId));
    final business = ref.watch(authProvider).business;

    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.translate('invoice_details')),
        actions: [
          saleAsync.when(
            data: (sale) => IconButton(
              icon: const Icon(Icons.share, color: AppColors.whatsapp),
              tooltip: l10n.translate('share_invoice'),
              onPressed: () => _shareInvoice(context, sale, business?.name ?? 'our shop'),
            ),
            loading: () => const SizedBox.shrink(),
            error: (_, __) => const SizedBox.shrink(),
          ),
        ],
      ),
      body: saleAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, _) => Center(child: Text('${l10n.translate('could_not_load_sale')}$err')),
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
                                    color: sale.dueAmount > 0 ? AppColors.warning.withValues(alpha: 0.12) : AppColors.success.withValues(alpha: 0.12),
                                    borderRadius: BorderRadius.circular(20),
                                  ),
                                  child: Text(
                                    sale.dueAmount > 0 ? l10n.translate('khata_due') : l10n.translate('fully_paid'),
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
                            _row(l10n.translate('customer_label'), sale.customerName),
                            if (sale.customerPhone.isNotEmpty) _row(l10n.translate('phone'), sale.customerPhone),
                            _row(l10n.translate('payment_mode'), sale.paymentMethodDisplay),
                            if (sale.notes != null && sale.notes!.isNotEmpty) _row(l10n.translate('notes_label'), sale.notes!),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),

                    // Line items
                    Text(l10n.translate('items_section'), style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppColors.textSecondary, letterSpacing: 1)),
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
                                  "${l10n.translate('qty_colon')}${item.quantity} × ${CurrencyFormatter.format(item.unitPrice)}"
                                  "${item.discount > 0 ? ' − ${l10n.translate('discount_label')} ${CurrencyFormatter.format(item.discount)}' : ''}",
                                  style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
                                ),
                                if (item.imeiNumbers != null && item.imeiNumbers!.isNotEmpty)
                                  Text(
                                    item.imeiNumbers!,
                                    style: const TextStyle(fontSize: 11, color: AppColors.info),
                                  ),
                                if (item.warrantyMonths > 0)
                                  Text(
                                    "${l10n.translate('warranty_label')}${item.warrantyMonths}${l10n.translate('warranty_months_suffix')}",
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
                            _amountRow(l10n.translate('subtotal_label'), sale.subtotal),
                            if (sale.discount > 0) _amountRow(l10n.translate('discount_label'), -sale.discount),
                            if (sale.taxAmount > 0) _amountRow('GST', sale.taxAmount),
                            const Divider(),
                            _amountRow(l10n.translate('grand_total'), sale.totalAmount, isBold: true),
                            _amountRow(l10n.translate('paid'), sale.paidAmount, color: AppColors.success),
                            if (sale.dueAmount > 0)
                              _amountRow(l10n.translate('balance_due_khata_plain'), sale.dueAmount, color: AppColors.danger, isBold: true),
                            const Divider(),
                            _amountRow(l10n.translate('gross_profit'), sale.grossProfit, color: AppColors.primary),
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
    final l10n = AppLocalizations.of(context);
    final cleanPhone = sale.customerPhone.replaceAll(RegExp(r'[^0-9]'), '');
    // Walk-in placeholder / invalid numbers cannot receive WhatsApp messages.
    if (cleanPhone.isEmpty || cleanPhone == '0000000000') {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(l10n.translate('no_customer_phone'))),
      );
      return;
    }
    final phone10 = cleanPhone.length == 10 ? '91$cleanPhone' : cleanPhone;

    final msg = StringBuffer()
      ..writeln("${l10n.translate('msg_namaste')}${sale.customerName},")
      ..writeln()
      ..writeln("${l10n.translate('msg_invoice_p1')}${sale.invoiceNumber}${l10n.translate('msg_invoice_p2')}*$shopName*:")
      ..writeln("${l10n.translate('msg_total_line')}${sale.totalAmount.toStringAsFixed(2)}")
      ..writeln("${l10n.translate('msg_paid_line')}${sale.paidAmount.toStringAsFixed(2)}");
    if (sale.dueAmount > 0) {
      msg.writeln("${l10n.translate('msg_due_line')}${sale.dueAmount.toStringAsFixed(2)}");
    }
    msg
      ..writeln("${l10n.translate('msg_date_line')}${sale.saleDate.length >= 10 ? sale.saleDate.substring(0, 10) : sale.saleDate}")
      ..writeln()
      ..writeln(l10n.translate('msg_thanks'));

    final waUrl = 'https://wa.me/$phone10?text=${Uri.encodeComponent(msg.toString())}';
    final uri = Uri.parse(waUrl);
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    } else if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(l10n.translate('could_not_launch_whatsapp'))),
      );
    }
  }
}
