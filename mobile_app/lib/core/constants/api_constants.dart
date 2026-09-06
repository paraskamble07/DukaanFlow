class ApiConstants {
  // Backend base URL — override at build/run time without editing code:
  //   flutter run --dart-define=API_BASE_URL=http://192.168.1.5:8000
  //   flutter build apk --release --dart-define=API_BASE_URL=https://dukaanflow.onrender.com
  //
  // Options (NEVER use localhost/127.0.0.1 on a real phone — that is the phone itself):
  //   Production (Render):  https://dukaanflow.onrender.com   ← default
  //   Android emulator:      http://10.0.2.2:8000            (emulator alias for host PC)
  //   Real phone on Wi-Fi:   http://<PC-LAN-IP>:8000         (e.g. http://192.168.1.5:8000)
  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'https://dukaanflow.onrender.com',
  );
  
  // Auth
  static const String login = '/api/auth/login/';
  static const String register = '/api/auth/register/';
  static const String refreshToken = '/api/auth/refresh/';
  static const String profile = '/api/auth/profile/';
  static const String businessSettings = '/api/business/settings/';
  static const String businessPlans = '/api/business/plans/';
  
  // Dashboard
  static const String dashboard = '/api/dashboard/';
  
  // Products & Inventory
  static const String products = '/api/products/';
  static const String categories = '/api/categories/';
  static const String stockMovements = '/api/inventory/movements/';
  static const String imeiDevices = '/api/inventory/imei/';
  static const String imeiLookup = '/api/inventory/imei/lookup/';
  
  // POS Billing & Sales
  static const String posCheckout = '/api/pos/checkout/';
  static const String sales = '/api/sales/';
  
  // Customers & Khata
  static const String customers = '/api/customers/';
  static String customerLedger(int id) => '/api/customers/$id/ledger/';
  
  // Suppliers & Purchases
  static const String suppliers = '/api/suppliers/';
  static const String purchases = '/api/purchases/';
  
  // Expenses & Payments
  static const String expenses = '/api/expenses/';
  static const String expenseCategories = '/api/expenses/categories/';
  static const String payments = '/api/payments/';
  static const String customerPayment = '/api/payments/customer/';
  static const String supplierPayment = '/api/payments/supplier/';
  
  // Reports
  static const String reportProfitLoss = '/api/reports/profit-loss/';
  static const String reportSales = '/api/reports/sales/';
  static const String reportStock = '/api/reports/stock/';
  static const String reportKhata = '/api/reports/khata/';
  static const String reportExpenses = '/api/reports/expenses/';
  static const String reportGst = '/api/reports/gst/';
  static const String reportTopProducts = '/api/reports/top-products/';
  static const String reportTopCustomers = '/api/reports/top-customers/';

  // Subscription (ShopZen Premium ₹30/month — manual admin-verified payments)
  static const String subscriptionStatus = '/api/subscription/status/';
  static const String subscriptionPaymentConfig = '/api/subscription/payment-config/';
  static const String subscriptionMyRequests = '/api/subscription/requests/';
  static const String subscriptionSubmitPayment = '/api/subscription/payment-request/';

  // ShopZen Admin (backend-enforced role; the APIs reject non-admins)
  static const String adminDashboard = '/api/admin/dashboard/';
  static const String adminPaymentRequests = '/api/admin/payment-requests/';
  static String adminReviewPayment(int id) => '/api/admin/payment-requests/$id/review/';

  // Health (public)
  static const String health = '/api/health/';

  // Sales detail
  static String saleDetail(int id) => '/api/sales/$id/';
}
