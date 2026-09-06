import 'package:flutter/material.dart';
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

  static const _reportNames = [
    'Profit & Loss',
    'Sales',
    'Stock',
    'Khata',
    'Expenses',
    'GST',
    'Top Products',
    'Top Customers',
  ];

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: _reportNames.length,
      child: Scaffold(
        appBar: AppBar(
          title: const Text('Business Reports'),
          bottom: TabBar(
            isScrollable: true,
            tabAlignment: TabAlignment.start,
            labelColor: AppColors.primary,
            unselectedLabelColor: AppColors.textSecondary,
            indicatorColor: AppColors.primary,
            tabs: _reportNames.map((n) => Tab(text: n)).toList(),
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

  static const _periods = {
    'today': 'Today',
    'yesterday': 'Yesterday',
    '7d': '7 Days',
    '30d': '30 Days',
    'this_month': 'This Month',
    'last_month': 'Last Month',
  };

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final current = ref.watch(reportPeriodProvider);
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      child: Row(
        children: _periods.entries.map((e) {
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
          'Could not load report: $error',
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
        color: item.color.withOpacity(0.06),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: item.color.withOpacity(0.25)),
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
                    (label: 'Revenue', value: CurrencyFormatter.format(data['total_revenue']), color: AppColors.primary),
                    (label: 'COGS', value: CurrencyFormatter.format(data['total_cogs']), color: AppColors.info),
                    (
                      label: 'Gross Profit',
                      value: CurrencyFormatter.format(data['gross_profit']),
                      color: (data['gross_profit'] as num) >= 0 ? AppColors.success : AppColors.danger
                    ),
                    (label: 'Gross Margin', value: '${data['gross_margin_percent']}%', color: AppColors.accentTeal),
                    (label: 'Expenses', value: CurrencyFormatter.format(data['total_expenses']), color: AppColors.warning),
                    (
                      label: 'Net Profit',
                      value: CurrencyFormatter.format(data['net_profit']),
                      color: (data['net_profit'] as num) >= 0 ? AppColors.success : AppColors.danger
                    ),
                  ]),
                  _SectionTitle('Expense Breakdown'),
                  if (breakdown.isEmpty)
                    const Padding(
                      padding: EdgeInsets.all(16),
                      child: Text('No expenses in this period.', style: TextStyle(color: AppColors.textSecondary)),
                    )
                  else
                    ...breakdown.map(
                      (b) => ListTile(
                        dense: true,
                        title: Text(b['category__name'] ?? 'Uncategorised', style: const TextStyle(fontSize: 14)),
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
                    (label: 'Bills', value: '${data['total_sales_count']}', color: AppColors.primary),
                    (label: 'Revenue', value: CurrencyFormatter.format(data['total_amount']), color: AppColors.primary),
                    (label: 'Collected', value: CurrencyFormatter.format(data['total_collected']), color: AppColors.success),
                    (label: 'Khata Due', value: CurrencyFormatter.format(data['total_due']), color: AppColors.danger),
                  ]),
                  if (trend.length >= 2) ...[
                    _SectionTitle('Daily Trend'),
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
                belowBarData: BarAreaData(show: true, color: AppColors.primary.withOpacity(0.08)),
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
              (label: 'Products', value: '${data['total_products']}', color: AppColors.primary),
              (label: 'Units', value: '${data['total_units']}', color: AppColors.accentTeal),
              (label: 'Stock Cost', value: CurrencyFormatter.format(data['stock_cost_value']), color: AppColors.info),
              (label: 'Potential Sales', value: CurrencyFormatter.format(data['stock_selling_value']), color: AppColors.primary),
              (label: 'Low Stock', value: '${data['low_stock_count']}', color: AppColors.warning),
              (label: 'Out of Stock', value: '${data['out_of_stock_count']}', color: AppColors.danger),
              (
                label: 'Potential Margin',
                value: CurrencyFormatter.format(data['potential_margin']),
                color: AppColors.success
              ),
            ]),
            _SectionTitle('Low Stock — Reorder Soon'),
            if (low.isEmpty)
              const Padding(
                padding: EdgeInsets.all(16),
                child: Text('All products healthy. Nothing low on stock.', style: TextStyle(color: AppColors.textSecondary)),
              )
            else
              ...low.map(
                (p) => ListTile(
                  dense: true,
                  title: Text(p['name'], style: const TextStyle(fontSize: 14)),
                  subtitle: Text('Min required: ${p['min_stock']}', style: const TextStyle(fontSize: 12)),
                  trailing: Text(
                    '${p['stock']} left',
                    style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: AppColors.warning),
                  ),
                ),
              ),
            _SectionTitle('Dead Stock (No sale in 60+ days)'),
            if (dead.isEmpty)
              const Padding(
                padding: EdgeInsets.all(16),
                child: Text('No dead stock identified.', style: TextStyle(color: AppColors.textSecondary)),
              )
            else
              ...dead.map(
                (p) => ListTile(
                  dense: true,
                  title: Text(p['name'], style: const TextStyle(fontSize: 14)),
                  subtitle: Text('${p['quantity']} units • last sale: ${p['last_sale']}', style: const TextStyle(fontSize: 12)),
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
              (label: 'Customer Udhar', value: CurrencyFormatter.format(data['total_customer_due']), color: AppColors.danger),
              (label: 'Supplier Payable', value: CurrencyFormatter.format(data['total_supplier_due']), color: AppColors.warning),
            ]),
            _SectionTitle('Pending Customer Khata (${khata.length})'),
            if (khata.isEmpty)
              const Padding(
                padding: EdgeInsets.all(16),
                child: Text('No pending udhar. All customers settled.', style: TextStyle(color: AppColors.textSecondary)),
              )
            else
              ...khata.map(
                (k) => ListTile(
                  dense: true,
                  leading: CircleAvatar(
                    backgroundColor: AppColors.danger.withOpacity(0.1),
                    child: Text(
                      (k['name'] as String)[0].toUpperCase(),
                      style: const TextStyle(color: AppColors.danger, fontWeight: FontWeight.bold, fontSize: 13),
                    ),
                  ),
                  title: Text(k['name'], style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold)),
                  subtitle: Text('Paid: ${CurrencyFormatter.format(k['total_paid'])}', style: const TextStyle(fontSize: 12)),
                  trailing: Text(
                    CurrencyFormatter.format(k['due']),
                    style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: AppColors.danger),
                  ),
                ),
              ),
            _SectionTitle('Supplier Payables (${payables.length})'),
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
                    (label: 'Total Expenses', value: CurrencyFormatter.format(data['total_expenses']), color: AppColors.warning),
                    (label: 'Entries', value: '${data['expense_count']}', color: AppColors.info),
                  ]),
                  _SectionTitle('Category Breakdown'),
                  if (breakdown.isEmpty)
                    const Padding(
                      padding: EdgeInsets.all(16),
                      child: Text('No expenses in this period.', style: TextStyle(color: AppColors.textSecondary)),
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
                    (label: 'Taxable Value', value: CurrencyFormatter.format(data['total_taxable_value']), color: AppColors.primary),
                    (label: 'GST Collected', value: CurrencyFormatter.format(data['total_gst_collected']), color: AppColors.accentTeal),
                    (label: 'Invoices', value: '${data['total_invoices']}', color: AppColors.info),
                    (label: 'Purchases Value', value: CurrencyFormatter.format(data['total_purchases_value']), color: AppColors.warning),
                  ]),
                  _SectionTitle('GST Sales Register'),
                  if (sales.isEmpty)
                    const Padding(
                      padding: EdgeInsets.all(16),
                      child: Text('No taxable invoices in this period.', style: TextStyle(color: AppColors.textSecondary)),
                    )
                  else
                    ...sales.map(
                      (s) => ListTile(
                        dense: true,
                        title: Text('${s['invoice_number']} • ${s['customer']}', style: const TextStyle(fontSize: 13.5, fontWeight: FontWeight.bold)),
                        subtitle: Text('${s['date']} • Taxable: ${CurrencyFormatter.format(s['taxable_value'])}', style: const TextStyle(fontSize: 12)),
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
                  _SectionTitle('Best Selling Products'),
                  if (products.isEmpty)
                    const Padding(
                      padding: EdgeInsets.all(16),
                      child: Text('No sales in this period yet.', style: TextStyle(color: AppColors.textSecondary)),
                    )
                  else
                    ...products.asMap().entries.map(
                          (e) => ListTile(
                            dense: true,
                            leading: CircleAvatar(
                              radius: 14,
                              backgroundColor: AppColors.primary.withOpacity(0.1),
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
                  _SectionTitle('Top Brands'),
                  ...brands.map(
                    (b) => ListTile(
                      dense: true,
                      leading: const Icon(Icons.branding_watermark, size: 20, color: AppColors.accentTeal),
                      title: Text(b['brand'], style: const TextStyle(fontSize: 14)),
                      subtitle: Text('${b['units_sold']} units', style: const TextStyle(fontSize: 12)),
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
                  _SectionTitle('Most Valuable Customers'),
                  if (customers.isEmpty)
                    const Padding(
                      padding: EdgeInsets.all(16),
                      child: Text('No customer sales in this period yet.', style: TextStyle(color: AppColors.textSecondary)),
                    )
                  else
                    ...customers.asMap().entries.map(
                          (e) => ListTile(
                            dense: true,
                            leading: CircleAvatar(
                              radius: 14,
                              backgroundColor: AppColors.success.withOpacity(0.1),
                              child: Text(
                                '${e.key + 1}',
                                style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppColors.success),
                              ),
                            ),
                            title: Text(e.value['name'], style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold)),
                            subtitle: Text('${e.value['visits']} visits • ${e.value['phone']}', style: const TextStyle(fontSize: 12)),
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
