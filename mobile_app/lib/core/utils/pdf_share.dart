import 'dart:io';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';

import '../constants/api_constants.dart';
import '../network/api_client.dart';

/// Fetches the **server-generated** ledger statement PDF for a customer,
/// writes it to the app's temporary directory and returns the file.
///
/// Every rupee figure in the PDF is computed by the backend from recorded
/// invoices and payments — the client never builds or trusts its own
/// financial totals (see the master prompt's financial-integrity rule).
Future<File> downloadLedgerPdf(
  ApiClient client,
  int customerId, {
  String? name,
  DateTime? fromDate,
  DateTime? toDate,
}) async {
  final params = <String, dynamic>{};
  if (fromDate != null) params['from_date'] = _ymd(fromDate);
  if (toDate != null) params['to_date'] = _ymd(toDate);

  final res = await client.dio.get<List<int>>(
    ApiConstants.customerLedgerPdf(customerId),
    queryParameters: params,
    options: Options(responseType: ResponseType.bytes, receiveTimeout: const Duration(seconds: 30)),
  );

  if (res.statusCode != 200 || res.data == null) {
    throw Exception('Failed to generate statement (HTTP ${res.statusCode}).');
  }

  final bytes = Uint8List.fromList(res.data!);
  if (!_looksLikePdf(bytes)) {
    // The server only ever returns a PDF here (or a JSON error, which Dio
    // would have raised as a non-2xx). Guard anyway: never silently hand
    // the user a truncated or non-PDF payload.
    throw Exception('Statement download was not a valid PDF.');
  }

  final dir = await getTemporaryDirectory();
  final slug = (name ?? 'customer').replaceAll(RegExp(r'[^A-Za-z0-9_-]+'), '_');
  final file = File('${dir.path}/ledger_${slug}_$customerId.pdf');
  await file.writeAsBytes(bytes, flush: true);
  return file;
}

/// Opens the OS share sheet for the downloaded statement.
Future<void> shareLedgerPdf(File file, {String? subject}) async {
  await Share.shareXFiles(
    [XFile(file.path)],
    subject: subject ?? 'Customer ledger statement',
  );
}

bool _looksLikePdf(Uint8List bytes) {
  const header = [0x25, 0x50, 0x44, 0x46]; // %PDF
  if (bytes.length < header.length) return false;
  for (var i = 0; i < header.length; i++) {
    if (bytes[i] != header[i]) return false;
  }
  return true;
}

String _ymd(DateTime d) =>
    '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';
