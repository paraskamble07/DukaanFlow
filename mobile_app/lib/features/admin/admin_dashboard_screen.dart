import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import '../../core/localization/app_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/constants/api_constants.dart';
import '../../core/constants/app_colors.dart';
import '../../providers/admin_provider.dart';
import '../../providers/auth_provider.dart';

/// ShopZen Admin Dashboard — visible only when the signed-in account is a
/// backend-authorized admin. All data comes from /api/admin/* which rejects
/// everyone else with 403, so the app UI is never the security boundary.
///
/// Monetization is AdMob-only as of this build: the ₹30 subscription
/// payment-verification workflow was retired, so this dashboard now
/// manages app releases (Phase 21) and registered shops. Historical
/// subscription data remains visible in the shops list.
class AdminDashboardScreen extends ConsumerStatefulWidget {
  const AdminDashboardScreen({super.key});

  @override
  ConsumerState<AdminDashboardScreen> createState() => _AdminDashboardScreenState();
}

class _AdminDashboardScreenState extends ConsumerState<AdminDashboardScreen> {
  @override
  Widget build(BuildContext context) {
    final dashAsync = ref.watch(adminDashboardProvider);

    return DefaultTabController(
      length: 3,
      child: Scaffold(
        appBar: AppBar(
          title: Text(AppLocalizations.of(context).translate('shopzen_admin')),
          actions: [
            IconButton(
              tooltip: AppLocalizations.of(context).translate('refresh'),
              icon: const Icon(Icons.refresh),
              onPressed: () {
                ref.invalidate(adminDashboardProvider);
                ref.invalidate(adminAppReleasesProvider);
                ref.invalidate(adminShopsProvider);
              },
            ),
          ],
          bottom: TabBar(
            tabs: [
              Tab(icon: const Icon(Icons.dashboard_outlined), text: AppLocalizations.of(context).translate('tab_overview')),
              Tab(icon: const Icon(Icons.system_update_alt_rounded), text: AppLocalizations.of(context).translate('tab_releases')),
              Tab(icon: const Icon(Icons.storefront_outlined), text: AppLocalizations.of(context).translate('tab_shops')),
            ],
          ),
        ),
        body: TabBarView(
          children: [
            // ---------------- Overview ----------------
            dashAsync.when(
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (err, _) => _errView('${AppLocalizations.of(context).translate('could_not_load_admin_stats')}$err'),
              data: (d) => RefreshIndicator(
                onRefresh: () async => ref.refresh(adminDashboardProvider.future),
                child: ListView(
                  padding: const EdgeInsets.all(16),
                  children: [
                    Wrap(
                      spacing: 12,
                      runSpacing: 12,
                      children: [
                        _statCard(AppLocalizations.of(context).translate('stat_total_users'), d['total_users'], Icons.people_outline),
                        _statCard(AppLocalizations.of(context).translate('stat_shops'), d['total_shops'], Icons.storefront_outlined),
                        _statCard(AppLocalizations.of(context).translate('stat_active_subs'), d['active_subscriptions'], Icons.verified_outlined, color: AppColors.success),
                        _statCard(AppLocalizations.of(context).translate('stat_expired'), d['expired_subscriptions'], Icons.timer_off_rounded, color: AppColors.danger),
                        _statCard(AppLocalizations.of(context).translate('stat_pending'), d['pending_payment_requests'], Icons.hourglass_top_rounded, color: Colors.orange),
                        _statCard(AppLocalizations.of(context).translate('stat_approved'), d['approved_payments'], Icons.check_circle_outline, color: AppColors.success),
                        _statCard(AppLocalizations.of(context).translate('stat_rejected'), d['rejected_payments'], Icons.cancel_outlined, color: AppColors.danger),
                        _statCard(AppLocalizations.of(context).translate('stat_revenue'), d['total_subscription_revenue'], Icons.currency_rupee_rounded, color: AppColors.success),
                      ],
                    ),
                    const SizedBox(height: 20),
                    _recentCard(d),
                  ],
                ),
              ),
            ),

            // ---------------- App releases ----------------
            Consumer(builder: (context, ref2, _) {
              final releasesAsync = ref2.watch(adminAppReleasesProvider);
              return Stack(
                children: [
                  releasesAsync.when(
                    loading: () => const Center(child: CircularProgressIndicator()),
                    error: (err, _) => _errView('${AppLocalizations.of(context).translate('could_not_load_releases')}$err'),
                    data: (list) {
                      if (list.isEmpty) {
                        return ListView(
                          physics: const AlwaysScrollableScrollPhysics(),
                          children: [
                            const SizedBox(height: 120),
                            Center(child: Text(AppLocalizations.of(context).translate('no_app_releases'),
                                style: TextStyle(color: AppColors.textSecondary))),
                          ],
                        );
                      }
                      return RefreshIndicator(
                        onRefresh: () async =>
                            ref2.refresh(adminAppReleasesProvider.future),
                        child: ListView.separated(
                          padding: const EdgeInsets.all(12),
                          itemCount: list.length,
                          separatorBuilder: (_, __) => const SizedBox(height: 10),
                          itemBuilder: (_, i) => _releaseCard(list[i]),
                        ),
                      );
                    },
                  ),
                  Positioned(
                    right: 16,
                    bottom: 16,
                    child: FloatingActionButton.extended(
                      onPressed: () => _showPublishDialog(context),
                      backgroundColor: AppColors.primary,
                      foregroundColor: Colors.white,
                      icon: const Icon(Icons.upload_rounded),
                      label: Text(AppLocalizations.of(context).translate('publish')),
                    ),
                  ),
                ],
              );
            }),

            // ---------------- Shops list ----------------
            Consumer(builder: (context, ref2, _) {
              final shopsAsync = ref2.watch(adminShopsProvider);
              return Column(
                children: [
                  Padding(
                    padding: const EdgeInsets.fromLTRB(16, 12, 16, 4),
                    child: TextField(
                      decoration: InputDecoration(
                        hintText: AppLocalizations.of(context).translate('search_shop_owner'),
                        prefixIcon: const Icon(Icons.search),
                        isDense: true,
                        border: OutlineInputBorder(),
                      ),
                      onSubmitted: (v) =>
                          ref2.read(adminShopSearchProvider.notifier).state = v.trim(),
                    ),
                  ),
                  const SizedBox(height: 4),
                  Expanded(
                    child: shopsAsync.when(
                      loading: () => const Center(child: CircularProgressIndicator()),
                      error: (err, _) =>
                          _errView('${AppLocalizations.of(context).translate('could_not_load_shops')}$err'),
                      data: (shops) {
                        if (shops.isEmpty) {
                          return ListView(
                            physics: const AlwaysScrollableScrollPhysics(),
                            children: [
                              const SizedBox(height: 120),
                              Center(child: Text(AppLocalizations.of(context).translate('no_shops_found'),
                                  style: TextStyle(color: AppColors.textSecondary))),
                            ],
                          );
                        }
                        return RefreshIndicator(
                          onRefresh: () async =>
                              ref2.refresh(adminShopsProvider.future),
                          child: ListView.separated(
                            padding: const EdgeInsets.all(12),
                            itemCount: shops.length,
                            separatorBuilder: (_, __) => const SizedBox(height: 10),
                            itemBuilder: (_, i) => _shopCard(shops[i]),
                          ),
                        );
                      },
                    ),
                  ),
                ],
              );
            }),
          ],
        ),
      ),
    );
  }

  Widget _errView(String msg) => ListView(
        physics: const AlwaysScrollableScrollPhysics(),
        children: [
          const SizedBox(height: 120),
          Center(child: Text(msg, textAlign: TextAlign.center)),
        ],
      );

  Widget _shopCard(Map<String, dynamic> s) {
    final active = s['subscription_status'] == 'ACTIVE';
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(s['shop'] ?? '-',
                      maxLines: 1, overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: (active ? AppColors.success : AppColors.danger)
                        .withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    s['subscription_status'] ?? '-',
                    style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 6),
            Text("${AppLocalizations.of(context).translate('owner_label')}${s['owner'] ?? '-'}", style: const TextStyle(fontSize: 12.5)),
            Text("${AppLocalizations.of(context).translate('email_label2')}${s['email'] ?? '-'}", style: const TextStyle(fontSize: 12.5)),
            if ((s['phone'] ?? '').toString().isNotEmpty)
              Text("${AppLocalizations.of(context).translate('phone_label2')}${s['phone']}", style: const TextStyle(fontSize: 12.5)),
            const SizedBox(height: 6),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text("${AppLocalizations.of(context).translate('registered_label')}${s['created'] ?? '-'}",
                    style: const TextStyle(fontSize: 11, color: AppColors.textSecondary)),
                Text(
                  active
                      ? "${AppLocalizations.of(context).translate('expires_label')}${s['subscription_end']} (${s['days_remaining']}${AppLocalizations.of(context).translate('days_remaining_suffix')}"
                      : "${AppLocalizations.of(context).translate('expired_label')}${s['subscription_end']}",
                  style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                      color: active ? AppColors.success : AppColors.danger),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _statCard(String label, dynamic value, IconData icon, {Color? color}) {
    return SizedBox(
      width: 158,
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Icon(icon, size: 18, color: color ?? AppColors.primary),
                  const SizedBox(width: 6),
                  Expanded(
                    child: Text(label,
                        maxLines: 1, overflow: TextOverflow.ellipsis,
                        style: const TextStyle(fontSize: 11, color: AppColors.textSecondary)),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                (value ?? '-').toString(),
                maxLines: 1, overflow: TextOverflow.ellipsis,
                style: TextStyle(fontSize: 19, fontWeight: FontWeight.bold, color: color ?? AppColors.textPrimary),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _recentCard(Map<String, dynamic> d) {
    final registrations = (d['recent_registrations'] as List<dynamic>? ?? []);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(AppLocalizations.of(context).translate('recent_registrations'),
                style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold,
                    color: AppColors.textSecondary, letterSpacing: 1)),
            const SizedBox(height: 8),
            if (registrations.isEmpty)
              Text(AppLocalizations.of(context).translate('no_shops_registered'),
                  style: TextStyle(color: AppColors.textSecondary))
            else
              ...registrations.map<Widget>((r) {
                return ListTile(
                  contentPadding: EdgeInsets.zero,
                  dense: true,
                  leading: const Icon(Icons.store, size: 20, color: AppColors.primary),
                  title: Text('${r['shop'] ?? '-'}', maxLines: 1, overflow: TextOverflow.ellipsis),
                  subtitle: Text('${r['email'] ?? ''} • ${r['created'] ?? ''}',
                      maxLines: 1, overflow: TextOverflow.ellipsis),
                  trailing: Text(
                    '${r['owner'] ?? ''}',
                    style: const TextStyle(fontSize: 11, color: AppColors.textSecondary),
                    overflow: TextOverflow.ellipsis,
                  ),
                );
              }),
          ],
        ),
      ),
    );
  }

  Widget _releaseCard(Map<String, dynamic> r) {
    final active = r['is_active'] == true;
    final mandatory = (r['minimum_supported_code'] ?? 0) > 1;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text("v${r['version_name'] ?? '-'}${AppLocalizations.of(context).translate('build_label')}${r['version_code'] ?? '-'}",
                      maxLines: 1, overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: (active ? AppColors.success : AppColors.textSecondary)
                        .withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    active ? 'ACTIVE' : 'INACTIVE',
                    style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 6),
            Text("${AppLocalizations.of(context).translate('platform_label')}${(r['platform'] ?? '-').toString().toUpperCase()}",
                style: const TextStyle(fontSize: 12.5)),
            Text("${AppLocalizations.of(context).translate('min_supported_build')}${r['minimum_supported_code'] ?? '-'}${mandatory ? AppLocalizations.of(context).translate('mandatory_for_older') : ''}",
                style: const TextStyle(fontSize: 12.5)),
            if ((r['checksum_sha256'] ?? '').toString().isNotEmpty)
              Text(
                "${AppLocalizations.of(context).translate('sha256_label')}${r['checksum_sha256'] ?? '-'}",
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
            const SizedBox(height: 6),
            Text("${AppLocalizations.of(context).translate('released_label')}${r['released_at'] ?? '-'}",
                style: const TextStyle(fontSize: 11, color: AppColors.textSecondary)),
            const SizedBox(height: 8),
            Text(r['release_notes'] ?? '',
                maxLines: 4, overflow: TextOverflow.ellipsis,
                style: const TextStyle(fontSize: 12.5)),
          ],
        ),
      ),
    );
  }

  Future<void> _showPublishDialog(BuildContext context) async {
    final versionCtrl = TextEditingController();
    final buildCtrl = TextEditingController();
    final minBuildCtrl = TextEditingController(text: '1');
    final notesCtrl = TextEditingController();
    final urlCtrl = TextEditingController(
      text: 'https://dukaanflow-1.onrender.com/static/apk/shopzen-release.apk',
    );
    final formKey = GlobalKey<FormState>();

    final published = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(AppLocalizations.of(context).translate('publish_release_title')),
        content: SingleChildScrollView(
          child: Form(
            key: formKey,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextFormField(
                  controller: versionCtrl,
                  decoration: InputDecoration(labelText: AppLocalizations.of(context).translate('version_name_label'), hintText: '1.1.0'),
                  validator: (v) => (v == null || v.trim().isEmpty) ? AppLocalizations.of(context).translate('required_field') : null,
                ),
                TextFormField(
                  controller: buildCtrl,
                  keyboardType: TextInputType.number,
                  decoration: InputDecoration(labelText: AppLocalizations.of(context).translate('build_number_label'), hintText: '2'),
                  validator: (v) {
                    final code = int.tryParse(v ?? '');
                    if (code == null || code < 1) return AppLocalizations.of(context).translate('positive_integer');
                    return null;
                  },
                ),
                TextFormField(
                  controller: minBuildCtrl,
                  keyboardType: TextInputType.number,
                  decoration: InputDecoration(labelText: AppLocalizations.of(context).translate('min_supported_build_label')),
                ),
                TextFormField(
                  controller: urlCtrl,
                  decoration: InputDecoration(labelText: AppLocalizations.of(context).translate('download_url_label')),
                  validator: (v) {
                    final uri = Uri.tryParse(v ?? '');
                    if (uri == null || !uri.isAbsolute) return AppLocalizations.of(context).translate('valid_url');
                    return null;
                  },
                ),
                TextFormField(
                  controller: notesCtrl,
                  decoration: InputDecoration(labelText: AppLocalizations.of(context).translate('release_notes_label')),
                  maxLines: 3,
                ),
              ],
            ),
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: Text(AppLocalizations.of(context).translate('cancel'))),
          FilledButton(onPressed: () => Navigator.pop(ctx, true), child: Text(AppLocalizations.of(context).translate('publish_btn'))),
        ],
      ),
    );

    if (published != true || !context.mounted) return;
    if (!formKey.currentState!.validate()) {
      // Re-open so the owner can fix the entered values.
      return _showPublishDialog(context);
    }

    final client = ref.read(apiClientProvider);
    try {
      await client.dio.post(
        ApiConstants.adminAppReleases,
        data: {
          'platform': 'android',
          'version_name': versionCtrl.text.trim(),
          'version_code': int.parse(buildCtrl.text.trim()),
          'minimum_supported_code': int.tryParse(minBuildCtrl.text.trim()) ?? 1,
          'release_notes': notesCtrl.text.trim(),
          'download_url': urlCtrl.text.trim(),
        },
      );
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(AppLocalizations.of(context).translate('release_published')),
              backgroundColor: AppColors.success),
        );
        ref.invalidate(adminAppReleasesProvider);
      }
    } on DioException catch (e) {
      if (mounted) {
        final detail = e.response?.data;
        final msg = (detail is Map && detail['error'] != null)
            ? detail['error'].toString()
            : AppLocalizations.of(context).translate('could_not_publish');
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(msg), backgroundColor: AppColors.danger),
        );
      }
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(AppLocalizations.of(context).translate('could_not_publish')),
              backgroundColor: AppColors.danger),
        );
      }
    }
  }
}
