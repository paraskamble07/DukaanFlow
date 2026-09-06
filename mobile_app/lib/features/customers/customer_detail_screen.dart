import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/constants/app_colors.dart';
import '../../core/utils/currency_formatter.dart';
import '../../core/utils/date_formatter.dart';
import '../../models/customer_model.dart';
import '../../providers/customer_provider.dart';
import '../../shared_widgets/whatsapp_button.dart';
import 'widgets/receive_payment_modal.dart';

class CustomerDetailScreen extends ConsumerWidget {
  final CustomerModel customer;

  const CustomerDetailScreen({super.key, required this.customer});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
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
              Center(child: Text('Error: $err', textAlign: TextAlign.center)),
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
                          Text('Mobile: ${customer.phone}', style: const TextStyle(color: Colors.white70)),
                          const Divider(color: Colors.white24, height: 24),
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  const Text('OUTSTANDING BALANCE', style: TextStyle(color: Colors.white70, fontSize: 11, fontWeight: FontWeight.bold)),
                                  Text(
                                    CurrencyFormatter.format(due),
                                    style: const TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.bold),
                                  ),
                                ],
                              ),
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
                                label: const Text('Add Payment'),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),

                  if (due > 0) ...[
                    WhatsAppButton(
                      url: summary['whatsapp_reminder_url'],
                      label: 'Send WhatsApp Payment Reminder',
                    ),
                    const SizedBox(height: 20),
                  ],

                  // Transaction History Tabs / Section
                  const Text('Sales Orders', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 8),
                  if (sales.isEmpty)
                    const Text('No sales records found.', style: TextStyle(color: AppColors.textSecondary))
                  else
                    ...sales.map((s) => Card(
                      child: ListTile(
                        title: Text('Invoice #${s['invoice_number']}', style: const TextStyle(fontWeight: FontWeight.bold)),
                        subtitle: Text(AppDateFormatter.formatDateTime(s['sale_date'])),
                        trailing: Text(CurrencyFormatter.format(s['total_amount']), style: const TextStyle(fontWeight: FontWeight.bold, color: AppColors.primary)),
                      ),
                    )),

                  const SizedBox(height: 20),
                  const Text('Payment Receipts Received', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 8),
                  if (payments.isEmpty)
                    const Text('No payments recorded.', style: TextStyle(color: AppColors.textSecondary))
                  else
                    ...payments.map((p) => Card(
                      child: ListTile(
                        leading: const Icon(Icons.check_circle_outline, color: AppColors.success),
                        title: Text('Payment via ${p['payment_method_display']}', style: const TextStyle(fontWeight: FontWeight.bold)),
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
