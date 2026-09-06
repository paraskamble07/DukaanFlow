import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../core/constants/app_colors.dart';

class WhatsAppButton extends StatelessWidget {
  final String? url;
  final String label;
  final bool isCompact;

  const WhatsAppButton({
    super.key,
    required this.url,
    this.label = 'WhatsApp Reminder',
    this.isCompact = false,
  });

  Future<void> _launchWhatsApp(BuildContext context) async {
    if (url == null || url!.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('No phone number available for WhatsApp.')),
      );
      return;
    }
    final uri = Uri.parse(url!);
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Could not launch WhatsApp. Please check if app is installed.')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    if (isCompact) {
      return IconButton.filled(
        style: IconButton.styleFrom(backgroundColor: AppColors.whatsapp),
        onPressed: () => _launchWhatsApp(context),
        icon: const Icon(Icons.chat, color: Colors.white, size: 18),
        tooltip: label,
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
      label: Text(label, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
    );
  }
}
