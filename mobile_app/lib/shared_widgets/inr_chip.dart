import 'package:flutter/material.dart';
import '../core/constants/app_colors.dart';
import '../core/utils/currency_formatter.dart';

class InrChip extends StatelessWidget {
  final double amount;
  final bool isDue;
  final bool isProfit;
  final TextStyle? style;

  const InrChip({
    super.key,
    required this.amount,
    this.isDue = false,
    this.isProfit = false,
    this.style,
  });

  @override
  Widget build(BuildContext context) {
    Color bg = AppColors.primary.withValues(alpha: 0.08);
    Color textColor = AppColors.primary;

    if (isDue) {
      bg = AppColors.danger.withValues(alpha: 0.12);
      textColor = AppColors.danger;
    } else if (isProfit) {
      bg = AppColors.success.withValues(alpha: 0.12);
      textColor = AppColors.success;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(
        CurrencyFormatter.format(amount),
        style: style ?? TextStyle(
          color: textColor,
          fontWeight: FontWeight.w700,
          fontSize: 13,
        ),
      ),
    );
  }
}
