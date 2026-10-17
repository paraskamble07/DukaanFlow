import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/constants/app_colors.dart';
import '../../core/localization/app_localizations.dart';
import '../../core/utils/currency_formatter.dart';
import '../../core/utils/date_formatter.dart';
import '../../core/utils/pdf_share.dart';
import '../../models/customer_model.dart';
import '../../providers/auth_provider.dart';
import '../../providers/customer_provider.dart';
import '../../shared_widgets/whatsapp_button.dart';
import 'widgets/receive_payment_modal.dart';
import 'widgets/upi_qr_dialog.dart';

class CustomerDetailScreen extends ConsumerStatefulWidget {
  final CustomerModel customer;

  const CustomerDetailScreen({super.key, required this.customer});

  @override
  ConsumerState<CustomerDetailScreen> createState() => _CustomerDetailScreenState();
}

class _CustomerDetailScreenState extends ConsumerState<CustomerDetailScreen> {
  bool _statementBusy = false;

  CustomerModel get customer => widget.customer;

  Future<void> _shareStatement() async {
    DateTime? fromDate;
    DateTime? toDate;

    final picked = await showDialog<Map<String, DateTime?>>(
      context: context,
      builder: (ctx) => _StatementPeriodDialog(customerName: customer.name),
    );
    if (picked == null) return;
    fromDate = picked['from'];
    toDate = picked['to'];
    if (!mounted) return;
    if (fromDate != null && toDate != null && fromDate.isAfter(toDate)) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(AppLocalizations.of(context).translate('start_after_end'))),
      );
      return;
    }

    setState(() => _statementBusy = true);
    try {
      final client = ref.read(apiClientProvider);
      final file = await downloadLedgerPdf(
        client, customer.id,
        name: customer.name, fromDate: fromDate, toDate: toDate,
      );
      if (!mounted) return;
      await shareLedgerPdf(file, subject: "${AppLocalizations.of(context).translate('ledger_subject')}${customer.name}");
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("${AppLocalizations.of(context).translate('could_not_generate_statement')}$e")),
      );
    } finally {
      if (mounted) setState(() => _statementBusy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final ledgerAsync = ref.watch(customerLedgerProvider(customer.id));

    return Scaffold(
      appBar: AppBar(title: Text(customer.name)),
      body: RefreshIndicator(
        onRefresh: () async => ref.refresh(customerLedgerProvider(customer.id)),
        child: ledgerAsync.when(
          // RefreshIndicator requires a scrollable child in EVERY state, or
          // the layout throws and the whole screen paints blank.
          loading: () => ListView(
            physics: const AlwaysScrollableScrollPhysics(),
            children: const [
              SizedBox(height: 200),
              Center(child: CircularProgressIndicator()),
            ],
          ),
          error: (err, _) => ListView(
            physics: const AlwaysScrollableScrollPhysics(),
            children: [
              const SizedBox(height: 120),
              Center(child: Text("${AppLocalizations.of(context).translate('error_prefix')}$err", textAlign: TextAlign.center)),
            ],
          ),
          data: (data) {
            final summary = data['summary'] as Map<String, dynamic>? ?? {};
            final due = double.tryParse(summary['outstanding_due']?.toString() ?? '0') ?? 0.0;
            final sales = data['sales'] as List<dynamic>? ?? [];
            final payments = data['payments'] as List<dynamic>? ?? [];

            return SingleChildScrollView(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Customer Header Card
                  Card(
                    color: AppColors.primary,
                    child: Padding(
                      padding: const EdgeInsets.all(20.0),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(customer.name, style: const TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold)),
                          Text("${AppLocalizations.of(context).translate('mobile_label')}${customer.phone}", style: const TextStyle(color: Colors.white70)),
                          const Divider(color: Colors.white24, height: 24),
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              // Flexible keeps a long balance (and the
                              // 24pt amount) from overflow-pushing the
                              // Add Payment button off-screen on narrow
                              // devices.
                              Flexible(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(l10n.translate('outstanding_balance'), style: const TextStyle(color: Colors.white70, fontSize: 11, fontWeight: FontWeight.bold)),
                                    Text(
                                      CurrencyFormatter.format(due),
                                      style: const TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.bold),
                                    ),
                                  ],
                                ),
                              ),
                              const SizedBox(width: 12),
                              ElevatedButton.icon(
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: Colors.white,
                                  foregroundColor: AppColors.primary,
                                ),
                                onPressed: () => showModalBottomSheet(
                                  context: context,
                                  isScrollControlled: true,
                                  builder: (_) => ReceivePaymentModal(
                                    customerId: customer.id,
                                    customerName: customer.name,
                                    outstandingDue: due,
                                  ),
                                ),
                                icon: const Icon(Icons.add, size: 18),
                                label: Text(l10n.translate('add_payment')),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 12),

                  // Ledger statement (PDF) — generated entirely server-side.
                  SizedBox(
                    width: double.infinity,
                    child: OutlinedButton.icon(
                      onPressed: _statementBusy ? null : _shareStatement,
                      icon: _statementBusy
                          ? const SizedBox(
                              width: 16, height: 16,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : const Icon(Icons.picture_as_pdf_outlined, size: 18),
                      label: Text(_statementBusy ? l10n.translate('generating_statement') : l10n.translate('share_ledger_pdf')),
                    ),
                  ),
                  const SizedBox(height: 16),

                  if (due > 0) ...[
                    WhatsAppButton(
                      url: summary['whatsapp_reminder_url'],
                      label: l10n.translate('send_whatsapp_reminder'),
                    ),
                    const SizedBox(height: 20),
                  ],
                  if (due > 0)
                    SizedBox(
                      width: double.infinity,
                      child: FilledButton.tonalIcon(
                        onPressed: _statementBusy ? null : () => showDialog(
                          context: context,
                          builder: (_) => UpiQrDialog(
                            customer: customer,
                            outstandingDue: due,
                          ),
                        ),
                        icon: const Icon(Icons.qr_code_2_rounded, size: 20),
                        label: Text(l10n.translate('collect_upi_qr')),
                      ),
                    ),

                  // Transaction History Tabs / Section
                  Text(l10n.translate('sales_orders'), style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 8),
                  if (sales.isEmpty)
                    Text(l10n.translate('no_sales'), style: const TextStyle(color: AppColors.textSecondary))
                  else
                    ...sales.map((s) => Card(
                      child: ListTile(
                        title: Text("${AppLocalizations.of(context).translate('invoice_hash')}${s['invoice_number']}", style: const TextStyle(fontWeight: FontWeight.bold)),
                        subtitle: Text(AppDateFormatter.formatDateTime(s['sale_date'])),
                        trailing: Text(CurrencyFormatter.format(s['total_amount']), style: const TextStyle(fontWeight: FontWeight.bold, color: AppColors.primary)),
                      ),
                    )),

                  const SizedBox(height: 20),
                  Text(l10n.translate('payment_receipts'), style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 8),
                  if (payments.isEmpty)
                    Text(l10n.translate('no_payments'), style: const TextStyle(color: AppColors.textSecondary))
                  else
                    ...payments.map((p) => Card(
                      child: ListTile(
                        leading: const Icon(Icons.check_circle_outline, color: AppColors.success),
                        title: Text("${AppLocalizations.of(context).translate('payment_via')}${p['payment_method_display']}", style: const TextStyle(fontWeight: FontWeight.bold)),
                        subtitle: Text(AppDateFormatter.formatDate(p['payment_date'])),
                        trailing: Text(CurrencyFormatter.format(p['amount']), style: const TextStyle(fontWeight: FontWeight.bold, color: AppColors.success)),
                      ),
                    )),
                ],
              ),
            );
          },
        ),
      ),
    );
  }
}

/// Picks an optional statement period. "All time" (both null) is the
/// default — the server then reports the full account history with its
/// current outstanding balance.
class _StatementPeriodDialog extends StatefulWidget {
  final String customerName;
  const _StatementPeriodDialog({required this.customerName});

  @override
  State<_StatementPeriodDialog> createState() => _StatementPeriodDialogState();
}

class _StatementPeriodDialogState extends State<_StatementPeriodDialog> {
  DateTime? _from;
  DateTime? _to;

  Future<void> _pick(bool isFrom) async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: now,
      firstDate: DateTime(2020),
      lastDate: now,
      helpText: isFrom ? AppLocalizations.of(context).translate('statement_start_date') : AppLocalizations.of(context).translate('statement_end_date'),
    );
    if (picked != null) {
      setState(() {
        if (isFrom) {
          _from = picked;
        } else {
          _to = picked;
        }
      });
    }
  }

  String? _fmt(DateTime? d) => d == null ? null : AppDateFormatter.formatDate(d.toIso8601String());

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return AlertDialog(
      title: Text('${l10n.translate('statement_period')} — ${widget.customerName}'),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(l10n.translate('full_history'),
              style: const TextStyle(fontSize: 12, color: AppColors.textSecondary)),
          const SizedBox(height: 12),
          ListTile(
            dense: true,
            leading: const Icon(Icons.event_outlined),
            title: Text(l10n.translate('from')),
            subtitle: Text(_fmt(_from) ?? l10n.translate('any_date')),
            onTap: () => _pick(true),
          ),
          ListTile(
            dense: true,
            leading: const Icon(Icons.event_available_outlined),
            title: Text(l10n.translate('to')),
            subtitle: Text(_fmt(_to) ?? l10n.translate('any_date')),
            onTap: () => _pick(false),
          ),
        ],
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: Text(l10n.translate('cancel')),
        ),
        FilledButton(
          onPressed: () => Navigator.pop(context, {'from': _from, 'to': _to}),
          child: Text(l10n.translate('generate_pdf')),
        ),
      ],
    );
  }
}
