import 'package:flutter_test/flutter_test.dart';

import 'package:dukaanflow/models/device_model.dart';
import 'package:dukaanflow/models/product_detail_model.dart';
import 'package:dukaanflow/models/purchase_model.dart';
import 'package:dukaanflow/models/stock_movement_model.dart';

/// Phase 11 model contracts: the app must faithfully ship what the server
/// computed — warranty state, movements, purchase history and timelines —
/// and never fall back to made-up values.
void main() {
  group('DeviceModel warranty fields', () {
    test('parses ACTIVE warranty from server payload', () {
      final device = DeviceModel.fromJson({
        'id': 1,
        'product': 5,
        'product_name': 'Galaxy A15',
        'imei_1': '356789012345601',
        'status': 'SOLD',
        'status_display': 'Sold / Dispatched',
        'purchase_price': '11000.00',
        'selling_price': '13000.00',
        'warranty_expiry_date': '2027-04-16',
        'warranty_status': 'ACTIVE',
        'warranty_days_remaining': 182,
      });
      expect(device.warrantyStatus, 'ACTIVE');
      expect(device.warrantyDaysRemaining, 182);
      expect(device.warrantyExpiryDate, '2027-04-16');
    });

    test('EXPIRED warranty carries negative days remaining', () {
      final device = DeviceModel.fromJson({
        'id': 2,
        'product': 5,
        'product_name': 'Galaxy A15',
        'imei_1': '356789012345602',
        'status': 'SOLD',
        'status_display': 'Sold / Dispatched',
        'warranty_status': 'EXPIRED',
        'warranty_days_remaining': -45,
      });
      expect(device.warrantyStatus, 'EXPIRED');
      expect(device.warrantyDaysRemaining, -45);
    });

    test('default warranty state is NO_WARRANTY for legacy payloads', () {
      final device = DeviceModel.fromJson({
        'id': 3,
        'product': 5,
        'product_name': 'Galaxy A15',
        'imei_1': '356789012345603',
        'status': 'IN_STOCK',
      });
      expect(device.warrantyStatus, 'NO_WARRANTY');
      expect(device.warrantyDaysRemaining, isNull);
    });
  });

  group('StockMovementModel', () {
    test('parses movement with linked device IMEI', () {
      final movement = StockMovementModel.fromJson({
        'id': 10,
        'product': 5,
        'product_name': 'Galaxy A15',
        'device': 1,
        'device_imei': '356789012345601',
        'movement_type': 'SALE',
        'movement_type_display': 'Sale Dispatched',
        'quantity': 1,
        'previous_stock': 1,
        'new_stock': 0,
        'notes': 'Sold to Vijay Rao (Bill #ASH-2001) — IMEI: 356789012345601',
        'reference_id': 'ASH-2001',
        'created_at': '2026-10-16T09:30:00+00:00',
      });
      expect(movement.movementType, 'SALE');
      expect(movement.deviceImei, '356789012345601');
      expect(movement.newStock, 0);
      expect(movement.referenceId, 'ASH-2001');
    });

    test('timeline entry exposes isSale', () {
      final entry = DeviceHistoryEntry.fromJson({
        'type': 'SALE',
        'type_display': 'Sale Dispatched',
        'date': '2026-10-16T09:30:00+00:00',
        'reference': 'ASH-2001',
        'note': 'Sold to Vijay Rao',
      });
      expect(entry.isSale, isTrue);
      expect(DeviceHistoryEntry.fromJson({'type': 'REGISTERED'}).isSale,
          isFalse);
    });
  });

  group('ProductDetailData', () {
    test('parses every history section from the enriched payload', () {
      final detail = ProductDetailData.fromJson({
        'id': 5,
        'name': 'Galaxy A15',
        'brand': 'Samsung',
        'purchase_price': '11000.00',
        'selling_price': '13000.00',
        'stock_quantity': 1,
        'min_stock': 2,
        'is_imei_tracked': true,
        'is_low_stock': true,
        'is_out_of_stock': false,
        'profit_margin': '18.18',
        'movements': [
          {
            'id': 10,
            'product': 5,
            'product_name': 'Galaxy A15',
            'movement_type': 'SALE',
            'movement_type_display': 'Sale Dispatched',
            'quantity': 1,
            'previous_stock': 1,
            'new_stock': 0,
            'created_at': '2026-10-16T09:30:00+00:00',
          }
        ],
        'purchase_history': [
          {
            'id': 1,
            'invoice_number': 'PO-11-1',
            'supplier_name': 'Nitin Telecom',
            'purchase_date': '2026-09-01',
            'quantity': 5,
            'unit_cost': 11000.0,
            'total_cost': 55000.0,
          }
        ],
        'devices': [
          {
            'id': 1,
            'product': 5,
            'product_name': 'Galaxy A15',
            'imei_1': '356789012345601',
            'status': 'SOLD',
            'status_display': 'Sold / Dispatched',
            'warranty_status': 'ACTIVE',
            'warranty_days_remaining': 200,
          }
        ],
        'last_sale_date': '2026-10-16T09:30:00+00:00',
        'is_dead_stock': false,
      });

      expect(detail.product.name, 'Galaxy A15');
      expect(detail.movements.length, 1);
      expect(detail.purchaseHistory.single.invoiceNumber, 'PO-11-1');
      // Amounts are taken verbatim — never recomputed client-side.
      expect(detail.purchaseHistory.single.totalCost, 55000.0);
      expect(detail.devices.single.warrantyStatus, 'ACTIVE');
      expect(detail.devices.single.warrantyDaysRemaining, 200);
      expect(detail.isDeadStock, isFalse);
      expect(detail.lastSaleDate, '2026-10-16T09:30:00+00:00');
    });

    test('empty payload yields empty sections, not failures', () {
      final detail = ProductDetailData.fromJson({
        'id': 6,
        'name': 'Legacy Bolt',
        'purchase_price': '0',
        'selling_price': '0',
        'stock_quantity': 0,
      });
      expect(detail.movements, isEmpty);
      expect(detail.purchaseHistory, isEmpty);
      expect(detail.devices, isEmpty);
      expect(detail.isDeadStock, isFalse);
    });
  });

  group('PurchaseModel', () {
    test('parses purchase with line items and due amount', () {
      final purchase = PurchaseModel.fromJson({
        'id': 7,
        'supplier': 3,
        'supplier_name': 'Nitin Telecom',
        'invoice_number': 'PO-11-1',
        'purchase_date': '2026-09-01',
        'total_amount': '55000.00',
        'paid_amount': '30000.00',
        'due_amount': '25000.00',
        'payment_method': 'CASH',
        'payment_method_display': 'Cash',
        'items': [
          {
            'id': 1,
            'product': 5,
            'product_name': 'Galaxy A15',
            'quantity': 5,
            'unit_cost': '11000.00',
            'total_cost': '55000.00',
          }
        ],
      });
      expect(purchase.invoiceNumber, 'PO-11-1');
      expect(purchase.dueAmount, 25000.0);
      expect(purchase.items.single.productName, 'Galaxy A15');
      expect(purchase.items.single.totalCost, 55000.0);
    });
  });
}
