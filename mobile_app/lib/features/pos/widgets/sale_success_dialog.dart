import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/utils/currency_formatter.dart';

class SaleSuccessDialog extends StatelessWidget {
  final Map<String, dynamic> saleData;

  const SaleSuccessDialog({super.key, required this.saleData});

  @override
  Widget build(BuildContext context) {
    final sale = saleData['sale'] as Map<String, dynamic>? ?? {};
    final invoiceNo = sale['invoice_number'] ?? '';
    final total = double.tryParse(sale['total_amount']?.toString() ?? '0') ?? 0.0;
    final paid = double.tryParse(sale['paid_amount']?.toString() ?? '0') ?? 0.0;
    final due = double.tryParse(sale['due_amount']?.toString() ?? '0') ?? 0.0;
    final waUrl = saleData['whatsapp_share_url'] as String?;

    return AlertDialog(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      contentPadding: const EdgeInsets.all(24),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            padding: const EdgeInsets.all(16),
            decoration: const BoxDecoration(
              color: AppColors.success,
              shape: BoxShape.circle,
            ),
            child: const Icon(Icons.check, size: 40, color: Colors.white),
          ),
          const SizedBox(height: 16),
          const Text(
            'Bill Generated!',
            style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
          ),
          Text(
            'Invoice #$invoiceNo',
            style: const TextStyle(color: AppColors.primary, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 16),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: AppColors.backgroundLight,
              borderRadius: BorderRadius.circular(10),
            ),
            child: Column(
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text('Total Bill:'),
                    Text(CurrencyFormatter.format(total), style: const TextStyle(fontWeight: FontWeight.bold)),
                  ],
                ),
                const SizedBox(height: 4),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text('Paid Amount:'),
                    Text(CurrencyFormatter.format(paid), style: const TextStyle(color: AppColors.success, fontWeight: FontWeight.bold)),
                  ],
                ),
                if (due > 0) ...[
                  const SizedBox(height: 4),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text('Balance Due (Khata):'),
                      Text(CurrencyFormatter.format(due), style: const TextStyle(color: AppColors.danger, fontWeight: FontWeight.bold)),
                    ],
                  ),
                ],
              ],
            ),
          ),
          const SizedBox(height: 20),
          if (waUrl != null && waUrl.isNotEmpty) ...[
            ElevatedButton.icon(
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.whatsapp,
                foregroundColor: Colors.white,
              ),
              onPressed: () async {
                final uri = Uri.parse(waUrl);
                if (await canLaunchUrl(uri)) {
                  await launchUrl(uri, mode: LaunchMode.externalApplication);
                }
              },
              icon: const Icon(Icons.chat, size: 18),
              label: const Text('Share Invoice on WhatsApp'),
            ),
            const SizedBox(height: 8),
          ],
          OutlinedButton(
            style: OutlinedButton.styleFrom(minimumSize: const Size.fromHeight(44)),
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Start Next Sale'),
          ),
        ],
      ),
    );
  }
}
