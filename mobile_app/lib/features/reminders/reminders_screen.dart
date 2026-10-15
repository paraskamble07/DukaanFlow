import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../core/constants/api_constants.dart';
import '../../core/constants/app_colors.dart';
import '../../providers/auth_provider.dart';
import '../../providers/reminder_provider.dart';

/// Payment Reminders (Phase 4). Lists customers with an outstanding
/// balance, their derived due date, and lets the owner send a WhatsApp or
/// SMS reminder. The message and the outstanding amount are built by the
/// server — this screen never computes balances, and logging the reminder
/// is a separate, user-confirmed step (opening a composer is not sending).
class RemindersScreen extends ConsumerStatefulWidget {
  const RemindersScreen({super.key});

  @override
  ConsumerState<RemindersScreen> createState() => _RemindersScreenState();
}

class _RemindersScreenState extends ConsumerState<RemindersScreen> {
  final Map<int, bool> _logging = {};
  final Map<int, String> _errors = {};

  Future<void> _openWhatsApp(String url) async {
    final uri = Uri.tryParse(url);
    if (uri == null) {
      _toast('This customer has no valid WhatsApp number.');
      return;
    }
    await launchUrl(uri, mode: LaunchMode.externalApplication);
  }

  Future<void> _openSms(String phone, String body) async {
    final clean = phone.replaceAll(RegExp(r'[^\d+]'), '');
    final uri = Uri.parse('sms:$clean?body=${Uri.encodeComponent(body)}');
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri);
    } else {
      _toast('No SMS app available on this phone.');
    }
  }

  void _toast(String msg) {
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));
  }

  /// After the composer closes, confirm with the user before recording —
  /// the app cannot know whether the message was actually sent.
  Future<void> _confirmAndLog(DueCustomer c, String channel) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Log this reminder?'),
        content: Text(
          channel == 'WHATSAPP'
              ? 'WhatsApp opened with the message for ${c.name}. Record this reminder in the history?'
              : 'The SMS composer opened for ${c.name}. Record this reminder in the history?',
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('CANCEL')),
          FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('LOG REMINDER')),
        ],
      ),
    );
    if (confirmed != true) return;

    setState(() {
      _logging[c.customerId] = true;
      _errors.remove(c.customerId);
    });
    try {
      final client = ref.read(apiClientProvider);
      await client.dio.post(
        ApiConstants.remindersLog,
        data: {'customer_id': c.customerId, 'channel': channel},
      );
      _toast('Reminder logged for ${c.name}.');
      ref.invalidate(reminderHistoryProvider);
      await ref.read(reminderProvider.notifier).load();
    } catch (e) {
      final msg = _explainError(e);
      setState(() => _errors[c.customerId] = msg);
      _toast(msg);
    } finally {
      if (mounted) setState(() => _logging[c.customerId] = false);
    }
  }

  String _explainError(Object e) {
    try {
      final res = (e as dynamic).response;
      final data = res?.data;
      if (data is Map && data['error'] is String) return data['error'];
    } catch (_) {}
    return 'Could not log the reminder. Please try again.';
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(reminderProvider);
    final history = ref.watch(reminderHistoryProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Payment Reminders'),
        actions: [
          IconButton(
            tooltip: 'Refresh balances',
            icon: const Icon(Icons.refresh),
            onPressed: state.isLoading ? null : () => ref.read(reminderProvider.notifier).load(),
          ),
        ],
      ),
      body: state.isLoading
          ? const Center(child: CircularProgressIndicator())
          : state.error != null
              ? _Centered(state.error!, onRetry: () => ref.read(reminderProvider.notifier).load())
              : state.dueList.isEmpty
                  ? _Centered(
                      'All settled! No customer has an outstanding balance right now.',
                      onRetry: () => ref.read(reminderProvider.notifier).load(),
                    )
                  : ListView(
                      padding: const EdgeInsets.all(12),
                      children: [
                        Padding(
                          padding: const EdgeInsets.fromLTRB(4, 4, 4, 8),
                          child: Text(
                            'Credit period: ${state.creditDays} days · amounts are recalculated by the server',
                            style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
                          ),
                        ),
                        for (final c in state.dueList) _dueCard(c),
                        const SizedBox(height: 20),
                        const _SectionTitle('REMINDER HISTORY'),
                        history.when(
                          loading: () => const Padding(
                            padding: EdgeInsets.all(16),
                            child: Center(child: CircularProgressIndicator()),
                          ),
                          error: (_, __) => const Padding(
                            padding: EdgeInsets.all(16),
                            child: Text('Could not load history.',
                                style: TextStyle(color: AppColors.textSecondary)),
                          ),
                          data: (rows) => rows.isEmpty
                              ? const Padding(
                                  padding: EdgeInsets.all(16),
                                  child: Text('No reminders logged yet.',
                                      style: TextStyle(color: AppColors.textSecondary)),
                                )
                              : Card(
                                  child: Column(
                                    children: [
                                      for (final r in rows.take(12)) _historyRow(r),
                                    ],
                                  ),
                                ),
                        ),
                      ],
                    ),
    );
  }

  Widget _dueCard(DueCustomer c) {
    final isBusy = _logging[c.customerId] == true;
    final color = c.status == 'OVERDUE'
        ? AppColors.danger
        : c.status == 'DUE_SOON'
            ? Colors.orange
            : AppColors.success;
    final statusLabel = c.status == 'OVERDUE'
        ? 'OVERDUE'
        : c.status == 'DUE_SOON'
            ? 'DUE SOON'
            : 'DUE';
    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(c.name,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: color.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(statusLabel,
                      style: TextStyle(
                          fontSize: 10.5, fontWeight: FontWeight.bold, color: color)),
                ),
              ],
            ),
            const SizedBox(height: 6),
            Row(
              children: [
                const Icon(Icons.currency_rupee_rounded, size: 15, color: AppColors.primary),
                Text(c.outstanding,
                    style: const TextStyle(
                        fontWeight: FontWeight.bold, fontSize: 16, color: AppColors.primary)),
                const SizedBox(width: 12),
                Icon(Icons.event_rounded, size: 15, color: AppColors.textSecondary),
                const SizedBox(width: 4),
                Text(
                  c.dueDate != null
                      ? 'Due ${_formatDate(c.dueDate!)}'
                      : 'No credit sale date',
                  style: const TextStyle(fontSize: 12.5, color: AppColors.textSecondary),
                ),
              ],
            ),
            if (c.reminderCount > 0) ...[
              const SizedBox(height: 4),
              Text(
                "${c.reminderCount} reminder(s) sent"
                "${c.lastAt != null ? ' · last ${_formatDateTime(c.lastAt!)}' : ''}",
                style: const TextStyle(fontSize: 11.5, color: AppColors.textSecondary),
              ),
            ],
            if (_errors[c.customerId] != null)
              Padding(
                padding: const EdgeInsets.only(top: 6),
                child: Text(_errors[c.customerId]!,
                    style: const TextStyle(fontSize: 12, color: AppColors.danger)),
              ),
            const SizedBox(height: 10),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: c.whatsappUrl.isEmpty || isBusy
                        ? null
                        : () => _openWhatsApp(c.whatsappUrl).then((_) {
                              // Give the composer a beat, then confirm.
                              Future.delayed(const Duration(milliseconds: 400), () {
                                if (mounted) _confirmAndLog(c, 'WHATSAPP');
                              });
                            }),
                    icon: const Icon(Icons.chat_rounded, size: 18),
                    label: const Text('WhatsApp'),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: c.phone.isEmpty || isBusy
                        ? null
                        : () => _openSms(c.phone, c.smsBody).then((_) {
                              Future.delayed(const Duration(milliseconds: 400), () {
                                if (mounted) _confirmAndLog(c, 'SMS');
                              });
                            }),
                    icon: const Icon(Icons.sms_rounded, size: 18),
                    label: const Text('SMS'),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _historyRow(Map<String, dynamic> r) {
    return ListTile(
      dense: true,
      leading: Icon(
        r['channel'] == 'WHATSAPP' ? Icons.chat_rounded : Icons.sms_rounded,
        size: 20,
        color: AppColors.primary,
      ),
      title: Text('${r['customer']} · ₹${r['amount']}',
          maxLines: 1, overflow: TextOverflow.ellipsis,
          style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
      subtitle: Text(
        "${r['channel']} · ${_formatDateTime(r['sent_at'])}${r['status'] == 'OVERDUE' ? ' · overdue' : ''}",
        style: const TextStyle(fontSize: 11.5, color: AppColors.textSecondary),
      ),
    );
  }

  String _formatDate(String iso) {
    final d = DateTime.tryParse(iso);
    return d == null ? iso : '${d.day.toString().padLeft(2, '0')}-${d.month.toString().padLeft(2, '0')}-${d.year}';
  }

  String _formatDateTime(String iso) {
    final d = DateTime.tryParse(iso)?.toLocal();
    if (d == null) return iso;
    return '${d.day.toString().padLeft(2, '0')}-${d.month.toString().padLeft(2, '0')}-${d.year} ${d.hour.toString().padLeft(2, '0')}:${d.minute.toString().padLeft(2, '0')}';
  }
}

class _SectionTitle extends StatelessWidget {
  final String text;
  const _SectionTitle(this.text);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(8, 8, 8, 8),
      child: Text(text,
          style: const TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.bold,
              color: AppColors.textSecondary,
              letterSpacing: 1)),
    );
  }
}

class _Centered extends StatelessWidget {
  final String message;
  final VoidCallback onRetry;
  const _Centered(this.message, {required this.onRetry});

  @override
  Widget build(BuildContext context) {
    return ListView(
      physics: const AlwaysScrollableScrollPhysics(),
      children: [
        const SizedBox(height: 120),
        Center(child: Text(message, textAlign: TextAlign.center,
            style: const TextStyle(color: AppColors.textSecondary))),
        const SizedBox(height: 16),
        Center(child: OutlinedButton(onPressed: onRetry, child: const Text('Refresh'))),
      ],
    );
  }
}
