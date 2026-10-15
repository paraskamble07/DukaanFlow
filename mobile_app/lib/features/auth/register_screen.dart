import 'package:flutter/material.dart';
import '../../core/localization/app_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/constants/app_colors.dart';
import '../../providers/auth_provider.dart';
import '../../main.dart';
import 'login_screen.dart';

class RegisterScreen extends ConsumerStatefulWidget {
  const RegisterScreen({super.key});

  @override
  ConsumerState<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends ConsumerState<RegisterScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _shopNameController = TextEditingController();
  final _phoneController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();

  @override
  void dispose() {
    _nameController.dispose();
    _shopNameController.dispose();
    _phoneController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _handleRegister() async {
    if (!_formKey.currentState!.validate()) return;

    final success = await ref.read(authProvider.notifier).register(
      fullName: _nameController.text,
      shopName: _shopNameController.text,
      phone: _phoneController.text,
      email: _emailController.text,
      password: _passwordController.text,
    );

    if (success && mounted) {
      Navigator.of(context).pushAndRemoveUntil(
        MaterialPageRoute(builder: (_) => const MainNavigationScaffold()),
        (route) => false,
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final authState = ref.watch(authProvider);

    return Scaffold(
      appBar: AppBar(title: Text(l10n.translate('create_shop_account'))),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24.0),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  l10n.translate('start_with_app'),
                  style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
                ),
                Text(
                  l10n.translate('onboarding_fast'),
                  style: const TextStyle(color: AppColors.textSecondary, fontSize: 14),
                ),
                const SizedBox(height: 24),

                if (authState.errorMessage != null)
                  Container(
                    padding: const EdgeInsets.all(12),
                    margin: const EdgeInsets.only(bottom: 16),
                    decoration: BoxDecoration(
                      color: AppColors.danger.withValues(alpha: 0.1),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          authState.errorMessage!,
                          style: const TextStyle(color: AppColors.danger, fontSize: 13),
                        ),
                        if (authState.errorMessage!
                            .contains('already registered')) ...[
                          const SizedBox(height: 8),
                          SizedBox(
                            width: double.infinity,
                            child: OutlinedButton.icon(
                              onPressed: () =>
                                  Navigator.of(context).pushReplacement(
                                MaterialPageRoute(
                                    builder: (_) => const LoginScreen()),
                              ),
                              icon: const Icon(Icons.login, size: 16),
                              label: Text(l10n.translate('login_instead')),
                            ),
                          ),
                        ],
                      ],
                    ),
                  ),

                Text(l10n.translate('owner_full_name'), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                const SizedBox(height: 6),
                TextFormField(
                  controller: _nameController,
                  decoration: InputDecoration(hintText: l10n.translate('owner_name_hint')),
                  validator: (v) => (v == null || v.isEmpty) ? l10n.translate('please_enter_your_name') : null,
                ),
                const SizedBox(height: 14),

                Text(l10n.translate('shop_name_label'), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                const SizedBox(height: 6),
                TextFormField(
                  controller: _shopNameController,
                  decoration: InputDecoration(hintText: l10n.translate('shop_name_hint')),
                  validator: (v) => (v == null || v.isEmpty) ? l10n.translate('please_enter_shop_name') : null,
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

                Text(l10n.translate('email_address'), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                const SizedBox(height: 6),
                TextFormField(
                  controller: _emailController,
                  keyboardType: TextInputType.emailAddress,
                  decoration: InputDecoration(hintText: l10n.translate('email_hint')),
                  validator: (v) => (v == null || !v.contains('@')) ? l10n.translate('enter_valid_email') : null,
                ),
                const SizedBox(height: 14),

                Text(l10n.translate('create_password'), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                const SizedBox(height: 6),
                TextFormField(
                  controller: _passwordController,
                  obscureText: true,
                  decoration: InputDecoration(hintText: l10n.translate('password_hint')),
                  validator: (v) => (v == null || v.length < 6) ? l10n.translate('password_min_chars') : null,
                ),
                const SizedBox(height: 24),

                ElevatedButton(
                  onPressed: authState.isLoading ? null : _handleRegister,
                  child: authState.isLoading
                      ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                      : Text(l10n.translate('create_shop_trial')),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
