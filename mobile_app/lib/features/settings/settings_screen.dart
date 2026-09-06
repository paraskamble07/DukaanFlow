import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/constants/api_constants.dart';
import '../../core/constants/app_colors.dart';
import '../../providers/auth_provider.dart';
import '../../providers/settings_provider.dart';
import '../auth/splash_screen.dart';

class SettingsScreen extends ConsumerStatefulWidget {
  const SettingsScreen({super.key});

  @override
  ConsumerState<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends ConsumerState<SettingsScreen> {
  final _nameController = TextEditingController();
  final _phoneController = TextEditingController();
  final _addressController = TextEditingController();
  final _gstinController = TextEditingController();
  final _prefixController = TextEditingController();
  bool _isEditingShop = false;
  bool _isSaving = false;

  @override
  void dispose() {
    _nameController.dispose();
    _phoneController.dispose();
    _addressController.dispose();
    _gstinController.dispose();
    _prefixController.dispose();
    super.dispose();
  }

  void _startEditing() {
    final biz = ref.read(authProvider).business;
    if (biz == null) return;
    _nameController.text = biz.name;
    _phoneController.text = biz.phone;
    _addressController.text = biz.address ?? '';
    _gstinController.text = biz.gstin ?? '';
    _prefixController.text = biz.invoicePrefix;
    setState(() => _isEditingShop = true);
  }

  Future<void> _saveShop() async {
    setState(() => _isSaving = true);
    final client = ref.read(apiClientProvider);
    try {
      final res = await client.dio.put(
        ApiConstants.businessSettings,
        data: {
          'name': _nameController.text.trim(),
          'phone': _phoneController.text.trim(),
          'address': _addressController.text.trim(),
          'gstin': _gstinController.text.trim(),
          'invoice_prefix': _prefixController.text.trim(),
        },
      );
      if (res.statusCode == 200 && mounted) {
        await ref.read(authProvider.notifier).fetchProfile();
        setState(() => _isEditingShop = false);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Shop profile updated. Invoices will use the new details.')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Could not save shop profile. Please try again.')),
        );
      }
    } finally {
      if (mounted) setState(() => _isSaving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final settings = ref.watch(settingsProvider);
    final auth = ref.watch(authProvider);
    final business = auth.business;

    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Appearance
          _sectionCard(
            title: 'Appearance',
            children: [
              const Text('Theme', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
              const SizedBox(height: 8),
              SegmentedButton<ThemeMode>(
                segments: const [
                  ButtonSegment(value: ThemeMode.light, label: Text('Light'), icon: Icon(Icons.light_mode)),
                  ButtonSegment(value: ThemeMode.system, label: Text('System'), icon: Icon(Icons.settings_suggest)),
                  ButtonSegment(value: ThemeMode.dark, label: Text('Dark'), icon: Icon(Icons.dark_mode)),
                ],
                selected: {settings.themeMode},
                onSelectionChanged: (modes) => ref.read(settingsProvider.notifier).setThemeMode(modes.first),
              ),
              const SizedBox(height: 16),
              const Text('Language', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
              const SizedBox(height: 8),
              SegmentedButton<String>(
                segments: const [
                  ButtonSegment(value: 'en', label: Text('English')),
                  ButtonSegment(value: 'hi', label: Text('हिंदी')),
                  ButtonSegment(value: 'mr', label: Text('मराठी')),
                ],
                selected: {settings.locale.languageCode},
                onSelectionChanged: (langs) => ref.read(settingsProvider.notifier).setLocale(langs.first),
              ),
            ],
          ),
          const SizedBox(height: 16),

          // Shop profile
          _sectionCard(
            title: 'Shop Profile',
            children: _isEditingShop
                ? [
                    TextField(
                      controller: _nameController,
                      decoration: const InputDecoration(labelText: 'Shop Name'),
                    ),
                    const SizedBox(height: 12),
                    TextField(
                      controller: _phoneController,
                      keyboardType: TextInputType.phone,
                      decoration: const InputDecoration(labelText: 'Phone'),
                    ),
                    const SizedBox(height: 12),
                    TextField(
                      controller: _addressController,
                      maxLines: 2,
                      decoration: const InputDecoration(labelText: 'Address'),
                    ),
                    const SizedBox(height: 12),
                    TextField(
                      controller: _gstinController,
                      decoration: const InputDecoration(labelText: 'GSTIN'),
                    ),
                    const SizedBox(height: 12),
                    TextField(
                      controller: _prefixController,
                      decoration: const InputDecoration(labelText: 'Invoice Prefix', hintText: 'SZ-'),
                    ),
                    const SizedBox(height: 16),
                    Row(
                      children: [
                        Expanded(
                          child: OutlinedButton(
                            onPressed: () => setState(() => _isEditingShop = false),
                            child: const Text('Cancel'),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          flex: 2,
                          child: ElevatedButton(
                            onPressed: _isSaving ? null : _saveShop,
                          child: _isSaving ? const Text('Saving...') : const Text('Save Changes'),
                          ),
                        ),
                      ],
                    ),
                  ]
                : [
                    _profileRow('Shop', business?.name ?? '-'),
                    _profileRow('Owner', business?.ownerName ?? auth.user?.firstName ?? '-'),
                    _profileRow('Phone', business?.phone ?? '-'),
                    _profileRow('GSTIN', (business?.gstin ?? '').isEmpty ? 'Not set' : business!.gstin!),
                    _profileRow('Invoice Prefix', business?.invoicePrefix ?? '-'),
                    const SizedBox(height: 8),
                    Align(
                      alignment: Alignment.centerRight,
                      child: TextButton.icon(
                        onPressed: _startEditing,
                        icon: const Icon(Icons.edit, size: 18),
                        label: const Text('Edit Shop Profile'),
                      ),
                    ),
                  ],
          ),
          const SizedBox(height: 16),

          // Account
          _sectionCard(
            title: 'Account',
            children: [
              _profileRow('Logged in as', auth.user?.email ?? '-'),
              _profileRow('Role', auth.user?.role ?? 'OWNER'),
            ],
          ),
          const SizedBox(height: 24),

          // Logout
          OutlinedButton.icon(
            style: OutlinedButton.styleFrom(
              foregroundColor: AppColors.danger,
              side: const BorderSide(color: AppColors.danger),
              minimumSize: const Size.fromHeight(48),
            ),
            onPressed: () async {
              final confirmed = await showDialog<bool>(
                context: context,
                builder: (ctx) => AlertDialog(
                  title: const Text('Logout from ShopZen?'),
                  content: const Text('All your shop data stays safe in the cloud. You can login again from any phone.'),
                  actions: [
                    TextButton(onPressed: () => Navigator.of(ctx).pop(false), child: const Text('Cancel')),
                    ElevatedButton(
                      style: ElevatedButton.styleFrom(backgroundColor: AppColors.danger, foregroundColor: Colors.white),
                      onPressed: () => Navigator.of(ctx).pop(true),
                      child: const Text('Logout'),
                    ),
                  ],
                ),
              );
              if (confirmed == true && context.mounted) {
                await ref.read(authProvider.notifier).logout();
                if (context.mounted) {
                  Navigator.of(context).pushAndRemoveUntil(
                    MaterialPageRoute(builder: (_) => const SplashScreen()),
                    (_) => false,
                  );
                }
              }
            },
            icon: const Icon(Icons.logout),
            label: const Text('Logout', style: TextStyle(fontWeight: FontWeight.bold)),
          ),
        ],
      ),
    );
  }

  Widget _sectionCard({required String title, required List<Widget> children}) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              title.toUpperCase(),
              style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppColors.textSecondary, letterSpacing: 1),
            ),
            const SizedBox(height: 12),
            ...children,
          ],
        ),
      ),
    );
  }

  Widget _profileRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 5),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: const TextStyle(fontSize: 13, color: AppColors.textSecondary)),
          Flexible(
            child: Text(
              value,
              style: const TextStyle(fontSize: 13.5, fontWeight: FontWeight.w600),
              textAlign: TextAlign.right,
            ),
          ),
        ],
      ),
    );
  }
}
