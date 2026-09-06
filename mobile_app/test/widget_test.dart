import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:dukaanflow/main.dart';
import 'package:dukaanflow/core/utils/currency_formatter.dart';
import 'package:dukaanflow/models/product_model.dart';
import 'package:dukaanflow/models/customer_model.dart';
import 'package:dukaanflow/models/sale_model.dart';
import 'package:dukaanflow/providers/pos_provider.dart';

void main() {
  group('CurrencyFormatter', () {
    test('formats Indian-style currency correctly', () {
      expect(CurrencyFormatter.format(18450), '₹18,450.00');
      expect(CurrencyFormatter.format(245000), '₹2,45,000.00');
      expect(CurrencyFormatter.format(0), '₹0.00');
      expect(CurrencyFormatter.format('125000'), '₹1,25,000.00');
      expect(CurrencyFormatter.format(null), '₹0.00');
    });
  });

  group('ProductModel', () {
    test('parses backend JSON payload', () {
      final product = ProductModel.fromJson({
        'id': 1,
        'name': 'iPhone 15',
        'brand': 'Apple',
        'purchase_price': '55000.00',
        'selling_price': '62000.00',
        'stock_quantity': 3,
        'min_stock': 5,
        'is_low_stock': true,
        'is_imei_tracked': true,
      });
      expect(product.name, 'iPhone 15');
      expect(product.purchasePrice, 55000.0);
      expect(product.sellingPrice, 62000.0);
      expect(product.stockQuantity, 3);
      expect(product.isLowStock, true);
    });
  });

  group('CustomerModel', () {
    test('parses khata fields from backend JSON', () {
      final customer = CustomerModel.fromJson({
        'id': 7,
        'name': 'Rahul',
        'phone': '9899001122',
        'total_sales': '35000.00',
        'total_paid': '25000.00',
        'outstanding_due': '10000.00',
        'whatsapp_reminder_url': 'https://wa.me/919899001122',
      });
      expect(customer.name, 'Rahul');
      expect(customer.totalSales, 35000.0);
      expect(customer.outstandingDue, 10000.0);
      expect(customer.whatsappReminderUrl, isNotNull);
    });
  });

  group('SaleModel', () {
    test('parses sale with items and due amount', () {
      final sale = SaleModel.fromJson({
        'id': 12,
        'customer': 7,
        'customer_name': 'Rahul',
        'invoice_number': 'SZ-1001',
        'subtotal': '20000.00',
        'total_amount': '20000.00',
        'paid_amount': '15000.00',
        'due_amount': '5000.00',
        'payment_status': 'PARTIAL',
        'payment_method': 'UPI',
        'sale_date': '2026-09-04T11:30:00',
        'items': [
          {
            'id': 1,
            'product': 3,
            'product_name': 'Redmi Note 13',
            'quantity': 1,
            'unit_price': '20000.00',
            'total_price': '20000.00',
          }
        ],
      });
      expect(sale.invoiceNumber, 'SZ-1001');
      expect(sale.dueAmount, 5000.0);
      expect(sale.items.length, 1);
      expect(sale.items.first.productName, 'Redmi Note 13');
    });
  });

  group('PosState cart math', () {
    test('computes subtotal, grand total and due correctly', () {
      final product = ProductModel(
        id: 1,
        name: 'Charger',
        purchasePrice: 300,
        sellingPrice: 500,
        stockQuantity: 10,
      );
      final state = PosState(
        items: [CartItem(product: product, quantity: 2, unitPrice: 500)],
        extraDiscount: 100,
        taxAmount: 40,
        paidAmount: 500,
      );
      expect(state.subtotal, 1000);
      expect(state.grandTotal, 940);
      expect(state.dueAmount, 440);
    });
  });

  testWidgets('ShopZen app renders splash screen', (WidgetTester tester) async {
    // The ProviderScope normally wraps ShopZenApp inside main(); widget tests
    // must provide it themselves or Riverpod consumers throw.
    await tester.pumpWidget(
      const ProviderScope(child: ShopZenApp()),
    );
    expect(find.text('ShopZen'), findsWidgets);
    expect(find.text('Smart Shop Management'), findsOneWidget);
    expect(find.text('Developed by PARAS KAMBLE'), findsOneWidget);

    // Flush the splash's 1.6s navigation timer so no Timer stays pending
    // when the test framework verifies invariants.
    await tester.pump(const Duration(seconds: 2));
  });
}
