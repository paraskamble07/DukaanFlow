import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:dukaanflow/core/localization/app_localizations.dart';

/// Phase 7 guards: Hindi and Marathi must translate every English key, and
/// no locale may ship an empty or untranslated value.
void main() {
  final en = AppLocalizations.translationsFor('en');
  final hi = AppLocalizations.translationsFor('hi');
  final mr = AppLocalizations.translationsFor('mr');

  test('English map has translations', () {
    expect(en.length, greaterThan(50), reason: 'English should carry the full key set');
  });

  test('Hindi map covers every English key', () {
    final missing = en.keys.where((k) => !hi.containsKey(k)).toList();
    expect(missing, [], reason: 'Hindi missing: $missing');
  });

  test('Marathi map covers every English key', () {
    final missing = en.keys.where((k) => !mr.containsKey(k)).toList();
    expect(missing, [], reason: 'Marathi missing: $missing');
  });

  test('no translated value is empty or left in English for hi/mr', () {
    final suspect = <String>[];
    for (final entry in en.entries) {
      final hv = hi[entry.key]!;
      final mv = mr[entry.key]!;
      if (hv.trim().isEmpty || hv == entry.value) {
        suspect.add('hi.${entry.key} = "$hv"');
      }
      if (mv.trim().isEmpty || mv == entry.value) {
        suspect.add('mr.${entry.key} = "$mv"');
      }
    }
    expect(suspect, [], reason: 'Untranslated values: $suspect');
  });

  test('unknown keys fall back to the key itself', () {
    final l = AppLocalizations(const Locale('hi'));
    expect(l.translate('definitely_not_a_real_key'), 'definitely_not_a_real_key');
  });

  test('each screen-visible key is known by the map contract', () {
    const usedKeys = <String>[
      'dashboard', 'pos_billing', 'inventory', 'khata', 'more', 'new_sale',
      'customers', 'suppliers', 'purchases', 'expenses', 'reports',
      'payment_reminders', 'app_settings', 'admin_dashboard',
      'outstanding_balance', 'add_payment', 'share_ledger_pdf',
      'collect_upi_qr', 'sales_orders', 'payment_receipts',
      'no_due_customers', 'overdue', 'due_soon', 'due', 'due_date',
    ];
    for (final k in usedKeys) {
      expect(AppLocalizations.keys, contains(k), reason: 'Missing key in contract: $k');
    }
  });
}
