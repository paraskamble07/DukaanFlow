from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from api.views import (
    auth_views, dashboard_views, product_views, inventory_views,
    pos_views, customer_views, supplier_views, expense_views,
    payment_views, report_views, subscription_views
)
from subscriptions import views as subscription_admin_views

app_name = 'api'

urlpatterns = [
    # Auth & Business
    path('auth/register/', auth_views.RegisterAPIView.as_view(), name='register'),
    path('auth/login/', auth_views.LoginAPIView.as_view(), name='login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/profile/', auth_views.ProfileAPIView.as_view(), name='profile'),
    path('business/settings/', auth_views.BusinessSettingsAPIView.as_view(), name='business_settings'),

    # ShopZen Premium ₹30/mo Subscription
    path('subscription/status/', subscription_views.SubscriptionStatusAPIView.as_view(), name='subscription_status'),
    path('subscription/payment-config/', subscription_admin_views.PaymentConfigAPIView.as_view(), name='subscription_payment_config'),
    path('subscription/requests/', subscription_admin_views.MySubscriptionRequestsAPIView.as_view(), name='subscription_my_requests'),
    path('subscription/payment-request/', subscription_admin_views.SubmitPaymentRequestAPIView.as_view(), name='subscription_submit_payment'),

    # ShopZen Admin (backend-enforced role)
    path('admin/dashboard/', subscription_admin_views.AdminDashboardAPIView.as_view(), name='admin_dashboard'),
    path('admin/payment-requests/', subscription_admin_views.AdminPaymentRequestsAPIView.as_view(), name='admin_payment_requests'),
    path('admin/payment-requests/<int:request_id>/review/', subscription_admin_views.AdminReviewPaymentAPIView.as_view(), name='admin_review_payment'),

    # Dashboard
    path('dashboard/', dashboard_views.DashboardAPIView.as_view(), name='dashboard'),

    # Products & Categories
    path('categories/', product_views.CategoryListCreateAPIView.as_view(), name='category_list_create'),
    path('products/', product_views.ProductListCreateAPIView.as_view(), name='product_list_create'),
    path('products/<int:pk>/', product_views.ProductDetailAPIView.as_view(), name='product_detail'),

    # Inventory & IMEI & Stock Adjustment
    path('inventory/movements/', inventory_views.StockMovementListAPIView.as_view(), name='stock_movements'),
    path('inventory/adjust/', inventory_views.StockAdjustmentAPIView.as_view(), name='stock_adjust'),
    path('inventory/imei/', inventory_views.MobileDeviceListCreateAPIView.as_view(), name='imei_list_create'),
    path('inventory/imei/lookup/', inventory_views.IMEILookupAPIView.as_view(), name='imei_lookup'),

    # POS Billing & Sales
    path('pos/checkout/', pos_views.POSCheckoutAPIView.as_view(), name='pos_checkout'),
    path('sales/', pos_views.SaleListAPIView.as_view(), name='sale_list'),
    path('sales/<int:pk>/', pos_views.SaleDetailAPIView.as_view(), name='sale_detail'),

    # Customers & Khata
    path('customers/', customer_views.CustomerListCreateAPIView.as_view(), name='customer_list_create'),
    path('customers/<int:pk>/', customer_views.CustomerDetailAPIView.as_view(), name='customer_detail'),
    path('customers/<int:pk>/ledger/', customer_views.CustomerLedgerAPIView.as_view(), name='customer_ledger'),

    # Suppliers & Purchases
    path('suppliers/', supplier_views.SupplierListCreateAPIView.as_view(), name='supplier_list_create'),
    path('suppliers/<int:pk>/', supplier_views.SupplierDetailAPIView.as_view(), name='supplier_detail'),
    path('purchases/', supplier_views.PurchaseListCreateAPIView.as_view(), name='purchase_list_create'),

    # Expenses
    path('expenses/categories/', expense_views.ExpenseCategoryListCreateAPIView.as_view(), name='expense_categories'),
    path('expenses/', expense_views.ExpenseListCreateAPIView.as_view(), name='expense_list_create'),
    path('expenses/<int:pk>/', expense_views.ExpenseDetailAPIView.as_view(), name='expense_detail'),

    # Payments
    path('payments/', payment_views.PaymentListAPIView.as_view(), name='payment_list'),
    path('payments/customer/', payment_views.CustomerPaymentCreateAPIView.as_view(), name='customer_payment'),
    path('payments/supplier/', payment_views.SupplierPaymentCreateAPIView.as_view(), name='supplier_payment'),

    # Reports
    path('reports/profit-loss/', report_views.ProfitLossReportAPIView.as_view(), name='report_profit_loss'),
    path('reports/sales/', report_views.SalesReportAPIView.as_view(), name='report_sales'),
    path('reports/stock/', report_views.StockReportAPIView.as_view(), name='report_stock'),
    path('reports/khata/', report_views.KhataReportAPIView.as_view(), name='report_khata'),
    path('reports/expenses/', report_views.ExpenseReportAPIView.as_view(), name='report_expenses'),
    path('reports/gst/', report_views.GSTReportAPIView.as_view(), name='report_gst'),
    path('reports/top-products/', report_views.TopProductsReportAPIView.as_view(), name='report_top_products'),
    path('reports/top-customers/', report_views.TopCustomersReportAPIView.as_view(), name='report_top_customers'),
]
