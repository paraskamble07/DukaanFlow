import 'package:flutter/material.dart';
import '../../core/localization/app_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fl_chart/fl_chart.dart';
import '../../core/constants/app_colors.dart';
import '../../core/utils/currency_formatter.dart';
import '../../providers/business_provider.dart';

class ReportsScreen extends ConsumerStatefulWidget {
  const ReportsScreen({super.key});

  @override
  ConsumerState<ReportsScreen> createState() => _ReportsScreenState();
}

class _ReportsScreenState extends ConsumerState<ReportsScreen> {
  int _selectedReport = 0;

  static List<String> _reportNames(AppLocalizations l10n) => [
    l10n.translate('profit_loss'),
    l10n.translate('sales_tab'),
    l10n.translate('stock'),
    l10n.translate('khata'),
    l10n.translate('expenses'),
    'GST',
    l10n.translate('top_products'),
    l10n.translate('top_customers'),
  ];

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final reportNames = _reportNames(l10n);
    return DefaultTabController(
      length: reportNames.length,
      child: Scaffold(
        appBar: AppBar(
          title: Text(l10n.translate('business_reports')),
          bottom: TabBar(
            isScrollable: true,
            tabAlignment: TabAlignment.start,
            labelColor: AppColors.primary,
            unselectedLabelColor: AppColors.textSecondary,
            indicatorColor: AppColors.primary,
            tabs: reportNames.map((n) => Tab(text: n)).toList(),
            onTap: (i) => setState(() => _selectedReport = i),
          ),
        ),
        body: IndexedSwitcher(index: _selectedReport),
      ),
    );
  }
}

class IndexedSwitcher extends ConsumerWidget {
  final int index;
  const IndexedSwitcher({super.key, required this.index});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    switch (index) {
      case 0:
        return const _ProfitLossTab();
      case 1:
        return const _SalesReportTab();
      case 2:
        return const _StockReportTab();
      case 3:
        return const _KhataReportTab();
      case 4:
        return const _ExpenseReportTab();
      case 5:
        return const _GstReportTab();
      case 6:
        return const _TopProductsTab();
      case 7:
        return const _TopCustomersTab();
      default:
        return const _ProfitLossTab();
    }
  }
}

class _PeriodChips extends ConsumerWidget {
  const _PeriodChips();

  static List<MapEntry<String, String>> _periods(AppLocalizations l10n) => [
    MapEntry('today', l10n.translate('today')),
    MapEntry('yesterday', l10n.translate('yesterday')),
    MapEntry('7d', l10n.translate('days_7')),
    MapEntry('30d', l10n.translate('days_30')),
    MapEntry('this_month', l10n.translate('this_month')),
    MapEntry('last_month', l10n.translate('last_month')),
  ];

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final current = ref.watch(reportPeriodProvider);
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      child: Row(
        children: _periods(l10n).map((e) {
          return Padding(
            padding: const EdgeInsets.only(right: 8),
            child: ChoiceChip(
              label: Text(e.value),
              selected: current == e.key,
              onSelected: (_) => ref.read(reportPeriodProvider.notifier).state = e.key,
            ),
          );
        }).toList(),
      ),
    );
  }
}

class _ReportError extends StatelessWidget {
  final Object error;
  const _ReportError(this.error);

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Text(
          "${AppLocalizations.of(context).translate('could_not_load_report')}$error",
          textAlign: TextAlign.center,
          style: const TextStyle(color: AppColors.textSecondary),
        ),
      ),
    );
  }
}

class _KpiGrid extends StatelessWidget {
  final List<({String label, String value, Color color})> items;
  const _KpiGrid(this.items);

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        for (int i = 0; i < items.length; i += 2)
          Padding(
            padding: const EdgeInsets.only(bottom: 10),
            child: Row(
              children: [
                Expanded(child: _kpiCard(items[i])),
                const SizedBox(width: 10),
                Expanded(child: i + 1 < items.length ? _kpiCard(items[i + 1]) : const SizedBox.shrink()),
              ],
            ),
          ),
      ],
    );
  }

  Widget _kpiCard(({String label, String value, Color color}) item) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: item.color.withValues(alpha: 0.06),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: item.color.withValues(alpha: 0.25)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            item.label.toUpperCase(),
            style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: item.color, letterSpacing: 0.5),
          ),
          const SizedBox(height: 6),
          Text(
            item.value,
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: item.color),
          ),
        ],
      ),
    );
  }
}

class _SectionTitle extends StatelessWidget {
  final String text;
  const _SectionTitle(this.text);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 20, 16, 8),
      child: Text(
        text.toUpperCase(),
        style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppColors.textSecondary, letterSpacing: 1),
      ),
    );
  }
}

// ------------------------------------------------------------------
// Profit & Loss
// ------------------------------------------------------------------
class _ProfitLossTab extends ConsumerWidget {
  const _ProfitLossTab();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final report = ref.watch(profitLossReportProvider);
    return Column(
      children: [
        const _PeriodChips(),
        Expanded(
          child: report.when(
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (e, _) => _ReportError(e),
            data: (data) {
              final breakdown = (data['expense_breakdown'] as List<dynamic>? ?? []);
              return ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  _KpiGrid([
                    (label: l10n.translate('revenue'), value: CurrencyFormatter.format(data['total_revenue']), color: AppColors.primary),
                    (label: l10n.translate('cogs'), value: CurrencyFormatter.format(data['total_cogs']), color: AppColors.info),
                    (
                      label: l10n.translate('gross_profit'),
                      value: CurrencyFormatter.format(data['gross_profit']),
                      color: (data['gross_profit'] as num) >= 0 ? AppColors.success : AppColors.danger
                    ),
                    (label: l10n.translate('gross_margin'), value: '${data['gross_margin_percent']}%', color: AppColors.accentTeal),
                    (label: l10n.translate('expenses'), value: CurrencyFormatter.format(data['total_expenses']), color: AppColors.warning),
                    (
                      label: l10n.translate('net_profit'),
                      value: CurrencyFormatter.format(data['net_profit']),
                      color: (data['net_profit'] as num) >= 0 ? AppColors.success : AppColors.danger
                    ),
                  ]),
                  _SectionTitle(l10n.translate('expense_breakdown')),
                  if (breakdown.isEmpty)
                    Padding(
                      padding: const EdgeInsets.all(16),
                      child: Text(l10n.translate('no_expenses_period'), style: const TextStyle(color: AppColors.textSecondary)),
                    )
                  else
                    ...breakdown.map(
                      (b) => ListTile(
                        dense: true,
                        title: Text(b['category__name'] ?? AppLocalizations.of(context).translate('uncategorised'), style: const TextStyle(fontSize: 14)),
                        trailing: Text(
                          CurrencyFormatter.format(b['total']),
                          style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold),
                        ),
                      ),
                    ),
                ],
              );
            },
          ),
        ),
      ],
    );
  }
}

// ------------------------------------------------------------------
// Sales
// ------------------------------------------------------------------
class _SalesReportTab extends ConsumerWidget {
  const _SalesReportTab();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final report = ref.watch(salesReportProvider);
    return Column(
      children: [
        const _PeriodChips(),
        Expanded(
          child: report.when(
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (e, _) => _ReportError(e),
            data: (data) {
              final trend = (data['trend'] as List<dynamic>? ?? [])
                  .map((t) => t as Map<String, dynamic>)
                  .where((t) => (t['amount'] as num) > 0)
                  .toList();
              return ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  _KpiGrid([
                    (label: l10n.translate('bills_count'), value: '${data['total_sales_count']}', color: AppColors.primary),
                    (label: l10n.translate('revenue'), value: CurrencyFormatter.format(data['total_amount']), color: AppColors.primary),
                    (label: l10n.translate('collected'), value: CurrencyFormatter.format(data['total_collected']), color: AppColors.success),
                    (label: l10n.translate('khata_due'), value: CurrencyFormatter.format(data['total_due']), color: AppColors.danger),
                  ]),
                  if (trend.length >= 2) ...[
                    _SectionTitle(l10n.translate('daily_trend')),
                    SizedBox(
                      height: 180,
                      child: _TrendChart(trend),
                    ),
                  ],
                ],
              );
            },
          ),
        ),
      ],
    );
  }
}

class _TrendChart extends StatelessWidget {
  final List<Map<String, dynamic>> points;
  const _TrendChart(this.points);

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(12, 16, 16, 8),
        child: LineChart(
          LineChartData(
            gridData: const FlGridData(show: false),
            titlesData: FlTitlesData(
              leftTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
              topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
              rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
              bottomTitles: AxisTitles(
                sideTitles: SideTitles(
                  showTitles: true,
                  reservedSize: 28,
                  getTitlesWidget: (value, meta) {
                    final idx = value.toInt();
                    if (idx < 0 || idx >= points.length) return const SizedBox.shrink();
                    return Padding(
                      padding: const EdgeInsets.only(top: 6),
                      child: Text(
                        points[idx]['date'].toString(),
                        style: const TextStyle(fontSize: 9, color: AppColors.textSecondary),
                      ),
                    );
                  },
                ),
              ),
            ),
            lineBarsData: [
              LineChartBarData(
                spots: [
                  for (int i = 0; i < points.length; i++)
                    FlSpot(i.toDouble(), (points[i]['amount'] as num).toDouble()),
                ],
                isCurved: true,
                color: AppColors.primary,
                barWidth: 2.5,
                dotData: const FlDotData(show: false),
                belowBarData: BarAreaData(show: true, color: AppColors.primary.withValues(alpha: 0.08)),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// ------------------------------------------------------------------
// Stock
// ------------------------------------------------------------------
class _StockReportTab extends ConsumerWidget {
  const _StockReportTab();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final report = ref.watch(stockReportProvider);
    return report.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, _) => _ReportError(e),
      data: (data) {
        final low = (data['low_stock_items'] as List<dynamic>? ?? []);
        final dead = (data['dead_stock'] as List<dynamic>? ?? []);
        return ListView(
          padding: const EdgeInsets.all(16),
          children: [
            _KpiGrid([
              (label: l10n.translate('products_section'), value: '${data['total_products']}', color: AppColors.primary),
              (label: l10n.translate('units'), value: '${data['total_units']}', color: AppColors.accentTeal),
              (label: l10n.translate('stock_cost'), value: CurrencyFormatter.format(data['stock_cost_value']), color: AppColors.info),
              (label: l10n.translate('potential_sales'), value: CurrencyFormatter.format(data['stock_selling_value']), color: AppColors.primary),
              (label: l10n.translate('low_stock'), value: '${data['low_stock_count']}', color: AppColors.warning),
              (label: l10n.translate('out_of_stock'), value: '${data['out_of_stock_count']}', color: AppColors.danger),
              (
                label: l10n.translate('potential_margin'),
                value: CurrencyFormatter.format(data['potential_margin']),
                color: AppColors.success
              ),
            ]),
            _SectionTitle(l10n.translate('low_stock_reorder')),
            if (low.isEmpty)
              Padding(
                padding: const EdgeInsets.all(16),
                child: Text(l10n.translate('all_products_healthy'), style: const TextStyle(color: AppColors.textSecondary)),
              )
            else
              ...low.map(
                (p) => ListTile(
                  dense: true,
                  title: Text(p['name'], style: const TextStyle(fontSize: 14)),
                  subtitle: Text("${l10n.translate('min_required')}${p['min_stock']}", style: const TextStyle(fontSize: 12)),
                  trailing: Text(
                    '${p['stock']} left',
                    style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: AppColors.warning),
                  ),
                ),
              ),
            _SectionTitle(l10n.translate('dead_stock_title')),
            if (dead.isEmpty)
              Padding(
                padding: const EdgeInsets.all(16),
                child: Text(l10n.translate('no_dead_stock'), style: const TextStyle(color: AppColors.textSecondary)),
              )
            else
              ...dead.map(
                (p) => ListTile(
                  dense: true,
                  title: Text(p['name'], style: const TextStyle(fontSize: 14)),
                  subtitle: Text("${p['quantity']}${l10n.translate('units_last_sale')}${p['last_sale']}", style: const TextStyle(fontSize: 12)),
                  trailing: Text(
                    CurrencyFormatter.format(p['investment']),
                    style: const TextStyle(fontSize: 13, color: AppColors.danger, fontWeight: FontWeight.bold),
                  ),
                ),
              ),
          ],
        );
      },
    );
  }
}

// ------------------------------------------------------------------
// Khata
// ------------------------------------------------------------------
class _KhataReportTab extends ConsumerWidget {
  const _KhataReportTab();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final report = ref.watch(khataReportProvider);
    return report.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, _) => _ReportError(e),
      data: (data) {
        final khata = (data['customer_khata'] as List<dynamic>? ?? []);
        final payables = (data['supplier_payables'] as List<dynamic>? ?? []);
        return ListView(
          padding: const EdgeInsets.all(16),
          children: [
            _KpiGrid([
              (label: l10n.translate('customer_udhar'), value: CurrencyFormatter.format(data['total_customer_due']), color: AppColors.danger),
              (label: l10n.translate('supplier_payable'), value: CurrencyFormatter.format(data['total_supplier_due']), color: AppColors.warning),
            ]),
            _SectionTitle("${l10n.translate('pending_customer_khata')}${khata.length})"),
            if (khata.isEmpty)
              Padding(
                padding: const EdgeInsets.all(16),
                child: Text(l10n.translate('no_pending_udhar'), style: const TextStyle(color: AppColors.textSecondary)),
              )
            else
              ...khata.map(
                (k) => ListTile(
                  dense: true,
                  leading: CircleAvatar(
                    backgroundColor: AppColors.danger.withValues(alpha: 0.1),
                    child: Text(
                      (k['name'] as String)[0].toUpperCase(),
                      style: const TextStyle(color: AppColors.danger, fontWeight: FontWeight.bold, fontSize: 13),
                    ),
                  ),
                  title: Text(k['name'], style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold)),
                  subtitle: Text("${l10n.translate('paid_label')}${CurrencyFormatter.format(k['total_paid'])}", style: const TextStyle(fontSize: 12)),
                  trailing: Text(
                    CurrencyFormatter.format(k['due']),
                    style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: AppColors.danger),
                  ),
                ),
              ),
            _SectionTitle("${l10n.translate('supplier_payables')}${payables.length})"),
            ...payables.map(
              (s) => ListTile(
                dense: true,
                title: Text(s['name'], style: const TextStyle(fontSize: 14)),
                trailing: Text(
                  CurrencyFormatter.format(s['due']),
                  style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: AppColors.warning),
                ),
              ),
            ),
          ],
        );
      },
    );
  }
}

// ------------------------------------------------------------------
// Expenses
// ------------------------------------------------------------------
class _ExpenseReportTab extends ConsumerWidget {
  const _ExpenseReportTab();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final report = ref.watch(expenseReportProvider);
    return Column(
      children: [
        const _PeriodChips(),
        Expanded(
          child: report.when(
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (e, _) => _ReportError(e),
            data: (data) {
              final breakdown = (data['category_breakdown'] as List<dynamic>? ?? []);
              return ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  _KpiGrid([
                    (label: l10n.translate('total_expenses'), value: CurrencyFormatter.format(data['total_expenses']), color: AppColors.warning),
                    (label: l10n.translate('entries'), value: '${data['expense_count']}', color: AppColors.info),
                  ]),
                  _SectionTitle(l10n.translate('category_breakdown')),
                  if (breakdown.isEmpty)
                    Padding(
                      padding: const EdgeInsets.all(16),
                      child: Text(l10n.translate('no_expenses_period'), style: const TextStyle(color: AppColors.textSecondary)),
                    )
                  else
                    ...breakdown.map(
                      (b) => ListTile(
                        dense: true,
                        leading: const Icon(Icons.category_outlined, size: 20, color: AppColors.warning),
                        title: Text(b['category'], style: const TextStyle(fontSize: 14)),
                        trailing: Text(
                          CurrencyFormatter.format(b['total']),
                          style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: AppColors.warning),
                        ),
                      ),
                    ),
                ],
              );
            },
          ),
        ),
      ],
    );
  }
}

// ------------------------------------------------------------------
// GST
// ------------------------------------------------------------------
class _GstReportTab extends ConsumerWidget {
  const _GstReportTab();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final report = ref.watch(gstReportProvider);
    return Column(
      children: [
        const _PeriodChips(),
        Expanded(
          child: report.when(
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (e, _) => _ReportError(e),
            data: (data) {
              final sales = (data['sales'] as List<dynamic>? ?? []);
              return ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  _KpiGrid([
                    (label: l10n.translate('taxable_value'), value: CurrencyFormatter.format(data['total_taxable_value']), color: AppColors.primary),
                    (label: l10n.translate('gst_collected'), value: CurrencyFormatter.format(data['total_gst_collected']), color: AppColors.accentTeal),
                    (label: l10n.translate('invoices'), value: '${data['total_invoices']}', color: AppColors.info),
                    (label: l10n.translate('purchases_value'), value: CurrencyFormatter.format(data['total_purchases_value']), color: AppColors.warning),
                  ]),
                  _SectionTitle(l10n.translate('gst_sales_register')),
                  if (sales.isEmpty)
                    Padding(
                      padding: const EdgeInsets.all(16),
                      child: Text(l10n.translate('no_taxable_invoices'), style: const TextStyle(color: AppColors.textSecondary)),
                    )
                  else
                    ...sales.map(
                      (s) => ListTile(
                        dense: true,
                        title: Text('${s['invoice_number']} • ${s['customer']}', style: const TextStyle(fontSize: 13.5, fontWeight: FontWeight.bold)),
                        subtitle: Text("${s['date']}${l10n.translate('taxable_label')}${CurrencyFormatter.format(s['taxable_value'])}", style: const TextStyle(fontSize: 12)),
                        trailing: Text(
                          'GST ${CurrencyFormatter.format(s['gst'])}',
                          style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: AppColors.accentTeal),
                        ),
                      ),
                    ),
                ],
              );
            },
          ),
        ),
      ],
    );
  }
}

// ------------------------------------------------------------------
// Top Products / Customers
// ------------------------------------------------------------------
class _TopProductsTab extends ConsumerWidget {
  const _TopProductsTab();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final report = ref.watch(topProductsReportProvider);
    return Column(
      children: [
        const _PeriodChips(),
        Expanded(
          child: report.when(
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (e, _) => _ReportError(e),
            data: (data) {
              final products = (data['top_products'] as List<dynamic>? ?? []);
              final brands = (data['top_brands'] as List<dynamic>? ?? []);
              return ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  _SectionTitle(l10n.translate('best_selling')),
                  if (products.isEmpty)
                    Padding(
                      padding: const EdgeInsets.all(16),
                      child: Text(l10n.translate('no_sales_period'), style: const TextStyle(color: AppColors.textSecondary)),
                    )
                  else
                    ...products.asMap().entries.map(
                          (e) => ListTile(
                            dense: true,
                            leading: CircleAvatar(
                              radius: 14,
                              backgroundColor: AppColors.primary.withValues(alpha: 0.1),
                              child: Text(
                                '${e.key + 1}',
                                style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppColors.primary),
                              ),
                            ),
                            title: Text(e.value['name'], style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold)),
                            subtitle: Text(
                              '${e.value['units_sold']} units • Profit ${CurrencyFormatter.format(e.value['profit'])}',
                              style: const TextStyle(fontSize: 12),
                            ),
                            trailing: Text(
                              CurrencyFormatter.format(e.value['revenue']),
                              style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: AppColors.primary),
                            ),
                          ),
                        ),
                  _SectionTitle(l10n.translate('top_brands')),
                  ...brands.map(
                    (b) => ListTile(
                      dense: true,
                      leading: const Icon(Icons.branding_watermark, size: 20, color: AppColors.accentTeal),
                      title: Text(b['brand'], style: const TextStyle(fontSize: 14)),
                      subtitle: Text("${b['units_sold']} ${l10n.translate('units')}", style: const TextStyle(fontSize: 12)),
                      trailing: Text(
                        CurrencyFormatter.format(b['revenue']),
                        style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold),
                      ),
                    ),
                  ),
                ],
              );
            },
          ),
        ),
      ],
    );
  }
}

class _TopCustomersTab extends ConsumerWidget {
  const _TopCustomersTab();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final report = ref.watch(topCustomersReportProvider);
    return Column(
      children: [
        const _PeriodChips(),
        Expanded(
          child: report.when(
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (e, _) => _ReportError(e),
            data: (data) {
              final customers = (data['top_customers'] as List<dynamic>? ?? []);
              return ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  _SectionTitle(l10n.translate('most_valuable_customers')),
                  if (customers.isEmpty)
                    Padding(
                      padding: const EdgeInsets.all(16),
                      child: Text(l10n.translate('no_customer_sales_period'), style: const TextStyle(color: AppColors.textSecondary)),
                    )
                  else
                    ...customers.asMap().entries.map(
                          (e) => ListTile(
                            dense: true,
                            leading: CircleAvatar(
                              radius: 14,
                              backgroundColor: AppColors.success.withValues(alpha: 0.1),
                              child: Text(
                                '${e.key + 1}',
                                style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppColors.success),
                              ),
                            ),
                            title: Text(e.value['name'], style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold)),
                            subtitle: Text("${e.value['visits']}${l10n.translate('visits_label')}${e.value['phone']}", style: const TextStyle(fontSize: 12)),
                            trailing: Text(
                              CurrencyFormatter.format(e.value['total_spent']),
                              style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: AppColors.primary),
                            ),
                          ),
                        ),
                ],
              );
            },
          ),
        ),
      ],
    );
  }
}
