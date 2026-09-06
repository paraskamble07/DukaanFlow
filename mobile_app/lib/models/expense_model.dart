class ExpenseModel {
  final int id;
  final int? categoryId;
  final String? categoryName;
  final String title;
  final double amount;
  final String paymentMethod;
  final String paymentMethodDisplay;
  final String expenseDate;
  final String? notes;

  ExpenseModel({
    required this.id,
    this.categoryId,
    this.categoryName,
    required this.title,
    required this.amount,
    required this.paymentMethod,
    required this.paymentMethodDisplay,
    required this.expenseDate,
    this.notes,
  });

  factory ExpenseModel.fromJson(Map<String, dynamic> json) {
    return ExpenseModel(
      id: json['id'] ?? 0,
      categoryId: json['category'],
      categoryName: json['category_name'],
      title: json['title'] ?? '',
      amount: double.tryParse(json['amount']?.toString() ?? '0') ?? 0.0,
      paymentMethod: json['payment_method'] ?? 'CASH',
      paymentMethodDisplay: json['payment_method_display'] ?? 'Cash',
      expenseDate: json['expense_date'] ?? '',
      notes: json['notes'],
    );
  }
}
