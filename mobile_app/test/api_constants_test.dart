import 'package:flutter_test/flutter_test.dart';
import 'package:dukaanflow/core/constants/api_constants.dart';

/// Guard: every id-substituting URL helper must inline the id.
///
/// Regression: `productDetail` and `imeiDeviceHistory` once used an escaped
/// `\$id`, which Dart renders as the *literal* text "$id" — the app then
/// requested `/api/products/$id/`, Django 404'd, and the Product Detail and
/// IMEI Device History screens broke on real phones (the defect was invisible
/// to widget tests, which never hit the network). A single assertion over the
/// whole helper set keeps this from ever shipping again.
void main() {
  group('id-substituting URL helpers inline the id', () {
    test('every helper emits the id and no literal dollar-prefixed token', () {
      final helpers = <String, String>{
        'productDetail': ApiConstants.productDetail(42),
        'productDetailMovements': ApiConstants.productDetailMovements(42),
        'imeiDeviceHistory': ApiConstants.imeiDeviceHistory(42),
        'customerLedger': ApiConstants.customerLedger(42),
        'customerLedgerPdf': ApiConstants.customerLedgerPdf(42),
        'customerUpiQr': ApiConstants.customerUpiQr(42),
        'staffDetail': ApiConstants.staffDetail(42),
        'saleDetail': ApiConstants.saleDetail(42),
      };
      helpers.forEach((name, url) {
        expect(url.contains('42'), isTrue, reason: '$name lost its id: "$url"');
        expect(url.contains(r'$id'), isFalse,
            reason: '$name kept a literal "\$id" token: "$url"');
      });
    });

    test('the helper output matches the backend route spelling', () {
      expect(ApiConstants.productDetail(7), '/api/products/7/');
      expect(ApiConstants.imeiDeviceHistory(7),
          '/api/inventory/imei/7/history/');
      expect(ApiConstants.customerLedger(7), '/api/customers/7/ledger/');
      expect(ApiConstants.staffDetail(7), '/api/staff/7/');
      expect(ApiConstants.saleDetail(7), '/api/sales/7/');
    });

    test('every route constant the app calls is non-empty', () {
      const routes = [
        ApiConstants.login,
        ApiConstants.register,
        ApiConstants.profile,
        ApiConstants.dashboard,
        ApiConstants.products,
        ApiConstants.customers,
        ApiConstants.sales,
        ApiConstants.posCheckout,
        ApiConstants.customerPayment,
        ApiConstants.staff,
        ApiConstants.notifications,
        ApiConstants.remindersDueList,
        ApiConstants.remindersLog,
        ApiConstants.remindersHistory,
        ApiConstants.health,
      ];
      for (final route in routes) {
        expect(route.startsWith('/api/'), isTrue, reason: route);
        expect(route.endsWith('/') || route.contains('?'), isTrue,
            reason: route);
      }
    });
  });
}
