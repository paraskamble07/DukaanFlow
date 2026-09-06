import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/constants/api_constants.dart';
import '../../core/constants/app_colors.dart';
import '../../providers/admin_provider.dart';
import '../../providers/auth_provider.dart';

/// ShopZen Admin Dashboard — visible only when the signed-in account is a
/// backend-authorized admin. All data comes from /api/admin/* which rejects
/// everyone else with 403, so the app UI is never the security boundary.
class AdminDashboardScreen extends ConsumerStatefulWidget {
  const AdminDashboardScreen({super.key});

  @override
  ConsumerState<AdminDashboardScreen> createState() => _AdminDashboardScreenState();
}

class _AdminDashboardScreenState extends ConsumerState<AdminDashboardScreen> {
  bool _reviewing = false;
  String? _reviewingId;
  @override
  Widget build(BuildContext context) {
    final dashAsync = ref.watch(adminDashboardProvider);
    final reqs = ref.watch(adminPaymentRequestsProvider);
    final statusFilter = ref.watch(adminPayStatusProvider);

    return DefaultTabController(
      length: 2,
      child: Scaffold(
        appBar: AppBar(
          title: const Text('ShopZen Admin'),
          actions: [
            IconButton(
              tooltip: 'Refresh',
              icon: const Icon(Icons.refresh),
              onPressed: () {
                ref.invalidate(adminDashboardProvider);
                ref.invalidate(adminPaymentRequestsProvider);
              },
            ),
          ],
          bottom: const TabBar(
            tabs: [
              Tab(icon: Icon(Icons.dashboard_outlined), text: 'Overview'),
              Tab(icon: Icon(Icons.payments_outlined), text: 'Payments'),
            ],
          ),
        ),
        body: TabBarView(
          children: [
            // ---------------- Overview ----------------
            dashAsync.when(
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (err, _) => _errView('Could not load admin stats: $err'),
              data: (d) => RefreshIndicator(
                onRefresh: () async => ref.refresh(adminDashboardProvider.future),
                child: ListView(
                  padding: const EdgeInsets.all(16),
                  children: [
                    Wrap(
                      spacing: 12,
                      runSpacing: 12,
                      children: [
                        _statCard('Total Users', d['total_users'], Icons.people_outline),
                        _statCard('Shops', d['total_shops'], Icons.storefront_outlined),
                        _statCard('Active Subs', d['active_subscriptions'], Icons.verified_outlined, color: AppColors.success),
                        _statCard('Expired', d['expired_subscriptions'], Icons.timer_off_outlined, color: AppColors.danger),
                        _statCard('Pending', d['pending_payments'], Icons.hourglass_top_outlined, color: Colors.orange),
                        _statCard('Approved', d['approved_payments'], Icons.check_circle_outline, color: AppColors.success),
                        _statCard('Rejected', d['rejected_payments'], Icons.cancel_outlined, color: AppColors.danger),
                        _statCard('Revenue', d['revenue_display'], Icons.currency_rupee, color: AppColors.success),
                      ],
                    ),
                    const SizedBox(height: 20),
                    _recentCard(d),
                  ],
                ),
              ),
            ),

            // ---------------- Payment review ----------------
            Column(
              children: [
                Padding(
                  padding: const EdgeInsets.fromLTRB(16, 12, 16, 4),
                  child: Row(
                    children: [
                      Expanded(
                        child: TextField(
                          decoration: const InputDecoration(
                            hintText: 'Search UTR / shop / email',
                            prefixIcon: Icon(Icons.search),
                            isDense: true,
                            border: OutlineInputBorder(),
                          ),
                          onSubmitted: (v) => ref.read(adminPaySearchProvider.notifier).state = v.trim(),
                        ),
                      ),
                    ],
                  ),
                ),
                SizedBox(
                  height: 42,
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                    children: [
                      for (final s in ['PENDING', 'APPROVED', 'REJECTED'])
                        ChoiceChip(
                          label: Text(s),
                          selected: statusFilter == s,
                          onSelected: (_) =>
                              ref.read(adminPayStatusProvider.notifier).state = s,
                        ),
                    ],
                  ),
                ),
                const Divider(height: 1),
                Expanded(
                  child: reqs.when(
                    loading: () => const Center(child: CircularProgressIndicator()),
                    error: (err, _) => _errView('Could not load payments: $err'),
                    data: (list) {
                      if (list.isEmpty) {
                        return ListView(
                          physics: const AlwaysScrollableScrollPhysics(),
                          children: const [
                            SizedBox(height: 120),
                            Center(child: Text('No payment requests in this view.',
                                style: TextStyle(color: AppColors.textSecondary))),
                          ],
                        );
                      }
                      return RefreshIndicator(
                        onRefresh: () async => ref.refresh(adminPaymentRequestsProvider.future),
                        child: ListView.separated(
                          padding: const EdgeInsets.all(12),
                          itemCount: list.length,
                          separatorBuilder: (_, __) => const SizedBox(height: 10),
                          itemBuilder: (_, i) => _paymentCard(list[i]),
                        ),
                      );
                    },
                  ),
                ),
              ],
            ),
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
            const Text('RECENT REGISTRATIONS',
                style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold,
                    color: AppColors.textSecondary, letterSpacing: 1)),
            const SizedBox(height: 8),
            if (registrations.isEmpty)
              const Text('No shops registered yet.',
                  style: TextStyle(color: AppColors.textSecondary))
            else
              ...registrations.map<Widget>((r) {
                return ListTile(
                  contentPadding: EdgeInsets.zero,
                  dense: true,
                  leading: const Icon(Icons.store, size: 20, color: AppColors.primary),
                  title: Text('${r['shop_name'] ?? '-'}', maxLines: 1, overflow: TextOverflow.ellipsis),
                  subtitle: Text('${r['email'] ?? ''} • ${r['date'] ?? ''}',
                      maxLines: 1, overflow: TextOverflow.ellipsis),
                  trailing: Text(
                    '${r['status'] ?? '-'}',
                    style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold),
                  ),
                );
              }),
          ],
        ),
      ),
    );
  }

  Widget _paymentCard(Map<String, dynamic> r) {
    final id = r['id'] as int;
    final isPending = r['status'] == 'PENDING';
    final busy = _reviewing && _reviewingId == id.toString();
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(r['shop_name'] ?? '-',
                      maxLines: 1, overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: (r['status'] == 'APPROVED'
                        ? AppColors.success
                        : r['status'] == 'REJECTED'
                            ? AppColors.danger
                            : Colors.orange)
                        .withOpacity(0.12),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    r['status'] ?? '-',
                    style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 6),
            Text('Owner: ${r['owner_name'] ?? '-'}', style: const TextStyle(fontSize: 12.5)),
            Text('Email: ${r['email'] ?? '-'}', style: const TextStyle(fontSize: 12.5)),
            if ((r['phone'] ?? '').toString().isNotEmpty)
              Text('Phone: ${r['phone']}', style: const TextStyle(fontSize: 12.5)),
            const SizedBox(height: 6),
            Row(
              children: [
                const Icon(Icons.currency_rupee, size: 16, color: AppColors.primary),
                Text('${r['amount_display'] ?? r['amount'] ?? '-'}',
                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: AppColors.primary)),
                const SizedBox(width: 12),
                Expanded(
                  child: Text('UTR: ${r['upi_reference'] ?? '-'}',
                      maxLines: 1, overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontSize: 12.5, fontWeight: FontWeight.bold)),
                ),
              ],
            ),
            Text('Submitted: ${r['requested_at_display'] ?? r['requested_at'] ?? '-'}',
                style: const TextStyle(fontSize: 11, color: AppColors.textSecondary)),
            if (r['status'] == 'APPROVED')
              Text('Approved: ${r['reviewed_at_display'] ?? r['reviewed_at'] ?? '-'}',
                  style: const TextStyle(fontSize: 11, color: AppColors.success)),
            if (r['status'] == 'REJECTED' && (r['rejection_reason'] ?? '').toString().isNotEmpty)
              Text('Reason: ${r['rejection_reason']}',
                  maxLines: 2, overflow: TextOverflow.ellipsis,
                  style: const TextStyle(fontSize: 11, color: AppColors.danger)),
            if (isPending) ...[
              const Divider(height: 20),
              Row(
                children: [
                  Expanded(
                    child: ElevatedButton.icon(
                      onPressed: busy ? null : () => _review(id, 'APPROVE'),
                      style: ElevatedButton.styleFrom(
                          backgroundColor: AppColors.success, foregroundColor: Colors.white),
                      icon: busy
                          ? const SizedBox(height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                          : const Icon(Icons.check, size: 18),
                      label: const Text('APPROVE'),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: busy ? null : () => _review(id, 'REJECT'),
                      style: OutlinedButton.styleFrom(foregroundColor: AppColors.danger),
                      icon: const Icon(Icons.close, size: 18),
                      label: const Text('REJECT'),
                    ),
                  ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }

  Future<void> _review(int id, String action) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(action == 'APPROVE' ? 'Approve payment?' : 'Reject payment?'),
        content: Text(action == 'APPROVE'
            ? 'Verify the UTR in your UPI app first. Approving activates Premium for this shop. This cannot be done twice.'
            : 'The shop owner will be told the payment could not be verified. They can pay and submit again.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('CANCEL')),
          FilledButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: Text(action == 'APPROVE' ? 'APPROVE' : 'REJECT'),
          ),
        ],
      ),
    );
    if (confirmed != true) return;

    setState(() {
      _reviewing = true;
      _reviewingId = id.toString();
    });
    final client = ref.read(apiClientProvider);
    try {
      final res = await client.dio.post(
        ApiConstants.adminReviewPayment(id),
        data: {'action': action},
      );
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(res.data['message'] ?? 'Done.'),
            backgroundColor: action == 'APPROVE' ? AppColors.success : AppColors.danger,
          ),
        );
        ref.invalidate(adminPaymentRequestsProvider);
        ref.invalidate(adminDashboardProvider);
      }
    } on DioException catch (e) {
      if (mounted) {
        final detail = e.response?.data;
        final msg = (detail is Map && detail['error'] != null)
            ? detail['error'].toString()
            : 'Could not complete. Please try again.';
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(msg), backgroundColor: AppColors.danger),
        );
      }
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
              content: Text('Could not complete. Please try again.'),
              backgroundColor: AppColors.danger),
        );
      }
    } finally {
      if (mounted) setState(() => _reviewing = false);
    }
  }
}
