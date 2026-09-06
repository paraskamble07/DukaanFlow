import 'package:intl/intl.dart';

class AppDateFormatter {
  static String formatDate(dynamic date) {
    if (date == null) return '-';
    DateTime? dt;
    if (date is DateTime) {
      dt = date;
    } else {
      dt = DateTime.tryParse(date.toString());
    }
    if (dt == null) return date.toString();
    return DateFormat('dd-MM-yyyy').format(dt);
  }

  static String formatDateTime(dynamic date) {
    if (date == null) return '-';
    DateTime? dt;
    if (date is DateTime) {
      dt = date;
    } else {
      dt = DateTime.tryParse(date.toString());
    }
    if (dt == null) return date.toString();
    return DateFormat('dd-MM-yyyy, hh:mm a').format(dt);
  }
}
