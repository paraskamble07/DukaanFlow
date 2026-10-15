import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../core/constants/app_colors.dart';
import '../../models/app_update_model.dart';
import '../../providers/update_provider.dart';

/// App Update screen (Phase 21): shows the installed build, queries the
/// trusted server manifest, and offers the official download. When the
/// server flags a mandatory update the user is told plainly — the block
/// itself is enforced by the server (builds below the minimum can no
/// longer rely on older API behaviour), and this screen explains why.
class AppUpdateScreen extends ConsumerWidget {
  const AppUpdateScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final update = ref.watch(appUpdateProvider);
    final info = update.info;

    return Scaffold(
      appBar: AppBar(title: const Text('App Updates')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _InstalledCard(update: update),
          const SizedBox(height: 16),
          if (update.isChecking)
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 24),
              child: Center(child: CircularProgressIndicator()),
            )
          else if (info != null && info.updateAvailable)
            _UpdateAvailableCard(info: info)
          else if (info != null)
            const _StatusCard(
              icon: Icons.check_circle_rounded,
              color: AppColors.success,
              title: 'You are on the latest version',
              body: 'No update is available for your build of ShopZen.',
            )
          else if (update.errorMessage != null)
            _StatusCard(
              icon: Icons.cloud_off_rounded,
              color: AppColors.warning,
              title: 'Check failed',
              body: update.errorMessage!,
            )
          else
            const _StatusCard(
              icon: Icons.system_update_rounded,
              color: AppColors.info,
              title: 'Not checked yet',
              body: 'Tap "Check for updates" to look for a newer ShopZen build.',
            ),
          const SizedBox(height: 16),
          FilledButton.icon(
            onPressed: update.isChecking
                ? null
                : () => ref.read(appUpdateProvider.notifier).checkForUpdates(),
            icon: const Icon(Icons.refresh_rounded),
            label: const Text('Check for updates'),
          ),
        ],
      ),
    );
  }
}

class _InstalledCard extends StatelessWidget {
  final AppUpdateState update;
  const _InstalledCard({required this.update});

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: AppColors.primary.withValues(alpha: 0.12),
                borderRadius: BorderRadius.circular(12),
              ),
              child: const Icon(Icons.phone_android_rounded,
                  color: AppColors.primary, size: 26),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Installed ShopZen',
                    style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    update.installedVersion.isEmpty
                        ? 'Version unavailable'
                        : 'v${update.installedVersion} • build ${update.installedBuildNumber}',
                    style: const TextStyle(
                        fontSize: 13, color: AppColors.textSecondary),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _StatusCard extends StatelessWidget {
  final IconData icon;
  final Color color;
  final String title;
  final String body;
  const _StatusCard({
    required this.icon,
    required this.color,
    required this.title,
    required this.body,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      child: ListTile(
        contentPadding: const EdgeInsets.all(16),
        leading: Icon(icon, color: color, size: 30),
        title: Text(title, style: const TextStyle(fontWeight: FontWeight.bold)),
        subtitle: Padding(
          padding: const EdgeInsets.only(top: 6),
          child: Text(body,
              style: const TextStyle(
                  fontSize: 13, color: AppColors.textSecondary)),
        ),
      ),
    );
  }
}

class _UpdateAvailableCard extends StatelessWidget {
  final AppUpdateInfo info;
  const _UpdateAvailableCard({required this.info});

  @override
  Widget build(BuildContext context) {
    final mandatory = info.mandatoryUpdate;
    final hasNotes = (info.releaseNotes ?? '').isNotEmpty;
    final notes = hasNotes
        ? info.releaseNotes!
        : 'Release notes are not available for this build.';

    return Card(
      shape: RoundedRectangleBorder(
        side: BorderSide(
          color: mandatory
              ? AppColors.danger.withValues(alpha: 0.6)
              : AppColors.success.withValues(alpha: 0.5),
          width: 1.5,
        ),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  mandatory
                      ? Icons.warning_amber_rounded
                      : Icons.system_update_alt_rounded,
                  color: mandatory ? AppColors.danger : AppColors.success,
                  size: 26,
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    mandatory
                        ? 'Mandatory update required'
                        : 'A new version is available',
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 15,
                      color: mandatory ? AppColors.danger : AppColors.success,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            _MetaRow(
              label: 'Latest version',
              value: 'v${info.latestVersion} • build ${info.latestBuildNumber}',
            ),
            if (info.minimumSupportedVersion != null)
              _MetaRow(
                label: 'Minimum supported',
                value: 'v${info.minimumSupportedVersion}',
              ),
            if (info.releasedAt != null)
              _MetaRow(
                label: 'Released',
                value: '${info.releasedAt!.toLocal()}'.split('.').first,
              ),
            if ((info.checksumSha256 ?? '').isNotEmpty)
              _MetaRow(
                label: 'SHA-256',
                value: '${info.checksumSha256!.substring(0, 16)}…',
              ),
            const SizedBox(height: 12),
            const Text(
              'What’s new',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
            ),
            const SizedBox(height: 6),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppColors.backgroundDark.withValues(alpha: 0.05),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                notes,
                style: const TextStyle(fontSize: 13, height: 1.45),
              ),
            ),
            const SizedBox(height: 14),
            if (mandatory)
              const Padding(
                padding: EdgeInsets.only(bottom: 10),
                child: Text(
                  'This build is no longer supported. Please update ShopZen to keep using your shop data safely.',
                  style: TextStyle(fontSize: 12.5, color: AppColors.danger),
                ),
              ),
            if ((info.downloadUrl ?? '').isNotEmpty)
              SizedBox(
                width: double.infinity,
                child: FilledButton.icon(
                  onPressed: () => _openDownload(context, info.downloadUrl),
                  icon: const Icon(Icons.download_rounded),
                  label: const Text('Download update'),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Future<void> _openDownload(BuildContext context, String? url) async {
    final uri = Uri.tryParse(url ?? '');
    if (uri == null) return;
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    } else if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Could not open the download link.')),
      );
    }
  }
}

class _MetaRow extends StatelessWidget {
  final String label;
  final String value;
  const _MetaRow({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 130,
            child: Text(label,
                style: const TextStyle(
                    fontSize: 12.5, color: AppColors.textSecondary)),
          ),
          Expanded(
            child: Text(value,
                style: const TextStyle(fontSize: 12.5),
                overflow: TextOverflow.ellipsis,
                maxLines: 2),
          ),
        ],
      ),
    );
  }
}
