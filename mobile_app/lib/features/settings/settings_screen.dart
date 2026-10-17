import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/ads/ad_banner.dart';
import '../../core/constants/api_constants.dart';
import '../../core/constants/app_colors.dart';
import '../../core/localization/app_localizations.dart';
import '../../providers/auth_provider.dart';
import '../../providers/settings_provider.dart';
import '../auth/splash_screen.dart';
import '../staff/staff_screen.dart';
import 'app_update_screen.dart';
import 'backup_restore_screen.dart';

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
  final _upiController = TextEditingController();
  final _prefixController = TextEditingController();
  bool _isEditingShop = false;
  bool _isSaving = false;

  @override
  void dispose() {
    _nameController.dispose();
    _phoneController.dispose();
    _addressController.dispose();
    _gstinController.dispose();
    _upiController.dispose();
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
    _upiController.text = biz.upiId ?? '';
    _prefixController.text = biz.invoicePrefix;
    setState(() => _isEditingShop = true);
  }

  Future<void> _saveShop() async {
    final l10n = AppLocalizations.of(context);
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
          'upi_id': _upiController.text.trim(),
          'invoice_prefix': _prefixController.text.trim(),
        },
      );
      if (res.statusCode == 200 && mounted) {
        await ref.read(authProvider.notifier).fetchProfile();
        setState(() => _isEditingShop = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(l10n.translate('shop_profile_updated'))),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(l10n.translate('could_not_save_profile'))),
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
    final l10n = AppLocalizations.of(context);
    final business = auth.business;

    return Scaffold(
      appBar: AppBar(title: Text(l10n.translate('settings'))),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Appearance
          _sectionCard(
            title: l10n.translate('appearance'),
            children: [
              Text(l10n.translate('theme'), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
              const SizedBox(height: 8),
              SegmentedButton<ThemeMode>(
                segments: [
                  ButtonSegment(value: ThemeMode.light, label: Text(l10n.translate('light')), icon: const Icon(Icons.light_mode)),
                  ButtonSegment(value: ThemeMode.system, label: Text(l10n.translate('system')), icon: const Icon(Icons.settings_suggest)),
                  ButtonSegment(value: ThemeMode.dark, label: Text(l10n.translate('dark')), icon: const Icon(Icons.dark_mode)),
                ],
                selected: {settings.themeMode},
                onSelectionChanged: (modes) => ref.read(settingsProvider.notifier).setThemeMode(modes.first),
              ),
              const SizedBox(height: 16),
              Text(l10n.translate('language'), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
              const SizedBox(height: 8),
              SegmentedButton<String>(
                segments: [
                  ButtonSegment(value: 'en', label: Text(l10n.translate('english'))),
                  const ButtonSegment(value: 'hi', label: Text('हिंदी')),
                  const ButtonSegment(value: 'mr', label: Text('मराठी')),
                ],
                selected: {settings.locale.languageCode},
                onSelectionChanged: (langs) => ref.read(settingsProvider.notifier).setLocale(langs.first),
              ),
            ],
          ),
          const SizedBox(height: 16),

// Shop profile
          _sectionCard(
            title: l10n.translate('shop_profile'),
            children: _isEditingShop
                ? [
                    TextField(
                      controller: _nameController,
                      decoration: InputDecoration(labelText: l10n.translate('shop_name')),
                    ),
                    const SizedBox(height: 12),
                    TextField(
                      controller: _phoneController,
                      keyboardType: TextInputType.phone,
                      decoration: InputDecoration(labelText: l10n.translate('phone')),
                    ),
                    const SizedBox(height: 12),
                    TextField(
                      controller: _addressController,
                      maxLines: 2,
                      decoration: InputDecoration(labelText: l10n.translate('address')),
                    ),
                    const SizedBox(height: 12),
                    TextField(
                      controller: _gstinController,
                      decoration: InputDecoration(labelText: l10n.translate('gstin_label')),
                    ),
                    const SizedBox(height: 12),
                    TextField(
                      controller: _upiController,
                      decoration: InputDecoration(
                        labelText: l10n.translate('upi_id'),
                        hintText: l10n.translate('upi_id_hint'),
                        helperText: l10n.translate('upi_id_helper'),
                      ),
                    ),
                    const SizedBox(height: 12),
                    TextField(
                      controller: _prefixController,
                      decoration: InputDecoration(labelText: l10n.translate('invoice_prefix'), hintText: 'SZ-'),
                    ),
                    const SizedBox(height: 16),
                    Row(
                      children: [
                        Expanded(
                          child: OutlinedButton(
                            onPressed: () => setState(() => _isEditingShop = false),
                            child: Text(l10n.translate('cancel')),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          flex: 2,
                          child: ElevatedButton(
                            onPressed: _isSaving ? null : _saveShop,
                            child: _isSaving
                                ? const SizedBox(
                                    width: 18,
                                    height: 18,
                                    child: CircularProgressIndicator(strokeWidth: 2),
                                  )
                                : Text(l10n.translate('save_changes')),
                          ),
                        ),
                      ],
                    ),
                  ]
                : [
                    _profileRow(l10n.translate('shop_label'), business?.name ?? '-'),
                    _profileRow(l10n.translate('owner_label'), business?.ownerName ?? auth.user?.firstName ?? '-'),
                    _profileRow(l10n.translate('phone'), business?.phone ?? '-'),
                    _profileRow(l10n.translate('gstin_label'), (business?.gstin ?? '').isEmpty ? l10n.translate('not_set') : business!.gstin!),
                    _profileRow(l10n.translate('upi_id'), (business?.upiId ?? '').isEmpty ? l10n.translate('not_set') : business!.upiId!),
                    _profileRow(l10n.translate('invoice_prefix'), business?.invoicePrefix ?? '-'),
                    const SizedBox(height: 8),
                    // Only the owner may edit shop settings (the endpoint is
                    // owner-only; staff would otherwise hit a 403).
                    if (auth.user?.role == 'OWNER')
                      Align(
                        alignment: Alignment.centerRight,
                        child: TextButton.icon(
                          onPressed: _startEditing,
                          icon: const Icon(Icons.edit, size: 18),
                          label: Text(l10n.translate('edit_shop_profile')),
                        ),
                      ),
                  ],
          ),
          const SizedBox(height: 16),

          // Staff & logins (owner-only: create staff, grant modules, disable logins)
          if (auth.user?.role == 'OWNER') ...[
            _sectionCard(
              title: l10n.translate('team'),
              children: [
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: const Icon(Icons.group_outlined, color: AppColors.primary),
                  title: Text(l10n.translate('staff_logins'),
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                  subtitle: Text(l10n.translate('staff_logins_sub'),
                      style: TextStyle(fontSize: 12, color: AppColors.textSecondary)),
                  trailing: const Icon(Icons.chevron_right, color: AppColors.textSecondary),
                  onTap: () => Navigator.of(context).push(
                    MaterialPageRoute(builder: (_) => const StaffScreen()),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
          ],

          // Account
          _sectionCard(
            title: l10n.translate('account'),
            children: [
              _profileRow(l10n.translate('logged_in_as'), auth.user?.email ?? '-'),
              _profileRow(l10n.translate('role'), auth.user?.role ?? 'OWNER'),
            ],
          ),
          const SizedBox(height: 16),

          // App Updates (Phase 21)
          _sectionCard(
            title: l10n.translate('application'),
            children: [
              ListTile(
                contentPadding: EdgeInsets.zero,
                leading: const Icon(Icons.system_update_rounded, color: AppColors.primary),
                title: Text(l10n.translate('app_updates'), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                subtitle: Text(l10n.translate('app_updates_sub'),
                    style: TextStyle(fontSize: 12, color: AppColors.textSecondary)),
                trailing: const Icon(Icons.chevron_right, color: AppColors.textSecondary),
                onTap: () => Navigator.of(context).push(
                  MaterialPageRoute(builder: (_) => const AppUpdateScreen()),
                ),
              ),
              ListTile(
                contentPadding: EdgeInsets.zero,
                leading: const Icon(Icons.backup_outlined, color: AppColors.primary),
                title: Text(l10n.translate('backup_restore_title'),
                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                subtitle: Text(l10n.translate('backup_restore_sub'),
                    style: TextStyle(fontSize: 12, color: AppColors.textSecondary)),
                trailing: const Icon(Icons.chevron_right, color: AppColors.textSecondary),
                onTap: () => Navigator.of(context).push(
                  MaterialPageRoute(builder: (_) => const BackupRestoreScreen()),
                ),
              ),
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
                  title: Text(l10n.translate('logout_title')),
                  content: Text(l10n.translate('logout_content')),
                  actions: [
                    TextButton(onPressed: () => Navigator.of(ctx).pop(false), child: Text(l10n.translate('cancel'))),
                    ElevatedButton(
                      style: ElevatedButton.styleFrom(backgroundColor: AppColors.danger, foregroundColor: Colors.white),
                      onPressed: () => Navigator.of(ctx).pop(true),
                      child: Text(l10n.translate('logout')),
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
            label: Text(l10n.translate('logout'), style: const TextStyle(fontWeight: FontWeight.bold)),
          ),
          const SizedBox(height: 24),

          // Ads (Phase 12): banner ads keep ShopZen free for every shop.
          Text(
            l10n.translate('ads_keep_app_free'),
            textAlign: TextAlign.center,
            style: const TextStyle(fontSize: 11, color: AppColors.textSecondary),
          ),
          const SizedBox(height: 4),
          const AdBanner(),
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
