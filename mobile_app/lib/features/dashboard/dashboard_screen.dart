import 'package:flutter/material.dart';
import '../../core/localization/app_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/constants/app_colors.dart';
import '../../core/utils/currency_formatter.dart';
import '../../providers/auth_provider.dart';
import '../../providers/dashboard_provider.dart';
import '../../shared_widgets/whatsapp_button.dart';
import '../inventory/imei_scanner_screen.dart';
import '../inventory/imei_lookup_screen.dart';
import '../admin/admin_dashboard_screen.dart';
import 'widgets/kpi_card.dart';
import 'widgets/sales_chart_card.dart';
import 'widgets/quick_actions_bar.dart';

class DashboardScreen extends ConsumerWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final authState = ref.watch(authProvider);
    final dashboardAsync = ref.watch(dashboardProvider);
    final business = authState.business;

    // ShopZen Admin accounts have no shop of their own — every /api/dashboard/
    // call would 403. Give them a clean landing instead of an error screen.
    if (business == null && authState.user?.isShopZenAdmin == true) {
      return Scaffold(
        appBar: AppBar(title: Text(l10n.translate('app_name'))),
        // (brand name stays Latin across locales)
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(32),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.admin_panel_settings_rounded,
                    size: 64, color: AppColors.primary),
                const SizedBox(height: 16),
                Text(
                  l10n.translate('signed_in_as_admin'),
                  style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 8),
                Text(
                  l10n.translate('admin_landing_desc'),
                  textAlign: TextAlign.center,
                  style: const TextStyle(fontSize: 13, color: AppColors.textSecondary),
                ),
                const SizedBox(height: 24),
                FilledButton.icon(
                  onPressed: () => Navigator.of(context).push(
                    MaterialPageRoute(builder: (_) => const AdminDashboardScreen()),
                  ),
                  icon: const Icon(Icons.dashboard_outlined),
                  label: Text(AppLocalizations.of(context).translate('open_admin_dashboard')),
                ),
              ],
            ),
          ),
        ),
      );
    }

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
              "${l10n.translate('good_morning')}${authState.user?.firstName ?? l10n.translate('owner_label')} 👋",
              style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.qr_code_scanner_rounded),
            tooltip: l10n.translate('scan_imei'),
            onPressed: () => Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => const ImeiScannerScreen()),
            ),
          ),
          IconButton(
            icon: const Icon(Icons.search),
            tooltip: l10n.translate('search_device'),
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
                Text('${l10n.translate('could_not_load_dashboard')}$err', textAlign: TextAlign.center),
                const SizedBox(height: 16),
                ElevatedButton(
                  onPressed: () => ref.refresh(dashboardProvider),
                  child: Text(AppLocalizations.of(context).translate('retry')),
                ),
              ],
            ),
          ),
          data: (data) {
            final l10n = AppLocalizations.of(context);
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
                        title: l10n.translate('today_sales'),
                        amount: data.today.sales,
                        subtitle: '${data.today.salesCount} ${l10n.translate('bills_generated')}',
                        icon: Icons.receipt_long_rounded,
                        iconColor: AppColors.primary,
                        amountColor: AppColors.primary,
                      ),
                      KpiCard(
                        title: l10n.translate('net_profit'),
                        amount: data.today.netProfit,
                        subtitle: "${l10n.translate('gross_colon')}${CurrencyFormatter.format(data.today.grossProfit)}",
                        icon: Icons.trending_up_rounded,
                        iconColor: AppColors.success,
                        amountColor: AppColors.success,
                      ),
                      KpiCard(
                        title: l10n.translate('outstanding_khata'),
                        amount: data.totalReceivable,
                        subtitle: l10n.translate('market_udhar'),
                        icon: Icons.people_alt_rounded,
                        iconColor: AppColors.danger,
                        amountColor: AppColors.danger,
                      ),
                      KpiCard(
                        title: l10n.translate('supplier_payable'),
                        amount: data.totalPayable,
                        subtitle: l10n.translate('vendor_outstanding'),
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
                      color: AppColors.danger.withValues(alpha: 0.06),
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
                                    "${data.lowStockCount}${l10n.translate('low_stock_products')}",
                                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: AppColors.danger),
                                  ),
                                  Text(
                                    l10n.translate('reorder_inventory'),
                                    style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
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
                      children: [
                        Text(
                          l10n.translate('pending_khata_reminders'),
                          style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold),
                        ),
                        Text(l10n.translate('one_tap_whatsapp'), style: const TextStyle(fontSize: 11, color: AppColors.whatsapp, fontWeight: FontWeight.bold)),
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
                              backgroundColor: AppColors.primary.withValues(alpha: 0.1),
                              child: Text(
                                (item['name'] as String? ?? 'C')[0].toUpperCase(),
                                style: const TextStyle(fontWeight: FontWeight.bold, color: AppColors.primary),
                              ),
                            ),
                            title: Text(item['name'] ?? '', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                            subtitle: Text("${l10n.translate('due_label')}${CurrencyFormatter.format(dueAmt)}", style: const TextStyle(color: AppColors.danger, fontWeight: FontWeight.bold)),
                            trailing: WhatsAppButton(
                              url: item['whatsapp_reminder_url'],
                              label: AppLocalizations.of(context).translate('remind'),
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
