import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/constants/app_colors.dart';
import '../../core/utils/currency_formatter.dart';
import '../../providers/auth_provider.dart';
import '../../providers/dashboard_provider.dart';
import '../../shared_widgets/whatsapp_button.dart';
import '../pos/pos_screen.dart';
import '../inventory/imei_scanner_screen.dart';
import '../inventory/imei_lookup_screen.dart';
import 'widgets/kpi_card.dart';
import 'widgets/sales_chart_card.dart';
import 'widgets/quick_actions_bar.dart';

class DashboardScreen extends ConsumerWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authProvider);
    final dashboardAsync = ref.watch(dashboardProvider);
    final business = authState.business;


    return Scaffold(
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              business?.name ?? 'ShopZen',
              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 17),
            ),
            Text(
              'Good Morning, ${authState.user?.firstName ?? "Owner"} 👋',
              style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.qr_code_scanner_rounded),
            tooltip: 'Scan IMEI',
            onPressed: () => Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => const ImeiScannerScreen()),
            ),
          ),
          IconButton(
            icon: const Icon(Icons.search),
            tooltip: 'Search Device',
            onPressed: () => Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => const ImeiLookupScreen()),
            ),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () async => ref.refresh(dashboardProvider),
        child: dashboardAsync.when(
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (err, _) => Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.error_outline, size: 48, color: AppColors.danger),
                const SizedBox(height: 12),
                Text('Could not load dashboard: $err', textAlign: TextAlign.center),
                const SizedBox(height: 16),
                ElevatedButton(
                  onPressed: () => ref.refresh(dashboardProvider),
                  child: const Text('Retry'),
                ),
              ],
            ),
          ),
          data: (data) {
            return SingleChildScrollView(
              physics: const AlwaysScrollableScrollPhysics(),
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // 1. Top 4 KPI Grid
                  GridView.count(
                    crossAxisCount: 2,
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    crossAxisSpacing: 12,
                    mainAxisSpacing: 12,
                    childAspectRatio: 1.35,
                    children: [
                      KpiCard(
                        title: "Today's Sales",
                        amount: data.today.sales,
                        subtitle: '${data.today.salesCount} bills generated',
                        icon: Icons.receipt_long_rounded,
                        iconColor: AppColors.primary,
                        amountColor: AppColors.primary,
                      ),
                      KpiCard(
                        title: "Today's Net Profit",
                        amount: data.today.netProfit,
                        subtitle: 'Gross: ${CurrencyFormatter.format(data.today.grossProfit)}',
                        icon: Icons.trending_up_rounded,
                        iconColor: AppColors.success,
                        amountColor: AppColors.success,
                      ),
                      KpiCard(
                        title: 'Customer Khata Due',
                        amount: data.totalReceivable,
                        subtitle: 'Market Udhar',
                        icon: Icons.people_alt_rounded,
                        iconColor: AppColors.danger,
                        amountColor: AppColors.danger,
                      ),
                      KpiCard(
                        title: 'Supplier Payable',
                        amount: data.totalPayable,
                        subtitle: 'Vendor Outstanding',
                        icon: Icons.local_shipping_rounded,
                        iconColor: AppColors.warning,
                        amountColor: AppColors.warning,
                      ),
                    ],
                  ),
                  const SizedBox(height: 20),

                  // 2. Quick Actions
                  const QuickActionsBar(),
                  const SizedBox(height: 20),

                  // 3. 7-Day Trend Chart
                  SalesChartCard(
                    labels: data.chartLabels,
                    sales: data.chartSales,
                    expenses: data.chartExpenses,
                  ),
                  const SizedBox(height: 20),

                  // 4. Low Stock Alerts Banner (if any)
                  if (data.lowStockCount > 0) ...[
                    Card(
                      color: AppColors.danger.withOpacity(0.06),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                        side: const BorderSide(color: AppColors.danger, width: 1),
                      ),
                      child: Padding(
                        padding: const EdgeInsets.all(16.0),
                        child: Row(
                          children: [
                            Container(
                              padding: const EdgeInsets.all(8),
                              decoration: const BoxDecoration(
                                color: AppColors.danger,
                                shape: BoxShape.circle,
                              ),
                              child: const Icon(Icons.warning_amber_rounded, color: Colors.white, size: 20),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    '${data.lowStockCount} Products Low on Stock',
                                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: AppColors.danger),
                                  ),
                                  const Text(
                                    'Reorder inventory before items run out.',
                                    style: TextStyle(fontSize: 12, color: AppColors.textSecondary),
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 20),
                  ],

                  // 5. Outstanding Khata Reminders List
                  if (data.topPendingKhata.isNotEmpty) ...[
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: const [
                        Text(
                          'Pending Khata Reminders',
                          style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold),
                        ),
                        Text('1-Tap WhatsApp', style: TextStyle(fontSize: 11, color: AppColors.whatsapp, fontWeight: FontWeight.bold)),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Card(
                      child: ListView.separated(
                        shrinkWrap: true,
                        physics: const NeverScrollableScrollPhysics(),
                        itemCount: data.topPendingKhata.length,
                        separatorBuilder: (_, __) => const Divider(height: 1),
                        itemBuilder: (context, index) {
                          final item = data.topPendingKhata[index];
                          final dueAmt = double.tryParse(item['due']?.toString() ?? '0') ?? 0.0;
                          return ListTile(
                            contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                            leading: CircleAvatar(
                              backgroundColor: AppColors.primary.withOpacity(0.1),
                              child: Text(
                                (item['name'] as String? ?? 'C')[0].toUpperCase(),
                                style: const TextStyle(fontWeight: FontWeight.bold, color: AppColors.primary),
                              ),
                            ),
                            title: Text(item['name'] ?? '', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                            subtitle: Text('Due: ${CurrencyFormatter.format(dueAmt)}', style: const TextStyle(color: AppColors.danger, fontWeight: FontWeight.bold)),
                            trailing: WhatsAppButton(
                              url: item['whatsapp_reminder_url'],
                              label: 'Remind',
                              isCompact: true,
                            ),
                          );
                        },
                      ),
                    ),
                  ],
                ],
              ),
            );
          },
        ),
      ),
    );
  }
}
