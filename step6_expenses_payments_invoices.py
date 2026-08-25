import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# --- 1. EXPENSES ---
# expenses/models.py
expenses_models = """from django.db import models
from decimal import Decimal
from django.utils import timezone
from core.models import TenantModel

DEFAULT_EXPENSE_CATEGORIES = [
    'Shop Rent',
    'Electricity Bill',
    'Staff Salary',
    'Internet & Telephone',
    'Transport & Delivery',
    'Shop Maintenance & Repairs',
    'Marketing & Ads',
    'Tea & Refreshments',
    'Packaging & Bags',
    'Other Business Expenses'
]

class ExpenseCategory(TenantModel):
    name = models.CharField(max_length=100, verbose_name="Category Name")

    class Meta:
        verbose_name_plural = "Expense Categories"
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(fields=['business', 'name'], name='unique_expense_category_per_business')
        ]

    def __str__(self):
        return self.name

class Expense(TenantModel):
    PAYMENT_METHODS = [
        ('CASH', 'Cash'),
        ('UPI', 'UPI / Online'),
        ('CARD', 'Card'),
        ('BANK', 'Bank Transfer'),
    ]
    category = models.ForeignKey(ExpenseCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='expenses')
    title = models.CharField(max_length=200, verbose_name="Expense Description / Title")
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Amount (₹)")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='CASH')
    expense_date = models.DateField(default=timezone.now)
    notes = models.TextField(blank=True, null=True)
    receipt_image = models.ImageField(upload_to='expenses/', blank=True, null=True)

    class Meta:
        ordering = ['-expense_date', '-created_at']

    def __str__(self):
        return f"{self.title} - ₹{self.amount} ({self.expense_date})"
"""
with open(os.path.join(BASE_DIR, "expenses", "models.py"), "w", encoding="utf-8") as f:
    f.write(expenses_models)

# expenses/forms.py
expenses_forms = """from django import forms
from .models import Expense, ExpenseCategory

class ExpenseForm(forms.ModelForm):
    category_name = forms.CharField(
        max_length=100, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Or type new category e.g. Office Supplies'})
    )

    class Meta:
        model = Expense
        fields = ['title', 'category', 'amount', 'payment_method', 'expense_date', 'notes', 'receipt_image']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. July Shop Rent', 'required': True}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'required': True}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'expense_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional reference or notes'}),
            'receipt_image': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, business=None, **kwargs):
        super().__init__(*args, **kwargs)
        if business:
            self.fields['category'].queryset = ExpenseCategory.objects.filter(business=business)
"""
with open(os.path.join(BASE_DIR, "expenses", "forms.py"), "w", encoding="utf-8") as f:
    f.write(expenses_forms)

# expenses/views.py
expenses_views = """from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Sum, Q
from core.utils import business_required
from .models import Expense, ExpenseCategory, DEFAULT_EXPENSE_CATEGORIES
from .forms import ExpenseForm

def ensure_expense_categories(business):
    for name in DEFAULT_EXPENSE_CATEGORIES:
        ExpenseCategory.objects.get_or_create(business=business, name=name)

@business_required
def expense_list(request):
    business = request.business
    ensure_expense_categories(business)
    
    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    
    expenses = Expense.objects.filter(business=business).select_related('category')
    
    if query:
        expenses = expenses.filter(Q(title__icontains=query) | Q(notes__icontains=query))
    if category_id:
        expenses = expenses.filter(category_id=category_id)
    if start_date:
        expenses = expenses.filter(expense_date__gte=start_date)
    if end_date:
        expenses = expenses.filter(expense_date__lte=end_date)
        
    total_expenses = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    categories = ExpenseCategory.objects.filter(business=business)
    
    paginator = Paginator(expenses, 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    return render(request, 'expenses/expense_list.html', {
        'page_obj': page_obj,
        'categories': categories,
        'total_expenses': total_expenses,
        'query': query,
        'selected_category': category_id,
        'start_date': start_date,
        'end_date': end_date,
    })

@business_required
def expense_create(request):
    business = request.business
    ensure_expense_categories(business)
    
    if request.method == 'POST':
        form = ExpenseForm(request.POST, request.FILES, business=business)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.business = business
            cat_name = form.cleaned_data.get('category_name')
            if cat_name:
                cat_obj, _ = ExpenseCategory.objects.get_or_create(business=business, name=cat_name.strip())
                expense.category = cat_obj
            expense.save()
            messages.success(request, f"Expense '{expense.title}' of ₹{expense.amount} recorded!")
            return redirect('expenses:list')
    else:
        form = ExpenseForm(business=business)
        
    return render(request, 'expenses/expense_form.html', {'form': form, 'title': 'Add New Expense'})

@business_required
def expense_delete(request, pk):
    expense = get_object_or_404(Expense, pk=pk, business=request.business)
    if request.method == 'POST':
        title = expense.title
        expense.delete()
        messages.success(request, f"Expense '{title}' deleted.")
        return redirect('expenses:list')
    return render(request, 'expenses/expense_confirm_delete.html', {'expense': expense})
"""
with open(os.path.join(BASE_DIR, "expenses", "views.py"), "w", encoding="utf-8") as f:
    f.write(expenses_views)

# expenses/urls.py
expenses_urls = """from django.urls import path
from . import views

app_name = 'expenses'

urlpatterns = [
    path('', views.expense_list, name='list'),
    path('add/', views.expense_create, name='create'),
    path('<int:pk>/delete/', views.expense_delete, name='delete'),
]
"""
with open(os.path.join(BASE_DIR, "expenses", "urls.py"), "w", encoding="utf-8") as f:
    f.write(expenses_urls)

# expenses/admin.py
expenses_admin = """from django.contrib import admin
from .models import ExpenseCategory, Expense

@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'business')

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'amount', 'payment_method', 'expense_date', 'business')
    list_filter = ('category', 'payment_method', 'expense_date', 'business')
    search_fields = ('title', 'notes')
"""
with open(os.path.join(BASE_DIR, "expenses", "admin.py"), "w", encoding="utf-8") as f:
    f.write(expenses_admin)


# --- 2. PAYMENTS ---
# payments/models.py
payments_models = """from django.db import models
from decimal import Decimal
from django.utils import timezone
from core.models import TenantModel

class Payment(TenantModel):
    PAYMENT_TYPES = [
        ('CUSTOMER_PAYMENT', 'Customer Payment / Khata Inflow'),
        ('SUPPLIER_PAYMENT', 'Supplier Payment / Outflow'),
    ]
    PAYMENT_METHODS = [
        ('CASH', 'Cash'),
        ('UPI', 'UPI (GPay / PhonePe / Paytm)'),
        ('CARD', 'Card'),
        ('BANK', 'Bank Transfer / NEFT'),
        ('OTHER', 'Other'),
    ]
    payment_type = models.CharField(max_length=25, choices=PAYMENT_TYPES)
    customer = models.ForeignKey('customers.Customer', on_delete=models.CASCADE, null=True, blank=True, related_name='payments')
    supplier = models.ForeignKey('suppliers.Supplier', on_delete=models.CASCADE, null=True, blank=True, related_name='payments')
    sale = models.ForeignKey('sales.Sale', on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    purchase = models.ForeignKey('purchases.Purchase', on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Amount (₹)")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='CASH')
    payment_date = models.DateField(default=timezone.now)
    reference_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="Txn Ref / UTR / Receipt No.")
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-payment_date', '-created_at']

    def __str__(self):
        party = self.customer.name if self.customer else (self.supplier.company_name if self.supplier else "General")
        return f"{self.get_payment_type_display()}: ₹{self.amount} from/to {party}"
"""
with open(os.path.join(BASE_DIR, "payments", "models.py"), "w", encoding="utf-8") as f:
    f.write(payments_models)

# payments/forms.py
payments_forms = """from django import forms
from .models import Payment
from customers.models import Customer
from suppliers.models import Supplier

class CustomerPaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['customer', 'amount', 'payment_method', 'payment_date', 'reference_number', 'notes']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00', 'required': True}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'payment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'UPI UTR / Cheque No.'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Khata settlement notes'}),
        }

    def __init__(self, *args, business=None, **kwargs):
        super().__init__(*args, **kwargs)
        if business:
            self.fields['customer'].queryset = Customer.objects.filter(business=business)

class SupplierPaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['supplier', 'amount', 'payment_method', 'payment_date', 'reference_number', 'notes']
        widgets = {
            'supplier': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00', 'required': True}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'payment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Bank Ref / Cheque No.'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, business=None, **kwargs):
        super().__init__(*args, **kwargs)
        if business:
            self.fields['supplier'].queryset = Supplier.objects.filter(business=business)
"""
with open(os.path.join(BASE_DIR, "payments", "forms.py"), "w", encoding="utf-8") as f:
    f.write(payments_forms)

# payments/views.py
payments_views = """from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Sum, Q
from core.utils import business_required, build_whatsapp_url, format_inr
from .models import Payment
from .forms import CustomerPaymentForm, SupplierPaymentForm
from customers.models import Customer
from suppliers.models import Supplier

@business_required
def payment_list(request):
    business = request.business
    p_type = request.GET.get('type', '')
    query = request.GET.get('q', '').strip()
    
    payments = Payment.objects.filter(business=business).select_related('customer', 'supplier', 'sale')
    
    if p_type:
        payments = payments.filter(payment_type=p_type)
    if query:
        payments = payments.filter(
            Q(customer__name__icontains=query) |
            Q(customer__phone__icontains=query) |
            Q(supplier__company_name__icontains=query) |
            Q(reference_number__icontains=query)
        )
        
    total_received = Payment.objects.filter(business=business, payment_type='CUSTOMER_PAYMENT').aggregate(Sum('amount'))['amount__sum'] or 0
    total_paid_out = Payment.objects.filter(business=business, payment_type='SUPPLIER_PAYMENT').aggregate(Sum('amount'))['amount__sum'] or 0
    
    paginator = Paginator(payments, 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    return render(request, 'payments/payment_list.html', {
        'page_obj': page_obj,
        'p_type': p_type,
        'query': query,
        'total_received': total_received,
        'total_paid_out': total_paid_out,
    })

@business_required
def customer_payment_create(request):
    business = request.business
    cust_id = request.GET.get('customer')
    initial = {}
    if cust_id:
        initial['customer'] = cust_id
        
    if request.method == 'POST':
        form = CustomerPaymentForm(request.POST, business=business)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.business = business
            payment.payment_type = 'CUSTOMER_PAYMENT'
            payment.save()
            
            # Recalculate customer due
            cust = payment.customer
            rem_due = cust.get_outstanding_due()
            
            # Build WhatsApp receipt url
            wa_msg = f"Namaste {cust.name},\\n\\nWe have received your payment of *{format_inr(payment.amount)}* on {payment.payment_date}.\\nRemaining Khata Balance: *{format_inr(rem_due)}*.\\n\\nThank you for shopping at *{business.name}*!"
            wa_url = build_whatsapp_url(cust.phone, wa_msg)
            
            messages.success(request, f"Payment of ₹{payment.amount} recorded for {cust.name}!")
            return render(request, 'payments/payment_receipt_success.html', {
                'payment': payment,
                'customer': cust,
                'remaining_due': rem_due,
                'wa_url': wa_url,
            })
    else:
        form = CustomerPaymentForm(initial=initial, business=business)
        
    return render(request, 'payments/customer_payment_form.html', {'form': form})

@business_required
def supplier_payment_create(request):
    business = request.business
    sup_id = request.GET.get('supplier')
    initial = {}
    if sup_id:
        initial['supplier'] = sup_id
        
    if request.method == 'POST':
        form = SupplierPaymentForm(request.POST, business=business)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.business = business
            payment.payment_type = 'SUPPLIER_PAYMENT'
            payment.save()
            messages.success(request, f"Payment voucher of ₹{payment.amount} recorded for {payment.supplier.company_name}!")
            return redirect('suppliers:detail', pk=payment.supplier.pk)
    else:
        form = SupplierPaymentForm(initial=initial, business=business)
        
    return render(request, 'payments/supplier_payment_form.html', {'form': form})
"""
with open(os.path.join(BASE_DIR, "payments", "views.py"), "w", encoding="utf-8") as f:
    f.write(payments_views)

# payments/urls.py
payments_urls = """from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('', views.payment_list, name='list'),
    path('customer/add/', views.customer_payment_create, name='customer_add'),
    path('supplier/add/', views.supplier_payment_create, name='supplier_add'),
]
"""
with open(os.path.join(BASE_DIR, "payments", "urls.py"), "w", encoding="utf-8") as f:
    f.write(payments_urls)

# payments/admin.py
payments_admin = """from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('payment_type', 'amount', 'payment_method', 'customer', 'supplier', 'payment_date', 'business')
    list_filter = ('payment_type', 'payment_method', 'payment_date', 'business')
    search_fields = ('customer__name', 'supplier__company_name', 'reference_number')
"""
with open(os.path.join(BASE_DIR, "payments", "admin.py"), "w", encoding="utf-8") as f:
    f.write(payments_admin)


# --- 3. INVOICES & PDF SERVICE ---
# invoices/pdf_service.py
pdf_service_code = """import io
from decimal import Decimal
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, HRFlowable
from core.utils import format_inr

def generate_invoice_pdf(sale):
    \"\"\"Generates a pixel-perfect, GST-ready Indian Invoice PDF using ReportLab.\"\"\"
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=15*mm,
        bottomMargin=15*mm
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'InvoiceTitle',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0F172A'),
        fontName='Helvetica-Bold'
    )
    shop_title_style = ParagraphStyle(
        'ShopTitle',
        parent=styles['Heading2'],
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#1E293B'),
        fontName='Helvetica-Bold'
    )
    normal_style = ParagraphStyle(
        'NormalText',
        parent=styles['Normal'],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#334155')
    )
    bold_style = ParagraphStyle(
        'BoldText',
        parent=styles['Normal'],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#0F172A'),
        fontName='Helvetica-Bold'
    )
    footer_style = ParagraphStyle(
        'FooterText',
        parent=styles['Normal'],
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#64748B'),
        alignment=1
    )
    
    business = sale.business
    customer = sale.customer
    
    # Header: Business Details & Invoice Metadata
    shop_info = f"<b>{business.name}</b><br/>"
    if business.address:
        shop_info += f"{business.address}<br/>"
    if business.city or business.state:
        shop_info += f"{business.city or ''}, {business.state or ''} - {business.pincode or ''}<br/>"
    shop_info += f"Phone: {business.phone}<br/>Email: {business.email}"
    if business.gstin:
        shop_info += f"<br/><b>GSTIN: {business.gstin}</b>"
        
    inv_meta = f"<b>TAX INVOICE / BILL OF SUPPLY</b><br/>"
    inv_meta += f"<b>Invoice No:</b> {sale.invoice_number}<br/>"
    inv_meta += f"<b>Date:</b> {sale.sale_date.strftime('%d-%m-%Y %I:%M %p')}<br/>"
    inv_meta += f"<b>Payment Method:</b> {sale.get_payment_method_display()}<br/>"
    inv_meta += f"<b>Payment Status:</b> {sale.get_payment_status_display()}"
    
    header_table_data = [
        [Paragraph(shop_info, normal_style), Paragraph(inv_meta, normal_style)]
    ]
    header_table = Table(header_table_data, colWidths=[90*mm, 80*mm])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 10))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E1'), spaceAfter=10))
    
    # Customer Details
    cust_info = f"<b>BILLED TO (CUSTOMER):</b><br/>"
    cust_info += f"<b>{customer.name}</b><br/>"
    cust_info += f"Mobile: {customer.phone}<br/>"
    if customer.address:
        cust_info += f"Address: {customer.address}"
        
    elements.append(Paragraph(cust_info, normal_style))
    elements.append(Spacer(1, 12))
    
    # Line Items Table
    table_data = [
        [
            Paragraph("<b>#</b>", bold_style),
            Paragraph("<b>Item Description / Serial / IMEI</b>", bold_style),
            Paragraph("<b>Qty</b>", bold_style),
            Paragraph("<b>Rate (₹)</b>", bold_style),
            Paragraph("<b>Discount (₹)</b>", bold_style),
            Paragraph("<b>Total (₹)</b>", bold_style),
        ]
    ]
    
    items = sale.items.select_related('product')
    idx = 1
    for item in items:
        desc = f"<b>{item.product.name}</b>"
        if item.product.brand:
            desc += f" <i>({item.product.brand})</i>"
        if item.imei_numbers:
            desc += f"<br/><font color='#2563EB' size=7>{item.imei_numbers}</font>"
        if item.product.warranty_months > 0:
            desc += f"<br/><font color='#059669' size=7>Warranty: {item.product.warranty_months} Months</font>"
            
        table_data.append([
            Paragraph(str(idx), normal_style),
            Paragraph(desc, normal_style),
            Paragraph(str(item.quantity), normal_style),
            Paragraph(f"{item.unit_price:.2f}", normal_style),
            Paragraph(f"{item.discount:.2f}", normal_style),
            Paragraph(f"{item.total_price:.2f}", normal_style),
        ])
        idx += 1
        
    items_table = Table(table_data, colWidths=[10*mm, 75*mm, 15*mm, 25*mm, 22*mm, 23*mm])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F1F5F9')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 10))
    
    # Financial Summary Table
    summary_data = [
        [Paragraph("", normal_style), Paragraph("<b>Subtotal:</b>", bold_style), Paragraph(format_inr(sale.subtotal), normal_style)],
        [Paragraph("", normal_style), Paragraph("<b>Special Discount:</b>", bold_style), Paragraph(format_inr(sale.discount), normal_style)],
    ]
    if sale.tax_amount > 0:
        summary_data.append([Paragraph("", normal_style), Paragraph("<b>GST / Tax:</b>", bold_style), Paragraph(format_inr(sale.tax_amount), normal_style)])
        
    summary_data.extend([
        [Paragraph("", normal_style), Paragraph("<b>Grand Total:</b>", bold_style), Paragraph(f"<b>{format_inr(sale.total_amount)}</b>", bold_style)],
        [Paragraph("", normal_style), Paragraph("<b>Amount Paid:</b>", bold_style), Paragraph(format_inr(sale.paid_amount), normal_style)],
        [Paragraph("", normal_style), Paragraph("<b>Balance Due (Khata):</b>", bold_style), Paragraph(f"<font color='{'#DC2626' if sale.due_amount > 0 else '#059669'}'><b>{format_inr(sale.due_amount)}</b></font>", bold_style)],
    ])
    
    summary_table = Table(summary_data, colWidths=[90*mm, 45*mm, 35*mm])
    summary_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 15))
    
    # Footer & Terms
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#E2E8F0'), spaceAfter=8))
    footer_text = business.invoice_footer or "Thank you for shopping with us! Visit again."
    elements.append(Paragraph(f"<b>Terms & Conditions:</b><br/>{footer_text}", footer_style))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph("This is a computer-generated invoice from DukaanFlow POS.", footer_style))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer
"""
with open(os.path.join(BASE_DIR, "invoices", "pdf_service.py"), "w", encoding="utf-8") as f:
    f.write(pdf_service_code)

# invoices/views.py
invoices_views = """from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from core.utils import business_required, build_whatsapp_url, format_inr
from sales.models import Sale
from .pdf_service import generate_invoice_pdf

@business_required
def invoice_detail(request, pk):
    sale = get_object_or_404(Sale, pk=pk, business=request.business)
    items = sale.items.select_related('product')
    
    # Build WhatsApp Share Link
    business_name = sale.business.name
    wa_msg = f"Namaste {sale.customer.name},\\n\\nHere is your invoice *#{sale.invoice_number}* from *{business_name}*:\\n"
    wa_msg += f"Total: *{format_inr(sale.total_amount)}*\\nPaid: *{format_inr(sale.paid_amount)}*\\n"
    if sale.due_amount > 0:
        wa_msg += f"Due: *{format_inr(sale.due_amount)}*\\n"
    wa_msg += f"Date: {sale.sale_date.strftime('%d-%m-%Y')}\\n\\nThank you for shopping with us!"
    wa_url = build_whatsapp_url(sale.customer.phone, wa_msg)
    
    return render(request, 'invoices/invoice_detail.html', {
        'sale': sale,
        'items': items,
        'wa_url': wa_url,
    })

@business_required
def invoice_pdf_download(request, pk):
    sale = get_object_or_404(Sale, pk=pk, business=request.business)
    pdf_buffer = generate_invoice_pdf(sale)
    response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Invoice_{sale.invoice_number}.pdf"'
    return response

@business_required
def invoice_print(request, pk):
    sale = get_object_or_404(Sale, pk=pk, business=request.business)
    items = sale.items.select_related('product')
    return render(request, 'invoices/invoice_print.html', {
        'sale': sale,
        'items': items,
    })
"""
with open(os.path.join(BASE_DIR, "invoices", "views.py"), "w", encoding="utf-8") as f:
    f.write(invoices_views)

# invoices/urls.py
invoices_urls = """from django.urls import path
from . import views

app_name = 'invoices'

urlpatterns = [
    path('<int:pk>/', views.invoice_detail, name='detail'),
    path('<int:pk>/pdf/', views.invoice_pdf_download, name='pdf'),
    path('<int:pk>/print/', views.invoice_print, name='print'),
]
"""
with open(os.path.join(BASE_DIR, "invoices", "urls.py"), "w", encoding="utf-8") as f:
    f.write(invoices_urls)

print("Phase 6 (Expenses, Payments & Invoices) created successfully!")
