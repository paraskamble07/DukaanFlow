import 'package:flutter/material.dart';
import '../../core/localization/app_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/constants/api_constants.dart';
import '../../providers/auth_provider.dart';
import '../../providers/business_provider.dart';

class SupplierFormScreen extends ConsumerStatefulWidget {
  const SupplierFormScreen({super.key});

  @override
  ConsumerState<SupplierFormScreen> createState() => _SupplierFormScreenState();
}

class _SupplierFormScreenState extends ConsumerState<SupplierFormScreen> {
  final _formKey = GlobalKey<FormState>();
  final _companyController = TextEditingController();
  final _contactController = TextEditingController();
  final _phoneController = TextEditingController();
  final _emailController = TextEditingController();
  final _addressController = TextEditingController();
  final _gstinController = TextEditingController();
  final _notesController = TextEditingController();
  bool _isSubmitting = false;

  @override
  void dispose() {
    _companyController.dispose();
    _contactController.dispose();
    _phoneController.dispose();
    _emailController.dispose();
    _addressController.dispose();
    _gstinController.dispose();
    _notesController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final l10n = AppLocalizations.of(context);
    if (!_formKey.currentState!.validate()) return;
    setState(() => _isSubmitting = true);

    final client = ref.read(apiClientProvider);
    try {
      final res = await client.dio.post(
        ApiConstants.suppliers,
        data: {
          'company_name': _companyController.text.trim(),
          'name': _contactController.text.trim(),
          'phone': _phoneController.text.trim(),
          'email': _emailController.text.trim(),
          'address': _addressController.text.trim(),
          'gstin': _gstinController.text.trim(),
          'notes': _notesController.text.trim(),
        },
      );
      if (res.statusCode == 201 && mounted) {
        ref.invalidate(supplierListProvider);
        Navigator.of(context).pop();
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(l10n.translate('supplier_saved'))),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(l10n.translate('could_not_save_supplier'))),
        );
      }
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Scaffold(
      appBar: AppBar(title: Text(l10n.translate('add_supplier'))),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _formKey,
          child: Column(
            children: [
              TextFormField(
                controller: _companyController,
                decoration: InputDecoration(labelText: l10n.translate('company_name_label')),
                validator: (v) => (v == null || v.trim().isEmpty) ? l10n.translate('company_name_required') : null,
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _contactController,
                decoration: InputDecoration(labelText: l10n.translate('contact_person')),
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _phoneController,
                keyboardType: TextInputType.phone,
                decoration: InputDecoration(labelText: l10n.translate('phone_number')),
                validator: (v) {
                  final digits = (v ?? '').replaceAll(RegExp(r'[^0-9]'), '');
                  return digits.length < 10 ? l10n.translate('enter_valid_10_digit') : null;
                },
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _emailController,
                keyboardType: TextInputType.emailAddress,
                decoration: InputDecoration(labelText: l10n.translate('email_optional')),
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _addressController,
                maxLines: 2,
                decoration: InputDecoration(labelText: l10n.translate('address_optional')),
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _gstinController,
                decoration: InputDecoration(labelText: l10n.translate('gstin_optional')),
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
                    : Text(l10n.translate('save_supplier')),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
