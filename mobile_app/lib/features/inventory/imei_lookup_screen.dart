import 'package:flutter/material.dart';
import '../../core/localization/app_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/constants/app_colors.dart';
import '../../core/utils/currency_formatter.dart';
import '../../core/utils/date_formatter.dart';
import '../../providers/inventory_provider.dart';

class ImeiLookupScreen extends ConsumerStatefulWidget {
  final String? initialImei;

  const ImeiLookupScreen({super.key, this.initialImei});

  @override
  ConsumerState<ImeiLookupScreen> createState() => _ImeiLookupScreenState();
}

class _ImeiLookupScreenState extends ConsumerState<ImeiLookupScreen> {
  late final TextEditingController _imeiController;
  String _searchQuery = '';

  @override
  void initState() {
    super.initState();
    _searchQuery = widget.initialImei ?? '';
    _imeiController = TextEditingController(text: _searchQuery);
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final lookupAsync = ref.watch(imeiLookupProvider(_searchQuery));

    return Scaffold(
      appBar: AppBar(title: Text(l10n.translate('imei_lookup'))),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _imeiController,
                    keyboardType: TextInputType.number,
                    decoration: InputDecoration(
                      hintText: l10n.translate('imei_search_hint'),
                      prefixIcon: Icon(Icons.search),
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                ElevatedButton(
                  style: ElevatedButton.styleFrom(minimumSize: const Size(80, 48)),
                  onPressed: () => setState(() => _searchQuery = _imeiController.text.trim()),
                  child: Text(l10n.translate('search')),
                ),
              ],
            ),
            const SizedBox(height: 20),

            if (_searchQuery.isNotEmpty)
              lookupAsync.when(
                loading: () => const Center(child: CircularProgressIndicator()),
                error: (err, _) => Center(child: Text(l10n.translate('device_not_found'))),
                data: (device) {
                  if (device == null) {
                    return Card(
                      color: AppColors.danger.withValues(alpha: 0.06),
                      child: Padding(
                        padding: const EdgeInsets.all(20.0),
                        child: Center(
                          child: Column(
                            children: [
                              const Icon(Icons.search_off, size: 48, color: AppColors.danger),
                              const SizedBox(height: 8),
                              Text('${l10n.translate('no_record_for_imei')}$_searchQuery', style: const TextStyle(fontWeight: FontWeight.bold)),
                            ],
                          ),
                        ),
                      ),
                    );
                  }

                  return Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16.0),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                decoration: BoxDecoration(
                                  color: device.status == 'SOLD' ? AppColors.textSecondary : AppColors.success,
                                  borderRadius: BorderRadius.circular(6),
                                ),
                                child: Text(device.statusDisplay, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 11)),
                              ),
                              Text(CurrencyFormatter.format(device.sellingPrice), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: AppColors.primary)),
                            ],
                          ),
                          const SizedBox(height: 12),
                          Text(device.productName, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                          if (device.modelName != null) Text(device.modelName!, style: const TextStyle(color: AppColors.textSecondary)),
                          const Divider(height: 24),

                          Text("${l10n.translate('imei_1')}${device.imei1}", style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                          if (device.imei2 != null) Text("${l10n.translate('imei_2')}${device.imei2}", style: const TextStyle(fontSize: 13, color: AppColors.textSecondary)),
                          const SizedBox(height: 12),

                          if (device.customerName != null) ...[
                            Container(
                              padding: const EdgeInsets.all(12),
                              decoration: BoxDecoration(color: AppColors.backgroundLight, borderRadius: BorderRadius.circular(8)),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(l10n.translate('purchased_by_customer'), style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppColors.textSecondary)),
                                  const SizedBox(height: 4),
                                  Text(device.customerName!, style: const TextStyle(fontWeight: FontWeight.bold)),
                                  Text('${l10n.translate('mobile_label')}${device.customerPhone ?? "-"}'),
                                  Text('${l10n.translate('sale_date_label')}${AppDateFormatter.formatDate(device.saleDate)}'),
                                  if (device.invoiceNumber != null) Text('${l10n.translate('invoice_bill')}${device.invoiceNumber}'),
                                ],
                              ),
                            ),
                          ],
                        ],
                      ),
                    ),
                  );
                },
              ),
          ],
        ),
      ),
    );
  }
}
