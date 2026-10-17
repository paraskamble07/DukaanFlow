import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/constants/app_colors.dart';
import '../../core/localization/app_localizations.dart';
import '../../core/network/api_error.dart';
import '../../models/staff_model.dart';
import '../../providers/staff_provider.dart';

/// Staff & Logins (owner-only). Lists the shop's staff accounts, their
/// per-module access, and lets the owner add, re-grant or disable a login.
/// The backend re-checks every grant on every request; this screen only
/// reflects and manages what the owner allows.
class StaffScreen extends ConsumerWidget {
  const StaffScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final staffAsync = ref.watch(staffListProvider);
    final modulesAsync = ref.watch(allowedModulesProvider);

    return Scaffold(
      appBar: AppBar(title: Text(l10n.translate('staff_logins'))),
      body: staffAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, _) => Center(
          child: Text(
            apiErrorMessage(err, l10n),
            textAlign: TextAlign.center,
          ),
        ),
        data: (staff) => modulesAsync.when(
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (err, _) => Center(
            child: Text(
              apiErrorMessage(err, l10n),
              textAlign: TextAlign.center,
            ),
          ),
          data: (modules) => RefreshIndicator(
            onRefresh: () async => ref.refresh(staffListProvider),
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                Card(
                  color: AppColors.primary.withValues(alpha: 0.08),
                  child: Padding(
                    padding: const EdgeInsets.all(14),
                    child: Row(
                      children: [
                        const Icon(Icons.shield_outlined, color: AppColors.primary),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Text(
                            l10n.translate('staff_screen_intro'),
                            style: const TextStyle(fontSize: 12.5),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 12),
                if (staff.isEmpty)
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: 40),
                    child: Center(
                      child: Text(
                        l10n.translate('no_staff_yet'),
                        textAlign: TextAlign.center,
                        style: const TextStyle(color: AppColors.textSecondary),
                      ),
                    ),
                  )
                else
                  ...staff.map((s) => _StaffCard(staff: s)),
                const SizedBox(height: 20),
                FilledButton.icon(
                  onPressed: () => _showAddStaffDialog(context, ref, modules),
                  icon: const Icon(Icons.person_add_outlined),
                  label: Text(l10n.translate('add_staff_member')),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Future<void> _showAddStaffDialog(
      BuildContext context, WidgetRef ref, List<String> modules) async {
    final result = await showDialog<bool>(
      context: context,
      builder: (_) => _AddStaffDialog(modules: modules),
    );
    if (result == true && context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(AppLocalizations.of(context).translate('staff_added'))),
      );
    }
  }
}

class _StaffCard extends ConsumerWidget {
  final StaffModel staff;
  const _StaffCard({required this.staff});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                CircleAvatar(
                  backgroundColor: staff.isActive
                      ? AppColors.primary.withValues(alpha: 0.12)
                      : AppColors.textSecondary.withValues(alpha: 0.15),
                  child: Text(
                    (staff.firstName.isNotEmpty
                            ? staff.firstName[0]
                            : staff.email[0])
                        .toUpperCase(),
                    style: TextStyle(
                        color: staff.isActive
                            ? AppColors.primary
                            : AppColors.textSecondary),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        staff.firstName.isNotEmpty ? staff.firstName : staff.email,
                        style: const TextStyle(
                            fontWeight: FontWeight.bold, fontSize: 14.5),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        staff.firstName.isNotEmpty ? staff.email : (staff.phone ?? ''),
                        style: const TextStyle(
                            fontSize: 12, color: AppColors.textSecondary),
                      ),
                    ],
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: staff.isActive
                        ? AppColors.success.withValues(alpha: 0.12)
                        : AppColors.danger.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Text(
                    staff.isActive
                        ? l10n.translate('active')
                        : l10n.translate('disabled'),
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                      color: staff.isActive
                          ? AppColors.success
                          : AppColors.danger,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            Wrap(
              spacing: 6,
              runSpacing: 6,
              children: staff.permissions.isEmpty
                  ? [Text(l10n.translate('no_access_granted'),
                      style: const TextStyle(
                          fontSize: 12, color: AppColors.danger))]
                  : staff.permissions
                      .map((m) => Chip(
                            label: Text(m,
                                style: const TextStyle(fontSize: 11)),
                            padding: EdgeInsets.zero,
                            visualDensity: VisualDensity.compact,
                          ))
                      .toList(),
            ),
            const SizedBox(height: 10),
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                TextButton.icon(
                  onPressed: () => _editGrant(context, ref),
                  icon: const Icon(Icons.edit_outlined, size: 18),
                  label: Text(l10n.translate('edit_access')),
                ),
                const SizedBox(width: 8),
                TextButton.icon(
                  onPressed: () => _confirmToggle(context, ref),
                  icon: Icon(
                    staff.isActive ? Icons.lock_outline : Icons.lock_open_outlined,
                    size: 18,
                  ),
                  style: TextButton.styleFrom(
                    foregroundColor:
                        staff.isActive ? AppColors.danger : AppColors.success,
                  ),
                  label: Text(staff.isActive
                      ? l10n.translate('disable_login')
                      : l10n.translate('enable_login')),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _editGrant(BuildContext context, WidgetRef ref) async {
    final modules = await ref.read(allowedModulesProvider.future);
    if (!context.mounted) return;
    final current = List<String>.from(staff.permissions);
    final result = await showDialog<List<String>?>(
      context: context,
      builder: (_) => _GrantDialog(
        modules: modules,
        initial: current,
        title: staff.firstName.isNotEmpty ? staff.firstName : staff.email,
      ),
    );
    if (result == null) return;
    final res = await updateStaffGrants(ref, staff.id, result);
    if (context.mounted) {
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text(res.message)));
    }
  }

  Future<void> _confirmToggle(BuildContext context, WidgetRef ref) async {
    final l10n = AppLocalizations.of(context);
    if (staff.isActive) {
      final confirmed = await showDialog<bool>(
        context: context,
        builder: (ctx) => AlertDialog(
          title: Text(l10n.translate('disable_login_title')),
          content: Text('${l10n.translate('disable_login_body_prefix')}'
              '${staff.email}${l10n.translate('disable_login_body_suffix')}'),
          actions: [
            TextButton(
                onPressed: () => Navigator.pop(ctx, false),
                child: Text(l10n.translate('cancel'))),
            FilledButton(
              style: FilledButton.styleFrom(backgroundColor: AppColors.danger),
              onPressed: () => Navigator.pop(ctx, true),
              child: Text(l10n.translate('disable_login')),
            ),
          ],
        ),
      );
      if (confirmed != true) return;
    }
    final res = await toggleStaffActive(ref, staff.id, !staff.isActive);
    if (context.mounted) {
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text(res.message)));
    }
  }
}

class _GrantDialog extends StatefulWidget {
  final List<String> modules;
  final List<String> initial;
  final String title;
  const _GrantDialog(
      {required this.modules, required this.initial, required this.title});

  @override
  State<_GrantDialog> createState() => _GrantDialogState();
}

class _GrantDialogState extends State<_GrantDialog> {
  late final Set<String> _selected;

  @override
  void initState() {
    super.initState();
    _selected = widget.initial.toSet();
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return AlertDialog(
      title: Text('${l10n.translate('access_for')} ${widget.title}'),
      content: SizedBox(
        width: double.maxFinite,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Align(
              alignment: Alignment.centerLeft,
              child: Text(
                l10n.translate('grant_modules_hint'),
                style: const TextStyle(
                    fontSize: 12, color: AppColors.textSecondary),
              ),
            ),
            const SizedBox(height: 10),
            Wrap(
              spacing: 6,
              runSpacing: 4,
              children: widget.modules.map((m) {
                return FilterChip(
                  label: Text(m),
                  selected: _selected.contains(m),
                  onSelected: (on) => setState(() {
                    if (on) {
                      _selected.add(m);
                    } else {
                      _selected.remove(m);
                    }
                  }),
                );
              }).toList(),
            ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: Text(l10n.translate('cancel')),
        ),
        FilledButton(
          onPressed: () => Navigator.pop(context, _selected.toList()),
          child: Text(l10n.translate('save')),
        ),
      ],
    );
  }
}

class _AddStaffDialog extends ConsumerStatefulWidget {
  final List<String> modules;
  const _AddStaffDialog({required this.modules});

  @override
  ConsumerState<_AddStaffDialog> createState() => _AddStaffDialogState();
}

class _AddStaffDialogState extends ConsumerState<_AddStaffDialog> {
  final _email = TextEditingController();
  final _name = TextEditingController();
  final _phone = TextEditingController();
  final _password = TextEditingController();
  final Set<String> _grants = {'sales', 'customers'};
  bool _busy = false;
  String? _error;

  @override
  void dispose() {
    _email.dispose();
    _name.dispose();
    _phone.dispose();
    _password.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final l10n = AppLocalizations.of(context);
    final email = _email.text.trim();
    final password = _password.text;
    if (email.isEmpty || !email.contains('@')) {
      setState(() => _error = l10n.translate('enter_valid_email'));
      return;
    }
    if (password.length < 8) {
      setState(() => _error = l10n.translate('password_too_short'));
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
    });
    final res = await createStaff(
      ref,
      email: email,
      password: password,
      firstName: _name.text.trim(),
      phone: _phone.text.trim(),
      permissions: _grants.toList(),
    );
    if (!mounted) return;
    if (res.success) {
      Navigator.pop(context, true);
    } else {
      setState(() {
        _error = res.message;
        _busy = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    // With the soft keyboard open the actions (Cancel/Add) would otherwise sit
    // below the fold of a tall form on small phones — lift the dialog above
    // the keyboard instead.
    return AnimatedPadding(
      padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
      duration: const Duration(milliseconds: 120),
      child: AlertDialog(
    title: Text(l10n.translate('add_staff_member')),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: _email,
              keyboardType: TextInputType.emailAddress,
              decoration: InputDecoration(labelText: l10n.translate('email_label')),
            ),
            const SizedBox(height: 10),
            TextField(
              controller: _name,
              decoration: InputDecoration(labelText: l10n.translate('full_name')),
            ),
            const SizedBox(height: 10),
            TextField(
              controller: _phone,
              keyboardType: TextInputType.phone,
              decoration: InputDecoration(labelText: l10n.translate('phone')),
            ),
            const SizedBox(height: 10),
            TextField(
              controller: _password,
              obscureText: true,
              decoration: InputDecoration(
                  labelText: l10n.translate('password'),
                  helperText: l10n.translate('min_8_chars')),
            ),
            const SizedBox(height: 12),
            Align(
              alignment: Alignment.centerLeft,
              child: Text(
                l10n.translate('grant_modules_hint'),
                style: const TextStyle(
                    fontSize: 12, color: AppColors.textSecondary),
              ),
            ),
            const SizedBox(height: 6),
            Wrap(
              spacing: 6,
              runSpacing: 4,
              children: widget.modules.map((m) {
                return FilterChip(
                  label: Text(m),
                  selected: _grants.contains(m),
                  onSelected: (on) => setState(() {
                    if (on) {
                      _grants.add(m);
                    } else {
                      _grants.remove(m);
                    }
                  }),
                );
              }).toList(),
            ),
            if (_error != null) ...[
              const SizedBox(height: 10),
              Text(_error!,
                  style: const TextStyle(color: AppColors.danger, fontSize: 12.5)),
            ],
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: _busy ? null : () => Navigator.pop(context),
          child: Text(l10n.translate('cancel')),
        ),
        FilledButton(
          onPressed: _busy ? null : _submit,
          child: _busy
              ? const SizedBox(
                  width: 18, height: 18,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : Text(l10n.translate('add')),
        ),
      ],
      ),
    );
  }
}
