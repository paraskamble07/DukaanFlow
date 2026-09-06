import 'package:flutter/material.dart';
import '../../../core/constants/app_colors.dart';
import '../../pos/pos_screen.dart';
import '../../inventory/product_form_screen.dart';
import '../../inventory/imei_scanner_screen.dart';
import '../../customers/customer_form_screen.dart';
import '../../expenses/expense_form_screen.dart';

class QuickActionsBar extends StatelessWidget {
  const QuickActionsBar({super.key});

  @override
  Widget build(BuildContext context) {
    final actions = [
      {
        'label': 'New Sale',
        'icon': Icons.point_of_sale_rounded,
        'color': AppColors.primary,
        'onTap': () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => const PosScreen())),
      },
      {
        'label': 'Scan IMEI',
        'icon': Icons.qr_code_scanner_rounded,
        'color': AppColors.accentTeal,
        'onTap': () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => const ImeiScannerScreen())),
      },
      {
        'label': 'Add Item',
        'icon': Icons.add_box_rounded,
        'color': const Color(0xFF8B5CF6),
        'onTap': () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => const ProductFormScreen())),
      },
      {
        'label': 'Add Customer',
        'icon': Icons.person_add_alt_1_rounded,
        'color': const Color(0xFFEC4899),
        'onTap': () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => const CustomerFormScreen())),
      },
      {
        'label': 'Add Expense',
        'icon': Icons.receipt_long_rounded,
        'color': AppColors.warning,
        'onTap': () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => const ExpenseFormScreen())),
      },
    ];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Quick Actions',
          style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 12),
        SizedBox(
          // 96px keeps icon + single-line label inside the tile even with
          // system font scaling on small (720px) screens.
          height: 96,
          child: ListView.separated(
            scrollDirection: Axis.horizontal,
            itemCount: actions.length,
            separatorBuilder: (_, __) => const SizedBox(width: 12),
            itemBuilder: (context, index) {
              final a = actions[index];
              final color = a['color'] as Color;
              return InkWell(
                borderRadius: BorderRadius.circular(12),
                onTap: a['onTap'] as VoidCallback,
                child: Container(
                  width: 84,
                  padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 4),
                  decoration: BoxDecoration(
                    color: color.withOpacity(0.08),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: color.withOpacity(0.2)),
                  ),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(a['icon'] as IconData, color: color, size: 24),
                      const SizedBox(height: 6),
                      Text(
                        a['label'] as String,
                        style: TextStyle(
                          fontSize: 10.5,
                          fontWeight: FontWeight.w700,
                          color: color,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        textAlign: TextAlign.center,
                      ),
                    ],
                  ),
                ),
              );
            },
          ),
        ),
      ],
    );
  }
}
