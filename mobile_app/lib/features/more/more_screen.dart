import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/constants/app_colors.dart';
import '../../core/localization/app_localizations.dart';
import '../../providers/auth_provider.dart';
import '../../features/customers/customer_list_screen.dart';
import '../../features/expenses/expense_list_screen.dart';
import '../../features/suppliers/supplier_list_screen.dart';
import '../../features/purchases/purchase_form_screen.dart';
import '../../features/reminders/reminders_screen.dart';
import '../../features/inventory/imei_lookup_screen.dart';
import '../../features/inventory/imei_scanner_screen.dart';
import '../../features/inventory/product_list_screen.dart';
import '../../features/reports/reports_screen.dart';
import '../../features/settings/settings_screen.dart';
import '../../features/admin/admin_dashboard_screen.dart';

class MoreScreen extends ConsumerWidget {
  const MoreScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authProvider);
    final business = auth.business;
    final l10n = AppLocalizations.of(context);

    return Scaffold(
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(business?.name ?? 'ShopZen', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 17)),
            Text(
              "${auth.user?.firstName ?? l10n.translate('owner_label')} • ${l10n.translate('free_account')}",
              style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
            ),
          ],
        ),
      ),
      body: ListView(
        padding: const EdgeInsets.all(12),
        children: [
          _SectionHeader(l10n.translate('inventory')),
          _NavTile(
            icon: Icons.inventory_2_rounded,
            color: AppColors.primary,
            title: l10n.translate('inventory'),
            subtitle: l10n.translate('low_stock_alert'),
            onTap: () => _push(context, const ProductListScreen()),
          ),
          _NavTile(
            icon: Icons.qr_code_scanner_rounded,
            color: AppColors.accentTeal,
            title: l10n.translate('scan_imei'),
            subtitle: l10n.translate('imei_register'),
            onTap: () => _push(context, const ImeiScannerScreen()),
          ),
          _NavTile(
            icon: Icons.search_rounded,
            color: AppColors.info,
            title: l10n.translate('imei_lookup_title'),
            subtitle: l10n.translate('warranty_lifecycle'),
            onTap: () => _push(context, const ImeiLookupScreen()),
          ),
          _NavTile(
            icon: Icons.people_alt_rounded,
            color: const Color(0xFFEC4899),
            title: l10n.translate('customers'),
            subtitle: l10n.translate('khata'),
            onTap: () => _push(context, const CustomerListScreen()),
          ),

          _SectionHeader('${l10n.translate('suppliers')} & ${l10n.translate('purchases')}'),
          _NavTile(
            icon: Icons.local_shipping_rounded,
            color: AppColors.warning,
            title: l10n.translate('suppliers'),
            subtitle: l10n.translate('distributors_payables'),
            onTap: () => _push(context, const SupplierListScreen()),
          ),
          _NavTile(
            icon: Icons.add_shopping_cart_rounded,
            color: AppColors.primary,
            title: l10n.translate('purchases'),
            subtitle: l10n.translate('stock'),
            onTap: () => _push(context, const PurchaseFormScreen()),
          ),

          _SectionHeader('${l10n.translate('reports')} & ${l10n.translate('expenses')}'),
          _NavTile(
            icon: Icons.notifications_active_rounded,
            color: AppColors.danger,
            title: l10n.translate('payment_reminders'),
            subtitle: l10n.translate('payment_reminders_sub'),
            onTap: () => _push(context, const RemindersScreen()),
          ),
          _NavTile(
            icon: Icons.receipt_long_rounded,
            color: AppColors.danger,
            title: l10n.translate('expenses'),
            subtitle: l10n.translate('rent_electricity_salary'),
            onTap: () => _push(context, const ExpenseListScreen()),
          ),
          _NavTile(
            icon: Icons.assessment_rounded,
            color: AppColors.accentTeal,
            title: l10n.translate('reports'),
            subtitle: l10n.translate('profit_loss'),
            onTap: () => _push(context, const ReportsScreen()),
          ),

          _SectionHeader(l10n.translate('account')),
          if (auth.user?.isShopZenAdmin == true)
            _NavTile(
              icon: Icons.admin_panel_settings_rounded,
              color: const Color(0xFF7C3AED),
              title: l10n.translate('admin_dashboard'),
              subtitle: l10n.translate('admin_dashboard_sub'),
              onTap: () => _push(context, const AdminDashboardScreen()),
            ),
          _NavTile(
            icon: Icons.settings_rounded,
            color: AppColors.textSecondary,
            title: l10n.translate('app_settings'),
            subtitle: l10n.translate('app_settings_sub'),
            onTap: () => _push(context, const SettingsScreen()),
          ),
          const SizedBox(height: 24),
          Center(
            child: Text(
              "${l10n.translate('app_version_label')}${l10n.translate('footer_tagline')}",
              textAlign: TextAlign.center,
              style: const TextStyle(fontSize: 11.5, color: AppColors.textSecondary),
            ),
          ),
        ],
      ),
    );
  }

  void _push(BuildContext context, Widget screen) {
    Navigator.of(context).push(MaterialPageRoute(builder: (_) => screen));
  }
}

class _SectionHeader extends StatelessWidget {
  final String text;
  const _SectionHeader(this.text);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(8, 16, 8, 8),
      child: Text(
        text,
        style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppColors.textSecondary, letterSpacing: 1),
      ),
    );
  }
}

class _NavTile extends StatelessWidget {
  final IconData icon;
  final Color color;
  final String title;
  final String subtitle;
  final VoidCallback onTap;

  const _NavTile({
    required this.icon,
    required this.color,
    required this.title,
    required this.subtitle,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 2),
        leading: Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: color.withValues(alpha: 0.12),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Icon(icon, color: color, size: 22),
        ),
        title: Text(title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14.5)),
        subtitle: Text(subtitle, style: const TextStyle(fontSize: 12, color: AppColors.textSecondary)),
        trailing: const Icon(Icons.chevron_right, color: AppColors.textSecondary),
        onTap: onTap,
      ),
    );
  }
}
