import 'package:intl/intl.dart';

class CurrencyFormatter {
  static String format(dynamic amount) {
    if (amount == null) return '₹0.00';
    double value = 0.0;
    if (amount is num) {
      value = amount.toDouble();
    } else {
      value = double.tryParse(amount.toString()) ?? 0.0;
    }

    final isNegative = value < 0;
    final absVal = value.abs();
    
    // Indian Currency Format e.g. 1,25,000.00
    final format = NumberFormat.currency(
      locale: 'en_IN',
      symbol: '₹',
      decimalDigits: 2,
    );
    
    final formatted = format.format(absVal);
    return isNegative ? '-$formatted' : formatted;
  }
}
