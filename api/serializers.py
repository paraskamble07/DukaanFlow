from rest_framework import serializers
from django.contrib.auth.models import User
from decimal import Decimal
from accounts.models import UserProfile
from businesses.models import Business, PLAN_LIMITS
from customers.models import Customer
from products.models import Product, Category
from inventory.models import StockMovement, MobileDevice
from sales.models import Sale, SaleItem
from purchases.models import Purchase, PurchaseItem
from suppliers.models import Supplier
from expenses.models import Expense, ExpenseCategory
from payments.models import Payment

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['phone', 'role', 'created_at']

class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(source='userprofile', read_only=True)
    is_shopzen_admin = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'profile', 'is_shopzen_admin']

    def get_is_shopzen_admin(self, obj):
        # Navigation hint only — every admin API re-checks this server-side.
        from subscriptions.permissions import is_shopzen_admin
        return is_shopzen_admin(obj)

class BusinessSerializer(serializers.ModelSerializer):
    plan_info = serializers.SerializerMethodField()
    logo_url = serializers.SerializerMethodField()

    class Meta:
        model = Business
        fields = [
            'id', 'name', 'owner_name', 'phone', 'email', 'address',
            'city', 'state', 'pincode', 'gstin', 'logo', 'logo_url',
            'invoice_prefix', 'invoice_footer', 'plan_tier', 'plan_info',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'plan_info', 'logo_url']

    def get_plan_info(self, obj):
        return obj.get_plan_info()

    def get_logo_url(self, obj):
        if obj.logo and hasattr(obj.logo, 'url'):
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.logo.url)
            return obj.logo.url
        return None

class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'product_count']

    def get_product_count(self, obj):
        return obj.products.count()

class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    supplier_name = serializers.CharField(source='supplier.company_name', read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)
    is_out_of_stock = serializers.BooleanField(read_only=True)
    profit_margin = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'brand', 'category', 'category_name', 'sku', 'barcode',
            'purchase_price', 'selling_price', 'stock_quantity', 'min_stock',
            'warranty_months', 'is_imei_tracked', 'supplier', 'supplier_name',
            'image', 'image_url', 'description', 'is_low_stock', 'is_out_of_stock',
            'profit_margin', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_low_stock', 'is_out_of_stock', 'profit_margin', 'image_url']

    def get_profit_margin(self, obj):
        return round(obj.get_profit_margin(), 1)

    def get_image_url(self, obj):
        if obj.image and hasattr(obj.image, 'url'):
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None

class MobileDeviceSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    customer_phone = serializers.CharField(source='customer.phone', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    invoice_number = serializers.SerializerMethodField()

    class Meta:
        model = MobileDevice
        fields = [
            'id', 'product', 'product_name', 'imei_1', 'imei_2', 'serial_number',
            'model_name', 'brand', 'purchase_price', 'selling_price', 'status',
            'status_display', 'customer', 'customer_name', 'customer_phone',
            'sale_date', 'warranty_expiry_date', 'invoice_number', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'product_name', 'customer_name', 'customer_phone', 'status_display', 'invoice_number']

    def get_invoice_number(self, obj):
        if obj.sale_item and obj.sale_item.sale:
            return obj.sale_item.sale.invoice_number
        return None

class StockMovementSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    movement_type_display = serializers.CharField(source='get_movement_type_display', read_only=True)

    class Meta:
        model = StockMovement
        fields = [
            'id', 'product', 'product_name', 'movement_type', 'movement_type_display',
            'quantity', 'previous_stock', 'new_stock', 'notes', 'reference_id', 'created_at'
        ]

class CustomerSerializer(serializers.ModelSerializer):
    total_sales = serializers.SerializerMethodField()
    total_paid = serializers.SerializerMethodField()
    outstanding_due = serializers.SerializerMethodField()
    whatsapp_reminder_url = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = [
            'id', 'name', 'phone', 'email', 'address', 'notes',
            'credit_limit', 'total_sales', 'total_paid', 'outstanding_due',
            'whatsapp_reminder_url', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'total_sales', 'total_paid', 'outstanding_due', 'whatsapp_reminder_url', 'created_at', 'updated_at']

    def get_total_sales(self, obj):
        return float(obj.get_total_sales())

    def get_total_paid(self, obj):
        return float(obj.get_total_paid())

    def get_outstanding_due(self, obj):
        return float(obj.get_outstanding_due())

    def get_whatsapp_reminder_url(self, obj):
        return obj.get_whatsapp_reminder_url()

class SaleItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_brand = serializers.CharField(source='product.brand', read_only=True)
    warranty_months = serializers.IntegerField(source='product.warranty_months', read_only=True)

    class Meta:
        model = SaleItem
        fields = [
            'id', 'product', 'product_name', 'product_brand', 'quantity',
            'unit_price', 'discount', 'total_price', 'imei_numbers', 'warranty_months'
        ]

class SaleSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    customer_phone = serializers.CharField(source='customer.phone', read_only=True)
    items = SaleItemSerializer(many=True, read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    gross_profit = serializers.SerializerMethodField()

    class Meta:
        model = Sale
        fields = [
            'id', 'customer', 'customer_name', 'customer_phone', 'invoice_number',
            'subtotal', 'discount', 'tax_amount', 'total_amount', 'paid_amount',
            'due_amount', 'payment_status', 'payment_status_display', 'payment_method',
            'payment_method_display', 'sale_date', 'notes', 'items', 'gross_profit', 'created_at'
        ]
        read_only_fields = ['id', 'invoice_number', 'due_amount', 'payment_status', 'gross_profit', 'created_at']

    def get_gross_profit(self, obj):
        return float(obj.get_gross_profit())

class PurchaseItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = PurchaseItem
        fields = ['id', 'product', 'product_name', 'quantity', 'unit_cost', 'total_cost']

class PurchaseSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source='supplier.company_name', read_only=True)
    items = PurchaseItemSerializer(many=True, read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)

    class Meta:
        model = Purchase
        fields = [
            'id', 'supplier', 'supplier_name', 'invoice_number', 'purchase_date',
            'total_amount', 'paid_amount', 'due_amount', 'payment_method',
            'payment_method_display', 'notes', 'items', 'created_at'
        ]
        read_only_fields = ['id', 'due_amount', 'created_at']

class SupplierSerializer(serializers.ModelSerializer):
    total_purchases = serializers.SerializerMethodField()
    total_paid = serializers.SerializerMethodField()
    outstanding_due = serializers.SerializerMethodField()

    class Meta:
        model = Supplier
        fields = [
            'id', 'company_name', 'name', 'phone', 'email', 'address',
            'gstin', 'notes', 'total_purchases', 'total_paid', 'outstanding_due', 'created_at'
        ]
        read_only_fields = ['id', 'total_purchases', 'total_paid', 'outstanding_due', 'created_at']

    def get_total_purchases(self, obj):
        return float(obj.get_total_purchases())

    def get_total_paid(self, obj):
        return float(obj.get_total_paid())

    def get_outstanding_due(self, obj):
        return float(obj.get_outstanding_due())

class ExpenseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseCategory
        fields = ['id', 'name']

class ExpenseSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)

    class Meta:
        model = Expense
        fields = [
            'id', 'category', 'category_name', 'title', 'amount',
            'payment_method', 'payment_method_display', 'expense_date',
            'notes', 'receipt_image', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class PaymentSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    supplier_name = serializers.CharField(source='supplier.company_name', read_only=True)
    payment_type_display = serializers.CharField(source='get_payment_type_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'payment_type', 'payment_type_display', 'customer', 'customer_name',
            'supplier', 'supplier_name', 'sale', 'purchase', 'amount',
            'payment_method', 'payment_method_display', 'payment_date',
            'reference_number', 'notes', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
