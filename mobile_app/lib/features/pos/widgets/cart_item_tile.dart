import 'package:flutter/material.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/utils/currency_formatter.dart';
import '../../../providers/pos_provider.dart';

class CartItemTile extends StatelessWidget {
  final CartItem item;
  final int index;
  final ValueChanged<int> onQuantityChanged;
  final VoidCallback onRemove;

  const CartItemTile({
    super.key,
    required this.item,
    required this.index,
    required this.onQuantityChanged,
    required this.onRemove,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      margin: const EdgeInsets.only(bottom: 8),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: AppColors.borderLight),
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  item.product.name,
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                ),
                if (item.imeiString != null)
                  Text(
                    item.imeiString!,
                    style: const TextStyle(fontSize: 11, color: AppColors.primary, fontWeight: FontWeight.bold),
                  ),
                const SizedBox(height: 2),
                Text(
                  '${CurrencyFormatter.format(item.unitPrice)} each',
                  style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
                ),
              ],
            ),
          ),
          if (item.product.isImeiTracked) ...[
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: AppColors.borderLight,
                borderRadius: BorderRadius.circular(6),
              ),
              child: const Text('1 unit', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
            ),
          ] else ...[
            Row(
              children: [
                IconButton(
                  icon: const Icon(Icons.remove_circle_outline, size: 20),
                  onPressed: () => onQuantityChanged(item.quantity - 1),
                ),
                Text(
                  '${item.quantity}',
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                ),
                IconButton(
                  icon: const Icon(Icons.add_circle_outline, size: 20),
                  onPressed: () => onQuantityChanged(item.quantity + 1),
                ),
              ],
            ),
          ],
          const SizedBox(width: 8),
          Text(
            CurrencyFormatter.format(item.total),
            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: AppColors.primary),
          ),
          IconButton(
            icon: const Icon(Icons.delete_outline, color: AppColors.danger, size: 20),
            onPressed: onRemove,
          ),
        ],
      ),
    );
  }
}
