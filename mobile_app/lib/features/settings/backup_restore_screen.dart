import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';

import '../../../core/constants/api_constants.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/localization/app_localizations.dart';
import '../../../providers/auth_provider.dart';
import '../../../providers/customer_provider.dart';
import '../../../providers/dashboard_provider.dart';
import '../../../providers/product_provider.dart';

/// Phase 8 — Backup & Restore.
///
/// Download: the shop's full dataset as server-generated JSON (every rupee
/// figure is computed by the backend; the client never trusts its own
/// totals). Restore: the file is first POSTed as a dry run so the shop
/// owner previews exactly what would be imported, then confirmed — the
/// server is the sole authority that recomputes totals, rejects
/// overpayments and skips already-present records.
class BackupRestoreScreen extends ConsumerStatefulWidget {
  const BackupRestoreScreen({super.key});

  @override
  ConsumerState<BackupRestoreScreen> createState() => _BackupRestoreScreenState();
}

class _BackupRestoreScreenState extends ConsumerState<BackupRestoreScreen> {
  bool _isDownloading = false;
  bool _isRestoring = false;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Scaffold(
      appBar: AppBar(title: Text(l10n.translate('backup_restore_title'))),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const Icon(Icons.cloud_download_outlined, color: AppColors.primary),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          l10n.translate('download_backup'),
                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(
                    l10n.translate('download_backup_desc'),
                    style: const TextStyle(fontSize: 13, color: AppColors.textSecondary),
                  ),
                  const SizedBox(height: 14),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton.icon(
                      onPressed: _isDownloading ? null : _downloadBackup,
                      icon: _isDownloading
                          ? const SizedBox(
                              height: 18, width: 18,
                              child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                          : const Icon(Icons.download),
                      label: Text(_isDownloading
                          ? l10n.translate('backup_in_progress')
                          : l10n.translate('download_backup')),
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const Icon(Icons.restore_outlined, color: AppColors.primary),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          l10n.translate('restore_backup'),
                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(
                    l10n.translate('restore_backup_desc'),
                    style: const TextStyle(fontSize: 13, color: AppColors.textSecondary),
                  ),
                  const SizedBox(height: 14),
                  SizedBox(
                    width: double.infinity,
                    child: OutlinedButton.icon(
                      onPressed: _isRestoring ? null : _pickAndRestore,
                      icon: _isRestoring
                          ? const SizedBox(
                              height: 18, width: 18,
                              child: CircularProgressIndicator(strokeWidth: 2))
                          : const Icon(Icons.file_upload_outlined),
                      label: Text(_isRestoring
                          ? l10n.translate('restore_in_progress')
                          : l10n.translate('pick_backup_file')),
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 4),
            child: Text(
              l10n.translate('backup_disclaimer'),
              style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
            ),
          ),
        ],
      ),
    );
  }

  // ------------------------------------------------------------------ //
  // Download
  // ------------------------------------------------------------------ //
  Future<void> _downloadBackup() async {
    final l10n = AppLocalizations.of(context);
    setState(() => _isDownloading = true);
    final client = ref.read(apiClientProvider);
    try {
      final res = await client.dio.get<List<int>>(
        ApiConstants.backupExport,
        options: Options(
          responseType: ResponseType.bytes,
          receiveTimeout: const Duration(seconds: 60),
        ),
      );
      if (res.statusCode != 200 || res.data == null) {
        throw Exception('HTTP ${res.statusCode}');
      }
      final bytes = Uint8List.fromList(res.data!);
      // Guard: never hand the user a payload that is not shop backup JSON.
      jsonDecode(utf8.decode(bytes));

      final disposition = res.headers.value('content-disposition') ?? '';
      final match = RegExp(r'filename="([^"]+)"').firstMatch(disposition);
      final fileName = (match?.group(1) ?? 'shopzen-backup.json')
          .replaceAll(RegExp(r'[^A-Za-z0-9._-]'), '_');

      final dir = await getApplicationDocumentsDirectory();
      final backupsDir = Directory('${dir.path}/backups')
        ..createSync(recursive: true);
      final file = File('${backupsDir.path}/$fileName');
      await file.writeAsBytes(bytes, flush: true);

      if (!mounted) return;
      await Share.shareXFiles(
        [XFile(file.path)],
        subject: l10n.translate('backup_share_subject'),
      );
      if (!mounted) return;
      _showInfo(
        l10n.translate('backup_saved_title'),
        l10n.translate('backup_saved_desc'),
      );
    } catch (e) {
      if (!mounted) return;
      _showError(
        l10n.translate('backup_download_failed'),
        _describe(e),
      );
    } finally {
      if (mounted) setState(() => _isDownloading = false);
    }
  }

  // ------------------------------------------------------------------ //
  // Restore (dry run -> preview -> confirm -> commit)
  // ------------------------------------------------------------------ //
  Future<void> _pickAndRestore() async {
    final l10n = AppLocalizations.of(context);
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['json'],
      withData: true,
    );
    if (result == null || result.files.single.bytes == null) return;

    Map<String, dynamic> backup;
    try {
      final decoded = jsonDecode(utf8.decode(result.files.single.bytes!));
      if (decoded is! Map) throw const FormatException('not an object');
      backup = Map<String, dynamic>.from(decoded);
      final meta = backup['meta'];
      if (meta is! Map || meta['backup_version'] != 1) {
        throw const FormatException('not a ShopZen backup');
      }
    } catch (_) {
      if (!mounted) return;
      _showError(l10n.translate('invalid_backup_file'), '');
      return;
    }

    setState(() => _isRestoring = true);
    final client = ref.read(apiClientProvider);
    try {
      // 1. Dry run: the server validates and previews without writing.
      final preview = await client.dio.post(
        ApiConstants.backupRestore,
        data: {...backup, 'dry_run': true},
        options: Options(receiveTimeout: const Duration(seconds: 60)),
      );
      if (preview.statusCode != 200 || preview.data is! Map) {
        throw Exception('HTTP ${preview.statusCode}');
      }
      if (!mounted) return;

      // 2. Show the owner exactly what would be imported.
      final confirmed = await showDialog<bool>(
        context: context,
        builder: (ctx) => _RestorePreviewDialog(
          report: Map<String, dynamic>.from(preview.data),
        ),
      );
      if (confirmed != true || !mounted) return;

      // 3. Commit: the server recomputes totals, skips existing records
      //    and rolls the whole import back on any validation failure.
      final commit = await client.dio.post(
        ApiConstants.backupRestore,
        data: backup,
        options: Options(receiveTimeout: const Duration(seconds: 120)),
      );
      if (commit.statusCode != 200) throw Exception('HTTP ${commit.statusCode}');
      if (!mounted) return;

      // The shop's data changed: force every cached screen to re-fetch.
      ref.invalidate(dashboardProvider);
      ref.invalidate(customerListProvider);
      ref.invalidate(productsListProvider);
      ref.invalidate(categoriesProvider);

      _showInfo(
        l10n.translate('restore_success_title'),
        l10n.translate('restore_success_desc'),
      );
    } on DioException catch (e) {
      if (!mounted) return;
      if (e.response?.statusCode == 403) {
        _showError(
          l10n.translate('backup_owner_only_title'),
          l10n.translate('backup_owner_only_desc'),
        );
      } else {
        _showError(
          l10n.translate('restore_failed_title'),
          _dioDetail(e) ?? _describe(e),
        );
      }
    } catch (e) {
      if (!mounted) return;
      _showError(l10n.translate('restore_failed_title'), _describe(e));
    } finally {
      if (mounted) setState(() => _isRestoring = false);
    }
  }

  // ------------------------------------------------------------------ //
  // Helpers
  // ------------------------------------------------------------------ //
  String? _dioDetail(DioException e) {
    final data = e.response?.data;
    if (data is Map && data['detail'] != null) {
      return data['detail'].toString();
    }
    if (data is String && data.isNotEmpty) return data;
    return null;
  }

  String _describe(Object error) {
    if (error is DioException) {
      final detail = _dioDetail(error);
      if (detail != null) return detail;
      if (error.type == DioExceptionType.connectionTimeout ||
          error.type == DioExceptionType.unknown) {
        return 'Network error';
      }
    }
    return error.toString().replaceFirst('Exception: ', '');
  }

  void _showInfo(String title, String body) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(title),
        content: Text(body),
        actions: [
          ElevatedButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: Text(AppLocalizations.of(context).translate('close')),
          ),
        ],
      ),
    );
  }

  void _showError(String title, String body) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(title),
        content: Text(body.isEmpty ? title : body),
        actions: [
          ElevatedButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: Text(AppLocalizations.of(context).translate('close')),
          ),
        ],
      ),
    );
  }
}

class _RestorePreviewDialog extends StatelessWidget {
  final Map<String, dynamic> report;

  const _RestorePreviewDialog({required this.report});

  String _countMap(Map<dynamic, dynamic> counts) {
    if (counts.isEmpty) return '0';
    return counts.entries
        .map((e) => '${e.key}: ${e.value}')
        .join(', ');
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final imported = Map<dynamic, dynamic>.from(report['imported'] as Map? ?? {});
    final skipped = Map<dynamic, dynamic>.from(report['skipped'] as Map? ?? {});
    final adjusted = Map<dynamic, dynamic>.from(report['adjusted'] as Map? ?? {});
    final warnings = (report['warnings'] as List?)?.cast<String>() ?? [];

    return AlertDialog(
      title: Text(l10n.translate('restore_preview_title')),
      content: SizedBox(
        width: double.maxFinite,
        child: ListView(
          shrinkWrap: true,
          children: [
            _kv(l10n.translate('restore_result_imported'), _countMap(imported)),
            const SizedBox(height: 6),
            _kv(l10n.translate('restore_result_skipped'), _countMap(skipped)),
            const SizedBox(height: 6),
            _kv(l10n.translate('restore_result_adjusted'), _countMap(adjusted)),
            const SizedBox(height: 12),
            Text(
              '${l10n.translate('restore_result_warnings')} (${warnings.length})',
              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
            ),
            const SizedBox(height: 6),
            if (warnings.isEmpty)
              Text(l10n.translate('restore_no_warnings'),
                  style: const TextStyle(fontSize: 12))
            else
              ...warnings.take(5).map((w) => Padding(
                    padding: const EdgeInsets.only(top: 4),
                    child: Text('• $w',
                        style: const TextStyle(fontSize: 11),
                        maxLines: 3,
                        overflow: TextOverflow.ellipsis),
                  )),
            if (warnings.length > 5)
              Padding(
                padding: const EdgeInsets.only(top: 4),
                child: Text('… ${warnings.length - 5}',
                    style: const TextStyle(fontSize: 11)),
              ),
            const SizedBox(height: 12),
            Text(
              l10n.translate('restore_confirm_content'),
              style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
            ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(false),
          child: Text(l10n.translate('cancel')),
        ),
        ElevatedButton(
          onPressed: () => Navigator.of(context).pop(true),
          child: Text(l10n.translate('ok')),
        ),
      ],
    );
  }

  Widget _kv(String label, String value) {
    return RichText(
      text: TextSpan(
        style: const TextStyle(fontSize: 12.5, color: Colors.black87),
        children: [
          TextSpan(
              text: '$label\n',
              style: const TextStyle(fontWeight: FontWeight.bold, color: AppColors.textSecondary)),
          TextSpan(text: value),
        ],
      ),
    );
  }
}
