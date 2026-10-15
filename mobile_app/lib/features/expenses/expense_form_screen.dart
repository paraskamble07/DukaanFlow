import 'package:flutter/material.dart';
import '../../core/localization/app_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/constants/api_constants.dart';
import '../../providers/auth_provider.dart';
import '../../providers/business_provider.dart';

class ExpenseFormScreen extends ConsumerStatefulWidget {
  const ExpenseFormScreen({super.key});

  @override
  ConsumerState<ExpenseFormScreen> createState() => _ExpenseFormScreenState();
}

class _ExpenseFormScreenState extends ConsumerState<ExpenseFormScreen> {
  final _formKey = GlobalKey<FormState>();
  final _titleController = TextEditingController();
  final _amountController = TextEditingController();
  final _notesController = TextEditingController();
  String _paymentMethod = 'CASH';
  int? _categoryId;
  DateTime _expenseDate = DateTime.now();
  bool _isSubmitting = false;

  @override
  void dispose() {
    _titleController.dispose();
    _amountController.dispose();
    _notesController.dispose();
    super.dispose();
  }

  Future<void> _pickDate() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _expenseDate,
      firstDate: DateTime(2020),
      lastDate: DateTime.now().add(const Duration(days: 1)),
    );
    if (picked != null) setState(() => _expenseDate = picked);
  }

  Future<void> _submit() async {
    final l10n = AppLocalizations.of(context);
    if (!_formKey.currentState!.validate()) return;
    setState(() => _isSubmitting = true);

    final client = ref.read(apiClientProvider);
    try {
      final res = await client.dio.post(
        ApiConstants.expenses,
        data: {
          'title': _titleController.text.trim(),
          'amount': _amountController.text.trim(),
          'category': _categoryId,
          'payment_method': _paymentMethod,
          'expense_date': '${_expenseDate.year.toString().padLeft(4, '0')}-${_expenseDate.month.toString().padLeft(2, '0')}-${_expenseDate.day.toString().padLeft(2, '0')}',
          'notes': _notesController.text.trim(),
        },
      );
      if (res.statusCode == 201 && mounted) {
        ref.invalidate(expenseListProvider);
        ref.invalidate(expenseReportProvider);
        Navigator.of(context).pop();
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(l10n.translate('expense_saved'))),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(l10n.translate('could_not_save_expense'))),
        );
      }
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final categoriesAsync = ref.watch(expenseCategoriesProvider);

    return Scaffold(
      appBar: AppBar(title: Text(l10n.translate('add_expense'))),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              TextFormField(
                controller: _titleController,
                decoration: InputDecoration(labelText: l10n.translate('expense_title_label'), hintText: l10n.translate('expense_title_hint')),
                validator: (v) => (v == null || v.trim().isEmpty) ? l10n.translate('please_enter_title') : null,
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _amountController,
                keyboardType: TextInputType.number,
                decoration: InputDecoration(labelText: l10n.translate('amount_label'), hintText: '0.00'),
                validator: (v) {
                  final amt = double.tryParse(v ?? '');
                  return (amt == null || amt <= 0) ? l10n.translate('enter_valid_amount') : null;
                },
              ),
              const SizedBox(height: 16),
              categoriesAsync.when(
                loading: () => const LinearProgressIndicator(),
                error: (_, __) => Text(l10n.translate('could_not_load_categories')),
                data: (cats) => DropdownButtonFormField<int?>(
                  value: _categoryId,
                  decoration: InputDecoration(labelText: l10n.translate('category')),
                  items: cats
                      .map((c) => DropdownMenuItem(
                            value: c['id'] as int,
                            child: Text(c['name'].toString()),
                          ))
                      .toList(),
                  onChanged: (v) => setState(() => _categoryId = v),
                ),
              ),
              const SizedBox(height: 16),
              Text(l10n.translate('payment_mode'), style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              Wrap(
                spacing: 8,
                children: ['CASH', 'UPI', 'CARD', 'BANK'].map((m) {
                  return ChoiceChip(
                    label: Text(m),
                    selected: _paymentMethod == m,
                    onSelected: (_) => setState(() => _paymentMethod = m),
                  );
                }).toList(),
              ),
              const SizedBox(height: 16),
              InkWell(
                onTap: _pickDate,
                borderRadius: BorderRadius.circular(10),
                child: InputDecorator(
                  decoration: InputDecoration(labelText: l10n.translate('expense_date'), suffixIcon: const Icon(Icons.calendar_month)),
                  child: Text(
                    '${_expenseDate.day.toString().padLeft(2, '0')}-${_expenseDate.month.toString().padLeft(2, '0')}-${_expenseDate.year}',
                    style: const TextStyle(fontSize: 15),
                  ),
                ),
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _notesController,
                maxLines: 2,
                decoration: InputDecoration(labelText: l10n.translate('notes_optional')),
              ),
              const SizedBox(height: 24),
              ElevatedButton(
                onPressed: _isSubmitting ? null : _submit,
                child: _isSubmitting
                    ? const SizedBox(height: 22, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                    : Text(l10n.translate('save_expense')),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
