import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/constants/app_colors.dart';
import '../../providers/auth_provider.dart';
import '../../features/customers/customer_list_screen.dart';
import '../../features/expenses/expense_list_screen.dart';
import '../../features/suppliers/supplier_list_screen.dart';
import '../../features/purchases/purchase_form_screen.dart';
import '../../features/inventory/imei_lookup_screen.dart';
import '../../features/inventory/imei_scanner_screen.dart';
import '../../features/inventory/product_list_screen.dart';
import '../../features/reports/reports_screen.dart';
import '../../features/subscription/subscription_screen.dart';
import '../../features/settings/settings_screen.dart';

class MoreScreen extends ConsumerWidget {
  const MoreScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authProvider);
    final business = auth.business;

    return Scaffold(
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(business?.name ?? 'ShopZen', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 17)),
            Text(
              '${auth.user?.firstName ?? 'Owner'} • ${business?.planTier == 'SHOPZEN_PREMIUM' ? 'Premium' : 'Premium'}',
              style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
            ),
          ],
        ),
      ),
      body: ListView(
        padding: const EdgeInsets.all(12),
        children: [
          _SectionHeader('SHOP OPERATIONS'),
          _NavTile(
            icon: Icons.inventory_2_rounded,
            color: AppColors.primary,
            title: 'Stock & Products',
            subtitle: 'Manage inventory, low stock alerts',
            onTap: () => _push(context, const ProductListScreen()),
          ),
          _NavTile(
            icon: Icons.qr_code_scanner_rounded,
            color: AppColors.accentTeal,
            title: 'IMEI Scanner',
            subtitle: 'Scan / register device IMEIs',
            onTap: () => _push(context, const ImeiScannerScreen()),
          ),
          _NavTile(
            icon: Icons.search_rounded,
            color: AppColors.info,
            title: 'IMEI Lookup',
            subtitle: 'Trace device lifecycle & warranty',
            onTap: () => _push(context, const ImeiLookupScreen()),
          ),
          _NavTile(
            icon: Icons.people_alt_rounded,
            color: const Color(0xFFEC4899),
            title: 'Customers & Khata',
            subtitle: 'Udhar ledger, payments, reminders',
            onTap: () => _push(context, const CustomerListScreen()),
          ),

          _SectionHeader('PURCHASES & SUPPLIERS'),
          _NavTile(
            icon: Icons.local_shipping_rounded,
            color: AppColors.warning,
            title: 'Suppliers',
            subtitle: 'Distributors & payables',
            onTap: () => _push(context, const SupplierListScreen()),
          ),
          _NavTile(
            icon: Icons.add_shopping_cart_rounded,
            color: AppColors.primary,
            title: 'New Purchase',
            subtitle: 'Record stock received from supplier',
            onTap: () => _push(context, const PurchaseFormScreen()),
          ),

          _SectionHeader('MONEY & REPORTS'),
          _NavTile(
            icon: Icons.receipt_long_rounded,
            color: AppColors.danger,
            title: 'Expenses',
            subtitle: 'Rent, electricity, salary & more',
            onTap: () => _push(context, const ExpenseListScreen()),
          ),
          _NavTile(
            icon: Icons.assessment_rounded,
            color: AppColors.accentTeal,
            title: 'Reports & Insights',
            subtitle: 'P&L, GST, top products, dead stock',
            onTap: () => _push(context, const ReportsScreen()),
          ),

          _SectionHeader('ACCOUNT'),
          _NavTile(
            icon: Icons.workspace_premium_rounded,
            color: const Color(0xFFF59E0B),
            title: 'ShopZen Premium',
            subtitle: '₹30/month — subscription status',
            onTap: () => _push(context, const SubscriptionScreen()),
          ),
          _NavTile(
            icon: Icons.settings_rounded,
            color: AppColors.textSecondary,
            title: 'Settings',
            subtitle: 'Shop profile, theme, language',
            onTap: () => _push(context, const SettingsScreen()),
          ),
          const SizedBox(height: 24),
          const Center(
            child: Text(
              'ShopZen v1.0.0\nSell. Stock. Khata. Profit. Simplified.',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 11.5, color: AppColors.textSecondary),
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
            color: color.withOpacity(0.12),
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
