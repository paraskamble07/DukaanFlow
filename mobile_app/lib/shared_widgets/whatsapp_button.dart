import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../core/constants/app_colors.dart';
import '../core/localization/app_localizations.dart';

class WhatsAppButton extends StatelessWidget {
  final String? url;
  final String? label;
  final bool isCompact;

  const WhatsAppButton({
    super.key,
    required this.url,
    this.label,
    this.isCompact = false,
  });

  Future<void> _launchWhatsApp(BuildContext context) async {
    if (url == null || url!.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(AppLocalizations.of(context).translate('no_phone_whatsapp'))),
      );
      return;
    }
    final uri = Uri.parse(url!);
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    } else if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(AppLocalizations.of(context).translate('could_not_launch_whatsapp_app'))),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final resolvedLabel = label ?? AppLocalizations.of(context).translate('whatsapp_reminder_label');
    if (isCompact) {
      return IconButton.filled(
        style: IconButton.styleFrom(backgroundColor: AppColors.whatsapp),
        onPressed: () => _launchWhatsApp(context),
        icon: const Icon(Icons.chat, color: Colors.white, size: 18),
        tooltip: resolvedLabel,
      );
    }

    return ElevatedButton.icon(
      style: ElevatedButton.styleFrom(
        backgroundColor: AppColors.whatsapp,
        foregroundColor: Colors.white,
        elevation: 0,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      ),
      onPressed: () => _launchWhatsApp(context),
      icon: const Icon(Icons.chat, size: 18),
      label: Text(resolvedLabel, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
    );
  }
}
