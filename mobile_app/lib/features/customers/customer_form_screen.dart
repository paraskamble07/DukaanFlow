import 'package:flutter/material.dart';
import '../../core/localization/app_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/constants/api_constants.dart';
import '../../models/customer_model.dart';
import '../../providers/auth_provider.dart';
import '../../providers/customer_provider.dart';

class CustomerFormScreen extends ConsumerStatefulWidget {
  final CustomerModel? customer;

  const CustomerFormScreen({super.key, this.customer});

  @override
  ConsumerState<CustomerFormScreen> createState() => _CustomerFormScreenState();
}

class _CustomerFormScreenState extends ConsumerState<CustomerFormScreen> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _nameController;
  late final TextEditingController _phoneController;
  late final TextEditingController _addressController;
  late final TextEditingController _creditLimitController;
  bool _isSubmitting = false;

  @override
  void initState() {
    super.initState();
    final c = widget.customer;
    _nameController = TextEditingController(text: c?.name ?? '');
    _phoneController = TextEditingController(text: c?.phone ?? '');
    _addressController = TextEditingController(text: c?.address ?? '');
    _creditLimitController = TextEditingController(text: c?.creditLimit.toString() ?? '5000');
  }

  @override
  void dispose() {
    _nameController.dispose();
    _phoneController.dispose();
    _addressController.dispose();
    _creditLimitController.dispose();
    super.dispose();
  }

  Future<void> _saveCustomer() async {
    final l10n = AppLocalizations.of(context);
    if (!_formKey.currentState!.validate()) return;
    setState(() => _isSubmitting = true);

    final client = ref.read(apiClientProvider);
    final payload = {
      'name': _nameController.text.trim(),
      'phone': _phoneController.text.trim(),
      'address': _addressController.text.trim(),
      'credit_limit': double.tryParse(_creditLimitController.text) ?? 0.0,
    };

    try {
      if (widget.customer != null) {
        await client.dio.put('${ApiConstants.customers}${widget.customer!.id}/', data: payload);
      } else {
        await client.dio.post(ApiConstants.customers, data: payload);
      }
      ref.invalidate(customerListProvider);
      if (mounted) {
        Navigator.of(context).pop();
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(l10n.translate('customer_saved'))),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("${l10n.translate('error_prefix')}$e")));
      }
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Scaffold(
      appBar: AppBar(title: Text(widget.customer != null ? l10n.translate('edit_customer') : l10n.translate('add_new_customer'))),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20.0),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(l10n.translate('customer_name_label'), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
              const SizedBox(height: 6),
              TextFormField(
                controller: _nameController,
                decoration: InputDecoration(hintText: l10n.translate('customer_name_hint')),
                validator: (v) => (v == null || v.isEmpty) ? l10n.translate('please_enter_name') : null,
              ),
              const SizedBox(height: 14),

              Text(l10n.translate('mobile_whatsapp_label'), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
              const SizedBox(height: 6),
              TextFormField(
                controller: _phoneController,
                keyboardType: TextInputType.phone,
                decoration: InputDecoration(hintText: l10n.translate('mobile_hint')),
                validator: (v) => (v == null || v.length < 10) ? l10n.translate('enter_valid_mobile') : null,
              ),
              const SizedBox(height: 14),

              Text(l10n.translate('address_locality'), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
              const SizedBox(height: 6),
              TextFormField(
                controller: _addressController,
                decoration: InputDecoration(hintText: l10n.translate('address_hint')),
              ),
              const SizedBox(height: 14),

              Text(l10n.translate('credit_limit'), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
              const SizedBox(height: 6),
              TextFormField(
                controller: _creditLimitController,
                keyboardType: TextInputType.number,
                decoration: InputDecoration(hintText: '5000'),
              ),
              const SizedBox(height: 24),

              ElevatedButton(
                onPressed: _isSubmitting ? null : _saveCustomer,
                child: _isSubmitting ? const CircularProgressIndicator() : Text(l10n.translate('save_customer')),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
