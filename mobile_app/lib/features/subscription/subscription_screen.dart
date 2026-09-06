import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/constants/api_constants.dart';
import '../../core/constants/app_colors.dart';
import '../../providers/auth_provider.dart';
import '../../providers/business_provider.dart';

/// ShopZen Premium — ₹30/month, paid by UPI to the owner's QR and verified
/// manually by the ShopZen admin. Submitting a payment only creates a
/// PENDING request; Premium activates after admin approval.
class SubscriptionScreen extends ConsumerStatefulWidget {
  const SubscriptionScreen({super.key});

  @override
  ConsumerState<SubscriptionScreen> createState() => _SubscriptionScreenState();
}

class _SubscriptionScreenState extends ConsumerState<SubscriptionScreen> {
  final _utrController = TextEditingController();
  bool _submitting = false;

  @override
  void dispose() {
    _utrController.dispose();
    super.dispose();
  }

  Future<void> _submitPayment(String amount) async {
    setState(() => _submitting = true);
    final client = ref.read(apiClientProvider);
    try {
      final res = await client.dio.post(
        ApiConstants.subscriptionSubmitPayment,
        data: {
          'amount': amount,
          'upi_reference': _utrController.text.trim(),
          'note': '',
        },
      );
      if (res.statusCode == 201 && mounted) {
        await ref.refresh(myPaymentRequestsProvider.future);
        await ref.refresh(subscriptionProvider.future);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: const Text(
              'Payment submitted successfully. Your subscription is waiting for verification.',
            ),
            backgroundColor: AppColors.success,
            duration: const Duration(seconds: 4),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        String msg = 'Could not submit. Please try again.';
        if (e.toString().contains('awaiting verification')) {
          msg = 'You already have a payment request awaiting verification.';
        }
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(msg), backgroundColor: AppColors.danger),
        );
      }
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final subAsync = ref.watch(subscriptionProvider);
    final cfgAsync = ref.watch(paymentConfigProvider);
    final reqAsync = ref.watch(myPaymentRequestsProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('ShopZen Premium')),
      body: subAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, _) => Center(child: Text('Could not load subscription status: $err')),
        data: (sub) {
          final isActive = sub['is_active'] == true;
          final daysLeft = sub['days_remaining'] ?? 0;
          final features = (sub['features'] as List<dynamic>? ?? []);
          final hasPending = reqAsync.hasValue &&
              (reqAsync.value?['pending_request'] == true);

          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              _heroCard(isActive, daysLeft, sub),
              const SizedBox(height: 16),
              _statusCard(sub),
              const SizedBox(height: 16),
              if (hasPending) _pendingCard(reqAsync.value) else
                cfgAsync.when(
                  loading: () => const Card(child: Padding(
                    padding: EdgeInsets.all(24),
                    child: Center(child: CircularProgressIndicator()),
                  )),
                  error: (e, _) => const SizedBox.shrink(),
                  data: (cfg) => _payCard(cfg),
                ),
              const SizedBox(height: 16),
              const Text('EVERYTHING INCLUDED', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppColors.textSecondary, letterSpacing: 1)),
              const SizedBox(height: 8),
              Card(
                child: Padding(
                  padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 12),
                  child: Column(
                    children: features.map<Widget>((f) {
                      return Padding(
                        padding: const EdgeInsets.symmetric(vertical: 7),
                        child: Row(
                          children: [
                            const Icon(Icons.check_circle, color: AppColors.success, size: 18),
                            const SizedBox(width: 10),
                            Expanded(child: Text(f.toString(), style: const TextStyle(fontSize: 13.5))),
                          ],
                        ),
                      );
                    }).toList(),
                  ),
                ),
              ),
              const SizedBox(height: 20),
              const Text(
                'Your shop data is never deleted when the subscription expires — pay any time and everything comes back.',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 11.5, color: AppColors.textSecondary),
              ),
            ],
          );
        },
      ),
    );
  }

  Widget _heroCard(bool isActive, int daysLeft, Map<String, dynamic> sub) {
    return Card(
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(
          color: isActive ? AppColors.success : AppColors.danger,
          width: 1.5,
        ),
      ),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          children: [
            Container(
              padding: const EdgeInsets.all(14),
              decoration: const BoxDecoration(
                color: AppColors.primary,
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.workspace_premium_rounded, color: Colors.white, size: 36),
            ),
            const SizedBox(height: 14),
            const Text('Run Your Shop Smarter',
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
            const SizedBox(height: 4),
            Text(
              sub['price_display'] ?? '₹30/month',
              style: const TextStyle(fontSize: 26, fontWeight: FontWeight.bold, color: AppColors.primary),
            ),
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              decoration: BoxDecoration(
                color: (isActive ? AppColors.success : AppColors.danger).withOpacity(0.1),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(isActive ? Icons.verified : Icons.error_outline,
                      size: 18, color: isActive ? AppColors.success : AppColors.danger),
                  const SizedBox(width: 6),
                  Text(
                    isActive ? 'ACTIVE • $daysLeft days left' : 'EXPIRED',
                    style: TextStyle(
                      fontSize: 13, fontWeight: FontWeight.bold,
                      color: isActive ? AppColors.success : AppColors.danger,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _statusCard(Map<String, dynamic> sub) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            _row('Current Plan', sub['plan_name'] ?? 'ShopZen Premium'),
            _row('Start Date', sub['start_date'] ?? '-'),
            _row('Expiry Date', sub['end_date'] ?? '-'),
            _row('Payment', 'UPI — manually verified'),
          ],
        ),
      ),
    );
  }

  Widget _pendingCard(Map<String, dynamic>? reqData) {
    return Card(
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: const BorderSide(color: Colors.orange, width: 1.2),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            const Icon(Icons.hourglass_top_rounded, color: Colors.orange, size: 32),
            const SizedBox(height: 10),
            const Text('Payment Under Verification',
                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
            const SizedBox(height: 6),
            const Text(
              'We received your payment details. ShopZen will verify it and activate Premium — usually within a few hours.',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 12.5, color: AppColors.textSecondary),
            ),
            const SizedBox(height: 10),
            OutlinedButton.icon(
              onPressed: () => ref.refresh(myPaymentRequestsProvider),
              icon: const Icon(Icons.refresh, size: 16),
              label: const Text('Check Status'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _payCard(Map<String, dynamic> cfg) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('PAY ₹30 & GET PREMIUM',
                style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold,
                    color: AppColors.textSecondary, letterSpacing: 1)),
            const SizedBox(height: 12),
            Center(
              child: Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  border: Border.all(color: AppColors.primary.withOpacity(0.4), width: 2),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(8),
                  child: Image.network(
                    cfg['qr_image_url'] ?? '',
                    width: 190, height: 190, fit: BoxFit.cover,
                    errorBuilder: (_, __, ___) => Container(
                      width: 190, height: 190,
                      color: AppColors.backgroundLight,
                      alignment: Alignment.center,
                      child: const Text('QR unavailable\n(check connection)',
                          textAlign: TextAlign.center,
                          style: TextStyle(fontSize: 12, color: AppColors.textSecondary)),
                    ),
                  ),
                ),
              ),
            ),
            const SizedBox(height: 10),
            Center(
              child: Text('Scan & pay via any UPI app',
                  style: TextStyle(fontSize: 12, color: AppColors.textSecondary)),
            ),
            const SizedBox(height: 6),
            Center(
              child: Text('UPI ID: ${cfg['upi_id'] ?? '-'}',
                  style: const TextStyle(fontSize: 12.5, fontWeight: FontWeight.bold)),
            ),
            const Divider(height: 28),
            const Text('After paying, enter your UTR / reference number:',
                style: TextStyle(fontSize: 12.5)),
            const SizedBox(height: 8),
            TextField(
              controller: _utrController,
              decoration: const InputDecoration(
                hintText: 'e.g. 3045XXXXXXX21',
                prefixIcon: Icon(Icons.receipt_long),
                isDense: true,
              ),
            ),
            const SizedBox(height: 12),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: _submitting ? null : () => _submitPayment('${cfg['price'] ?? 30}'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.success,
                  minimumSize: const Size.fromHeight(48),
                ),
                icon: _submitting
                    ? const SizedBox(height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                    : const Icon(Icons.check_circle_outline),
                label: const Text('I HAVE PAID — SUBMIT',
                    style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _row(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(fontSize: 13, color: AppColors.textSecondary)),
          Text(value, style: const TextStyle(fontSize: 13.5, fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }
}
