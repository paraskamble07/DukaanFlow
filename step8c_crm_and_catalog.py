import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# --- 1. CUSTOMERS TEMPLATES ---
# templates/customers/customer_list.html
customer_list_html = """{% extends 'base.html' %}
{% load dukaan_tags %}

{% block title %}Customers & Khata — {{ current_business.name }}{% endblock %}

{% block content %}
<div class="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2">
    <div>
        <h4 class="fw-bold mb-0">Customer & Khata Ledger</h4>
        <span class="text-muted small">Total Market Udhar (Receivable): <strong class="text-danger">{{ total_market_due|inr }}</strong></span>
    </div>
    <div class="d-flex gap-2">
        {% if can_add %}
            <a href="{% url 'customers:create' %}" class="btn btn-primary fw-bold"><i class="bi bi-person-plus-fill me-1"></i> Add Customer</a>
        {% else %}
            <a href="{% url 'businesses:plans' %}" class="btn btn-warning fw-bold"><i class="bi bi-stars me-1"></i> Upgrade for More Customers ({{ current_count }}/{{ max_limit }})</a>
        {% endif %}
    </div>
</div>

<!-- Search & Filters -->
<div class="card p-3 mb-3">
    <form method="get" class="row g-2">
        <div class="col-md-6">
            <div class="input-group">
                <span class="input-group-text"><i class="bi bi-search"></i></span>
                <input type="text" name="q" class="form-control" placeholder="Search customer by name, phone or address..." value="{{ query }}">
            </div>
        </div>
        <div class="col-md-3">
            <select name="due" class="form-select">
                <option value="">All Customers</option>
                <option value="yes" {% if due_filter == 'yes' %}selected{% endif %}>Pending Due / Khata Only</option>
                <option value="cleared" {% if due_filter == 'cleared' %}selected{% endif %}>Cleared Accounts Only</option>
            </select>
        </div>
        <div class="col-md-3 d-flex gap-2">
            <button type="submit" class="btn btn-secondary flex-grow-1">Filter</button>
            <a href="{% url 'customers:list' %}" class="btn btn-outline-secondary">Reset</a>
        </div>
    </form>
</div>

<!-- Customers Table -->
<div class="card">
    <div class="table-responsive">
        <table class="table table-hover mb-0">
            <thead>
                <tr>
                    <th>Customer Name</th>
                    <th>Mobile / WhatsApp</th>
                    <th>Total Purchases</th>
                    <th>Total Paid</th>
                    <th>Balance Due (Khata)</th>
                    <th class="text-end">Actions</th>
                </tr>
            </thead>
            <tbody>
                {% for c in page_obj %}
                    <tr>
                        <td>
                            <a href="{% url 'customers:detail' c.pk %}" class="fw-bold text-dark text-decoration-none">
                                {{ c.name }}
                            </a>
                            {% if c.address %}
                                <div class="text-muted small">{{ c.address|truncatechars:30 }}</div>
                            {% endif %}
                        </td>
                        <td>
                            <span class="font-monospace">{{ c.phone }}</span>
                        </td>
                        <td class="fw-bold">{{ c.total_purchases|inr }}</td>
                        <td class="text-success fw-bold">{{ c.total_paid_amt|inr }}</td>
                        <td>
                            {% if c.due_amt > 0 %}
                                <span class="inr-badge-due">{{ c.due_amt|inr }}</span>
                            {% else %}
                                <span class="badge bg-success-subtle text-success">Cleared</span>
                            {% endif %}
                        </td>
                        <td class="text-end">
                            <div class="btn-group btn-group-sm">
                                {% if c.due_amt > 0 and c.wa_link %}
                                    <a href="{{ c.wa_link }}" target="_blank" class="btn btn-whatsapp" title="Send WhatsApp Payment Reminder">
                                        <i class="bi bi-whatsapp"></i> Remind
                                    </a>
                                {% endif %}
                                <a href="{% url 'payments:customer_add' %}?customer={{ c.pk }}" class="btn btn-outline-success" title="Record Payment">
                                    <i class="bi bi-cash"></i> Pay
                                </a>
                                <a href="{% url 'customers:detail' c.pk %}" class="btn btn-outline-secondary" title="View Ledger">
                                    <i class="bi bi-eye"></i>
                                </a>
                                <a href="{% url 'customers:update' c.pk %}" class="btn btn-outline-secondary" title="Edit Customer">
                                    <i class="bi bi-pencil"></i>
                                </a>
                            </div>
                        </td>
                    </tr>
                {% empty %}
                    <tr><td colspan="6" class="text-center py-4 text-muted">No customer records found.</td></tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    <!-- Pagination -->
    {% if page_obj.has_other_pages %}
        <div class="card-footer d-flex justify-content-between align-items-center">
            <span class="text-muted small">Showing {{ page_obj.start_index }}-{{ page_obj.end_index }} of {{ page_obj.paginator.count }}</span>
            <ul class="pagination pagination-sm mb-0">
                {% if page_obj.has_previous %}
                    <li class="page-item"><a class="page-link" href="?page={{ page_obj.previous_page_number }}&q={{ query }}&due={{ due_filter }}">Previous</a></li>
                {% endif %}
                <li class="page-item active"><span class="page-link">{{ page_obj.number }}</span></li>
                {% if page_obj.has_next %}
                    <li class="page-item"><a class="page-link" href="?page={{ page_obj.next_page_number }}&q={{ query }}&due={{ due_filter }}">Next</a></li>
                {% endif %}
            </ul>
        </div>
    {% endif %}
</div>
{% endblock %}
"""
with open(os.path.join(BASE_DIR, "templates", "customers", "customer_list.html"), "w", encoding="utf-8") as f:
    f.write(customer_list_html)

# templates/customers/customer_form.html
customer_form_html = """{% extends 'base.html' %}

{% block title %}{{ title }} — {{ current_business.name }}{% endblock %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-lg-6">
        <div class="card p-4 shadow-sm">
            <h5 class="fw-bold mb-3 border-bottom pb-2"><i class="bi bi-person-fill text-primary me-2"></i>{{ title }}</h5>
            <form method="post">
                {% csrf_token %}
                <div class="mb-3">
                    <label class="form-label small fw-bold">Customer Full Name *</label>
                    {{ form.name }}
                </div>
                <div class="row g-2 mb-3">
                    <div class="col-md-6">
                        <label class="form-label small fw-bold">Mobile / WhatsApp No. *</label>
                        {{ form.phone }}
                    </div>
                    <div class="col-md-6">
                        <label class="form-label small fw-bold">Email Address</label>
                        {{ form.email }}
                    </div>
                </div>
                <div class="mb-3">
                    <label class="form-label small fw-bold">Address / Locality</label>
                    {{ form.address }}
                </div>
                <div class="mb-3">
                    <label class="form-label small fw-bold">Credit / Khata Limit (₹)</label>
                    {{ form.credit_limit }}
                </div>
                <div class="mb-4">
                    <label class="form-label small fw-bold">Notes / Identity / Reference</label>
                    {{ form.notes }}
                </div>
                <div class="d-flex gap-2">
                    <button type="submit" class="btn btn-primary fw-bold px-4">Save Customer</button>
                    <a href="{% url 'customers:list' %}" class="btn btn-light border">Cancel</a>
                </div>
            </form>
        </div>
    </div>
</div>
{% endblock %}
"""
with open(os.path.join(BASE_DIR, "templates", "customers", "customer_form.html"), "w", encoding="utf-8") as f:
    f.write(customer_form_html)

# templates/customers/customer_detail.html
customer_detail_html = """{% extends 'base.html' %}
{% load dukaan_tags %}

{% block title %}{{ customer.name }} — Customer Ledger{% endblock %}

{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
    <div>
        <a href="{% url 'customers:list' %}" class="text-muted text-decoration-none small"><i class="bi bi-arrow-left"></i> Back to Customers</a>
        <h4 class="fw-bold mb-0 mt-1">{{ customer.name }}</h4>
        <span class="text-muted small"><i class="bi bi-telephone"></i> {{ customer.phone }} | {{ customer.address|default:"No address given" }}</span>
    </div>
    <div class="d-flex gap-2">
        {% if due > 0 and wa_reminder %}
            <a href="{{ wa_reminder }}" target="_blank" class="btn btn-whatsapp fw-bold shadow-sm">
                <i class="bi bi-whatsapp me-1"></i> WhatsApp Reminder
            </a>
        {% endif %}
        <a href="{% url 'payments:customer_add' %}?customer={{ customer.pk }}" class="btn btn-success fw-bold">
            <i class="bi bi-plus-circle me-1"></i> Receive Payment
        </a>
        <a href="{% url 'customers:update' customer.pk %}" class="btn btn-outline-secondary">
            <i class="bi bi-pencil"></i>
        </a>
    </div>
</div>

<!-- Ledger Summary Cards -->
<div class="row g-3 mb-4">
    <div class="col-md-4">
        <div class="card p-3 bg-white">
            <div class="text-muted small fw-bold text-uppercase">Total Sales Purchases</div>
            <div class="fs-4 fw-bold text-dark">{{ total_sales|inr }}</div>
        </div>
    </div>
    <div class="col-md-4">
        <div class="card p-3 bg-white">
            <div class="text-muted small fw-bold text-uppercase">Total Amount Paid</div>
            <div class="fs-4 fw-bold text-success">{{ total_paid|inr }}</div>
        </div>
    </div>
    <div class="col-md-4">
        <div class="card p-3 bg-white">
            <div class="text-muted small fw-bold text-uppercase">Current Outstanding Due (Khata)</div>
            <div class="fs-4 fw-bold {% if due > 0 %}text-danger{% else %}text-success{% endif %}">
                {{ due|inr }}
            </div>
        </div>
    </div>
</div>

<!-- Customer Transactions Timeline -->
<div class="row g-3">
    <!-- Sales History -->
    <div class="col-lg-7">
        <div class="card">
            <div class="card-header fw-bold">
                <i class="bi bi-receipt me-2"></i>Sales Orders & Bills
            </div>
            <div class="table-responsive">
                <table class="table table-hover mb-0">
                    <thead>
                        <tr>
                            <th>Invoice #</th>
                            <th>Date</th>
                            <th>Bill Total</th>
                            <th>Paid</th>
                            <th>Due</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for s in sales %}
                            <tr>
                                <td class="fw-bold text-primary">#{{ s.invoice_number }}</td>
                                <td>{{ s.sale_date|date:"d-m-Y" }}</td>
                                <td class="fw-bold">{{ s.total_amount|inr }}</td>
                                <td class="text-success">{{ s.paid_amount|inr }}</td>
                                <td>
                                    {% if s.due_amount > 0 %}
                                        <span class="inr-badge-due">{{ s.due_amount|inr }}</span>
                                    {% else %}
                                        <span class="badge bg-success">Paid</span>
                                    {% endif %}
                                </td>
                                <td>
                                    <a href="{% url 'invoices:detail' s.pk %}" class="btn btn-light btn-sm border"><i class="bi bi-eye"></i></a>
                                </td>
                            </tr>
                        {% empty %}
                            <tr><td colspan="6" class="text-center py-4 text-muted">No sales orders found for this customer.</td></tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- Payments History -->
    <div class="col-lg-5">
        <div class="card">
            <div class="card-header fw-bold">
                <i class="bi bi-cash-stack me-2"></i>Payment Receipts Received
            </div>
            <div class="table-responsive">
                <table class="table table-hover mb-0">
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Amount</th>
                            <th>Method</th>
                            <th>Ref</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for p in payments %}
                            <tr>
                                <td>{{ p.payment_date|date:"d-m-Y" }}</td>
                                <td class="fw-bold text-success">{{ p.amount|inr }}</td>
                                <td><span class="badge bg-light text-dark border">{{ p.get_payment_method_display }}</span></td>
                                <td class="small text-muted">{{ p.reference_number|default:"-" }}</td>
                            </tr>
                        {% empty %}
                            <tr><td colspan="4" class="text-center py-4 text-muted">No payment records found.</td></tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>
{% endblock %}
"""
with open(os.path.join(BASE_DIR, "templates", "customers", "customer_detail.html"), "w", encoding="utf-8") as f:
    f.write(customer_detail_html)

# templates/customers/customer_confirm_delete.html
customer_del_html = """{% extends 'base.html' %}
{% block content %}
<div class="row justify-content-center py-4">
    <div class="col-md-5">
        <div class="card p-4 text-center">
            <i class="bi bi-exclamation-triangle-fill text-danger fs-1 mb-2"></i>
            <h5 class="fw-bold">Delete Customer Record?</h5>
            <p class="text-muted">Are you sure you want to delete <strong>{{ customer.name }}</strong> ({{ customer.phone }})?</p>
            <form method="post" class="d-flex justify-content-center gap-2">
                {% csrf_token %}
                <button type="submit" class="btn btn-danger fw-bold">Yes, Delete</button>
                <a href="{% url 'customers:list' %}" class="btn btn-light border">Cancel</a>
            </form>
        </div>
    </div>
</div>
{% endblock %}
"""
with open(os.path.join(BASE_DIR, "templates", "customers", "customer_confirm_delete.html"), "w", encoding="utf-8") as f:
    f.write(customer_del_html)


# --- 2. PRODUCTS TEMPLATES ---
# templates/products/product_list.html
product_list_html = """{% extends 'base.html' %}
{% load dukaan_tags %}

{% block title %}Products & Catalog — {{ current_business.name }}{% endblock %}

{% block content %}
<div class="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2">
    <div>
        <h4 class="fw-bold mb-0">Products & Accessory Catalog</h4>
        <span class="text-muted small">Manage items, selling rates, and stock thresholds</span>
    </div>
    <div class="d-flex gap-2">
        {% if can_add %}
            <a href="{% url 'products:create' %}" class="btn btn-primary fw-bold"><i class="bi bi-plus-circle-fill me-1"></i> Add Product</a>
        {% else %}
            <a href="{% url 'businesses:plans' %}" class="btn btn-warning fw-bold"><i class="bi bi-stars me-1"></i> Upgrade for More Products ({{ current_count }}/{{ max_limit }})</a>
        {% endif %}
    </div>
</div>

<!-- Filters -->
<div class="card p-3 mb-3">
    <form method="get" class="row g-2">
        <div class="col-md-5">
            <div class="input-group">
                <span class="input-group-text"><i class="bi bi-search"></i></span>
                <input type="text" name="q" class="form-control" placeholder="Search by name, brand, SKU or barcode..." value="{{ query }}">
            </div>
        </div>
        <div class="col-md-3">
            <select name="category" class="form-select">
                <option value="">All Categories</option>
                {% for cat in categories %}
                    <option value="{{ cat.id }}" {% if selected_category == cat.id|stringformat:"i" %}selected{% endif %}>{{ cat.name }}</option>
                {% endfor %}
            </select>
        </div>
        <div class="col-md-2">
            <select name="stock" class="form-select">
                <option value="">All Stock</option>
                <option value="in_stock" {% if stock_status == 'in_stock' %}selected{% endif %}>In Stock</option>
                <option value="low" {% if stock_status == 'low' %}selected{% endif %}>Low Stock Only</option>
                <option value="out" {% if stock_status == 'out' %}selected{% endif %}>Out of Stock</option>
            </select>
        </div>
        <div class="col-md-2 d-flex gap-2">
            <button type="submit" class="btn btn-secondary flex-grow-1">Filter</button>
            <a href="{% url 'products:list' %}" class="btn btn-outline-secondary">Reset</a>
        </div>
    </form>
</div>

<!-- Products Table -->
<div class="card">
    <div class="table-responsive">
        <table class="table table-hover mb-0">
            <thead>
                <tr>
                    <th>Product Name & Brand</th>
                    <th>Category</th>
                    <th>Cost Price</th>
                    <th>Selling MRP</th>
                    <th>Current Stock</th>
                    <th>Type</th>
                    <th class="text-end">Actions</th>
                </tr>
            </thead>
            <tbody>
                {% for p in page_obj %}
                    <tr>
                        <td>
                            <a href="{% url 'products:detail' p.pk %}" class="fw-bold text-dark text-decoration-none">
                                {{ p.name }}
                            </a>
                            {% if p.brand %}
                                <div class="text-muted small">Brand: {{ p.brand }} {% if p.sku %}| SKU: {{ p.sku }}{% endif %}</div>
                            {% endif %}
                        </td>
                        <td><span class="badge bg-light text-dark border">{{ p.category.name|default:"General" }}</span></td>
                        <td class="text-muted">{{ p.purchase_price|inr }}</td>
                        <td class="fw-bold text-primary">{{ p.selling_price|inr }}</td>
                        <td>
                            {% if p.is_out_of_stock %}
                                <span class="badge bg-danger">0 (Out of Stock)</span>
                            {% elif p.is_low_stock %}
                                <span class="badge bg-warning text-dark">{{ p.stock_quantity }} (Low Stock)</span>
                            {% else %}
                                <span class="badge bg-success-subtle text-success fw-bold">{{ p.stock_quantity }} in stock</span>
                            {% endif %}
                        </td>
                        <td>
                            {% if p.is_imei_tracked %}
                                <span class="badge bg-info-subtle text-info"><i class="bi bi-upc-scan me-1"></i>IMEI Phone</span>
                            {% else %}
                                <span class="text-muted small">Accessory</span>
                            {% endif %}
                        </td>
                        <td class="text-end">
                            <div class="btn-group btn-group-sm">
                                <a href="{% url 'products:detail' p.pk %}" class="btn btn-outline-secondary"><i class="bi bi-eye"></i></a>
                                <a href="{% url 'products:update' p.pk %}" class="btn btn-outline-secondary"><i class="bi bi-pencil"></i></a>
                            </div>
                        </td>
                    </tr>
                {% empty %}
                    <tr><td colspan="7" class="text-center py-4 text-muted">No products registered yet. Click <strong>Add Product</strong> to populate catalog.</td></tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    <!-- Pagination -->
    {% if page_obj.has_other_pages %}
        <div class="card-footer d-flex justify-content-between align-items-center">
            <span class="text-muted small">Showing {{ page_obj.start_index }}-{{ page_obj.end_index }} of {{ page_obj.paginator.count }}</span>
            <ul class="pagination pagination-sm mb-0">
                {% if page_obj.has_previous %}
                    <li class="page-item"><a class="page-link" href="?page={{ page_obj.previous_page_number }}&q={{ query }}&category={{ selected_category }}&stock={{ stock_status }}">Previous</a></li>
                {% endif %}
                <li class="page-item active"><span class="page-link">{{ page_obj.number }}</span></li>
                {% if page_obj.has_next %}
                    <li class="page-item"><a class="page-link" href="?page={{ page_obj.next_page_number }}&q={{ query }}&category={{ selected_category }}&stock={{ stock_status }}">Next</a></li>
                {% endif %}
            </ul>
        </div>
    {% endif %}
</div>
{% endblock %}
"""
with open(os.path.join(BASE_DIR, "templates", "products", "product_list.html"), "w", encoding="utf-8") as f:
    f.write(product_list_html)

# templates/products/product_form.html
product_form_html = """{% extends 'base.html' %}

{% block title %}{{ title }} — {{ current_business.name }}{% endblock %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-lg-8">
        <div class="card p-4 shadow-sm">
            <h5 class="fw-bold mb-3 border-bottom pb-2"><i class="bi bi-box-seam text-primary me-2"></i>{{ title }}</h5>
            <form method="post" enctype="multipart/form-data">
                {% csrf_token %}
                <div class="row g-3 mb-3">
                    <div class="col-md-8">
                        <label class="form-label small fw-bold">Product / Model Name *</label>
                        {{ form.name }}
                    </div>
                    <div class="col-md-4">
                        <label class="form-label small fw-bold">Brand / Company</label>
                        {{ form.brand }}
                    </div>
                </div>

                <div class="row g-3 mb-3">
                    <div class="col-md-6">
                        <label class="form-label small fw-bold">Category</label>
                        {{ form.category }}
                    </div>
                    <div class="col-md-6">
                        <label class="form-label small fw-bold">Or New Category Name</label>
                        {{ form.category_name }}
                    </div>
                </div>

                <div class="row g-3 mb-3">
                    <div class="col-md-6">
                        <label class="form-label small fw-bold">Cost Price / Purchase (₹) *</label>
                        {{ form.purchase_price }}
                    </div>
                    <div class="col-md-6">
                        <label class="form-label small fw-bold">Selling Price / MRP (₹) *</label>
                        {{ form.selling_price }}
                    </div>
                </div>

                <div class="row g-3 mb-3">
                    <div class="col-md-4">
                        <label class="form-label small fw-bold">Current Stock Quantity *</label>
                        {{ form.stock_quantity }}
                    </div>
                    <div class="col-md-4">
                        <label class="form-label small fw-bold">Low Stock Alert Level</label>
                        {{ form.min_stock }}
                    </div>
                    <div class="col-md-4">
                        <label class="form-label small fw-bold">Warranty (Months)</label>
                        {{ form.warranty_months }}
                    </div>
                </div>

                <div class="p-3 bg-light rounded border mb-3">
                    <div class="form-check form-switch">
                        {{ form.is_imei_tracked }}
                        <label class="form-check-label fw-bold" for="{{ form.is_imei_tracked.id_for_label }}">
                            Enable IMEI / Serial Number Tracking (For Mobile Phones & Laptops)
                        </label>
                    </div>
                    <div class="text-muted small mt-1">If enabled, you can attach specific 15-digit IMEI serial numbers for warranty & search.</div>
                </div>

                <div class="row g-3 mb-3">
                    <div class="col-md-6">
                        <label class="form-label small fw-bold">SKU Code</label>
                        {{ form.sku }}
                    </div>
                    <div class="col-md-6">
                        <label class="form-label small fw-bold">Barcode / EAN</label>
                        {{ form.barcode }}
                    </div>
                </div>

                <div class="mb-3">
                    <label class="form-label small fw-bold">Preferred Supplier</label>
                    {{ form.supplier }}
                </div>

                <div class="mb-4">
                    <label class="form-label small fw-bold">Description / Technical Specs</label>
                    {{ form.description }}
                </div>

                <div class="d-flex gap-2">
                    <button type="submit" class="btn btn-primary fw-bold px-4">Save Product</button>
                    <a href="{% url 'products:list' %}" class="btn btn-light border">Cancel</a>
                </div>
            </form>
        </div>
    </div>
</div>
{% endblock %}
"""
with open(os.path.join(BASE_DIR, "templates", "products", "product_form.html"), "w", encoding="utf-8") as f:
    f.write(product_form_html)

# templates/products/product_detail.html
product_detail_html = """{% extends 'base.html' %}
{% load dukaan_tags %}

{% block title %}{{ product.name }} — Product Details{% endblock %}

{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
    <div>
        <a href="{% url 'products:list' %}" class="text-muted text-decoration-none small"><i class="bi bi-arrow-left"></i> Back to Products</a>
        <h4 class="fw-bold mb-0 mt-1">{{ product.name }}</h4>
        <span class="text-muted small">Brand: {{ product.brand|default:"Unbranded" }} | Category: {{ product.category.name|default:"General" }}</span>
    </div>
    <div class="d-flex gap-2">
        <a href="{% url 'products:update' product.pk %}" class="btn btn-primary fw-bold"><i class="bi bi-pencil me-1"></i> Edit Product</a>
    </div>
</div>

<div class="row g-3 mb-4">
    <div class="col-md-3">
        <div class="card p-3">
            <div class="text-muted small fw-bold text-uppercase">Selling Price / MRP</div>
            <div class="fs-4 fw-bold text-primary">{{ product.selling_price|inr }}</div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card p-3">
            <div class="text-muted small fw-bold text-uppercase">Purchase Cost</div>
            <div class="fs-4 fw-bold text-secondary">{{ product.purchase_price|inr }}</div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card p-3">
            <div class="text-muted small fw-bold text-uppercase">Available Stock</div>
            <div class="fs-4 fw-bold {% if product.is_out_of_stock %}text-danger{% elif product.is_low_stock %}text-warning{% else %}text-success{% endif %}">
                {{ product.stock_quantity }} units
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card p-3">
            <div class="text-muted small fw-bold text-uppercase">Profit Margin</div>
            <div class="fs-4 fw-bold text-success">{{ product.get_profit_margin|floatformat:1 }}%</div>
        </div>
    </div>
</div>

<div class="row g-3">
    <!-- Stock Movements Log -->
    <div class="col-lg-6">
        <div class="card">
            <div class="card-header fw-bold"><i class="bi bi-arrow-left-right me-2"></i>Stock Movement History</div>
            <div class="table-responsive">
                <table class="table table-hover mb-0">
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Type</th>
                            <th>Qty</th>
                            <th>Prev &rarr; New</th>
                            <th>Notes</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for sm in stock_movements %}
                            <tr>
                                <td class="small">{{ sm.created_at|date:"d-m-Y H:i" }}</td>
                                <td><span class="badge bg-light text-dark border">{{ sm.get_movement_type_display }}</span></td>
                                <td class="fw-bold">{{ sm.quantity }}</td>
                                <td class="small">{{ sm.previous_stock }} &rarr; {{ sm.new_stock }}</td>
                                <td class="small text-muted">{{ sm.notes|default:"-" }}</td>
                            </tr>
                        {% empty %}
                            <tr><td colspan="5" class="text-center py-3 text-muted">No stock movements logged.</td></tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- IMEI Serial Numbers if Tracked -->
    <div class="col-lg-6">
        <div class="card">
            <div class="card-header d-flex justify-content-between align-items-center">
                <span class="fw-bold"><i class="bi bi-upc-scan me-2"></i>Tracked Devices & IMEIs</span>
                {% if product.is_imei_tracked %}
                    <a href="{% url 'inventory:imei_create' %}" class="btn btn-outline-primary btn-sm">Add IMEI</a>
                {% endif %}
            </div>
            <div class="table-responsive">
                <table class="table table-hover mb-0">
                    <thead>
                        <tr>
                            <th>IMEI 1</th>
                            <th>Status</th>
                            <th>Customer</th>
                            <th>Warranty Exp.</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for dev in imei_devices %}
                            <tr>
                                <td class="font-monospace fw-bold">{{ dev.imei_1 }}</td>
                                <td>
                                    {% if dev.status == 'IN_STOCK' %}
                                        <span class="badge bg-success">In Stock</span>
                                    {% elif dev.status == 'SOLD' %}
                                        <span class="badge bg-secondary">Sold</span>
                                    {% else %}
                                        <span class="badge bg-warning">{{ dev.status }}</span>
                                    {% endif %}
                                </td>
                                <td>{{ dev.customer.name|default:"-" }}</td>
                                <td class="small">{{ dev.warranty_expiry_date|date:"d-m-Y"|default:"-" }}</td>
                            </tr>
                        {% empty %}
                            <tr><td colspan="4" class="text-center py-3 text-muted">{% if product.is_imei_tracked %}No serial devices attached yet.{% else %}IMEI tracking is disabled for this product.{% endif %}</td></tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>
{% endblock %}
"""
with open(os.path.join(BASE_DIR, "templates", "products", "product_detail.html"), "w", encoding="utf-8") as f:
    f.write(product_detail_html)

# templates/products/product_confirm_delete.html
product_del_html = """{% extends 'base.html' %}
{% block content %}
<div class="row justify-content-center py-4">
    <div class="col-md-5">
        <div class="card p-4 text-center">
            <i class="bi bi-exclamation-triangle-fill text-danger fs-1 mb-2"></i>
            <h5 class="fw-bold">Delete Product?</h5>
            <p class="text-muted">Are you sure you want to remove <strong>{{ product.name }}</strong> from catalog?</p>
            <form method="post" class="d-flex justify-content-center gap-2">
                {% csrf_token %}
                <button type="submit" class="btn btn-danger fw-bold">Yes, Delete</button>
                <a href="{% url 'products:list' %}" class="btn btn-light border">Cancel</a>
            </form>
        </div>
    </div>
</div>
{% endblock %}
"""
with open(os.path.join(BASE_DIR, "templates", "products", "product_confirm_delete.html"), "w", encoding="utf-8") as f:
    f.write(product_del_html)


# --- 3. INVENTORY & IMEI TEMPLATES ---
# templates/inventory/stock_list.html
stock_list_html = """{% extends 'base.html' %}
{% load dukaan_tags %}

{% block title %}Inventory & Stock Valuation — {{ current_business.name }}{% endblock %}

{% block content %}
<div class="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2">
    <div>
        <h4 class="fw-bold mb-0">Inventory Stock & Valuation</h4>
        <span class="text-muted small">Realtime stock valuation and movement audit</span>
    </div>
    <div class="d-flex gap-2">
        <a href="{% url 'reports:inventory' %}?export=csv" class="btn btn-outline-secondary"><i class="bi bi-download me-1"></i> Export CSV</a>
    </div>
</div>

<div class="row g-3 mb-4">
    <div class="col-md-3">
        <div class="card p-3">
            <div class="text-muted small fw-bold text-uppercase">Total In-Stock Items</div>
            <div class="fs-4 fw-bold text-dark">{{ total_items }} units</div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card p-3">
            <div class="text-muted small fw-bold text-uppercase">Stock Valuation (Cost)</div>
            <div class="fs-4 fw-bold text-secondary">{{ total_val_cost|inr }}</div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card p-3">
            <div class="text-muted small fw-bold text-uppercase">Stock Valuation (Retail MRP)</div>
            <div class="fs-4 fw-bold text-primary">{{ total_val_mrp|inr }}</div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card p-3">
            <div class="text-muted small fw-bold text-uppercase">Low / Out of Stock</div>
            <div class="fs-4 fw-bold text-danger">{{ low_stock_count }} items</div>
        </div>
    </div>
</div>

<div class="card">
    <div class="card-header fw-bold">Stock Movement Audit Log</div>
    <div class="table-responsive">
        <table class="table table-hover mb-0">
            <thead>
                <tr>
                    <th>Timestamp</th>
                    <th>Product</th>
                    <th>Movement Type</th>
                    <th>Qty</th>
                    <th>Previous &rarr; New</th>
                    <th>Reference / Notes</th>
                </tr>
            </thead>
            <tbody>
                {% for m in recent_movements %}
                    <tr>
                        <td class="small">{{ m.created_at|date:"d-m-Y H:i" }}</td>
                        <td class="fw-bold">{{ m.product.name }}</td>
                        <td><span class="badge bg-light text-dark border">{{ m.get_movement_type_display }}</span></td>
                        <td class="fw-bold">{{ m.quantity }}</td>
                        <td>{{ m.previous_stock }} &rarr; {{ m.new_stock }}</td>
                        <td class="small text-muted">{{ m.notes|default:"-" }}</td>
                    </tr>
                {% empty %}
                    <tr><td colspan="6" class="text-center py-4 text-muted">No stock movements recorded.</td></tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% endblock %}
"""
with open(os.path.join(BASE_DIR, "templates", "inventory", "stock_list.html"), "w", encoding="utf-8") as f:
    f.write(stock_list_html)

# templates/inventory/imei_list.html
imei_list_html = """{% extends 'base.html' %}
{% load dukaan_tags %}

{% block title %}IMEI Device Tracker — {{ current_business.name }}{% endblock %}

{% block content %}
<div class="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2">
    <div>
        <h4 class="fw-bold mb-0">IMEI & Mobile Device Tracker</h4>
        <span class="text-muted small">Available in stock: <strong>{{ in_stock_count }}</strong> | Sold: <strong>{{ sold_count }}</strong></span>
    </div>
    <div class="d-flex gap-2">
        <a href="{% url 'inventory:imei_search' %}" class="btn btn-outline-primary"><i class="bi bi-search me-1"></i> Quick Search</a>
        <a href="{% url 'inventory:imei_create' %}" class="btn btn-primary fw-bold"><i class="bi bi-plus-circle-fill me-1"></i> Register Device</a>
    </div>
</div>

<div class="card p-3 mb-3">
    <form method="get" class="row g-2">
        <div class="col-md-6">
            <div class="input-group">
                <span class="input-group-text"><i class="bi bi-search"></i></span>
                <input type="text" name="q" class="form-control" placeholder="Search by 15-digit IMEI, Model, S/N, Customer..." value="{{ query }}">
            </div>
        </div>
        <div class="col-md-3">
            <select name="status" class="form-select">
                <option value="">All Statuses</option>
                <option value="IN_STOCK" {% if status_filter == 'IN_STOCK' %}selected{% endif %}>In Stock</option>
                <option value="SOLD" {% if status_filter == 'SOLD' %}selected{% endif %}>Sold</option>
                <option value="DEFECTIVE" {% if status_filter == 'DEFECTIVE' %}selected{% endif %}>Defective / In Repair</option>
            </select>
        </div>
        <div class="col-md-3 d-flex gap-2">
            <button type="submit" class="btn btn-secondary flex-grow-1">Filter</button>
            <a href="{% url 'inventory:imei_list' %}" class="btn btn-outline-secondary">Reset</a>
        </div>
    </form>
</div>

<div class="card">
    <div class="table-responsive">
        <table class="table table-hover mb-0">
            <thead>
                <tr>
                    <th>Primary IMEI 1</th>
                    <th>Model / Variant</th>
                    <th>Status</th>
                    <th>Selling Price</th>
                    <th>Sold To Customer</th>
                    <th>Sale Date</th>
                    <th>Warranty Upto</th>
                </tr>
            </thead>
            <tbody>
                {% for dev in page_obj %}
                    <tr>
                        <td class="font-monospace fw-bold text-primary">
                            {{ dev.imei_1 }}
                            {% if dev.imei_2 %}<div class="text-muted small font-monospace">IMEI 2: {{ dev.imei_2 }}</div>{% endif %}
                        </td>
                        <td>
                            <strong>{{ dev.product.name }}</strong>
                            {% if dev.model_name %}<div class="text-muted small">{{ dev.model_name }}</div>{% endif %}
                        </td>
                        <td>
                            {% if dev.status == 'IN_STOCK' %}
                                <span class="badge bg-success">In Stock</span>
                            {% elif dev.status == 'SOLD' %}
                                <span class="badge bg-secondary">Sold</span>
                            {% else %}
                                <span class="badge bg-warning">{{ dev.status }}</span>
                            {% endif %}
                        </td>
                        <td class="fw-bold">{{ dev.selling_price|inr }}</td>
                        <td>
                            {% if dev.customer %}
                                <a href="{% url 'customers:detail' dev.customer.pk %}" class="text-decoration-none fw-bold">{{ dev.customer.name }}</a>
                            {% else %}
                                <span class="text-muted">-</span>
                            {% endif %}
                        </td>
                        <td class="small">{{ dev.sale_date|date:"d-m-Y"|default:"-" }}</td>
                        <td class="small">
                            {% if dev.warranty_expiry_date %}
                                <span class="badge bg-info-subtle text-info">{{ dev.warranty_expiry_date|date:"d-m-Y" }}</span>
                            {% else %}
                                <span class="text-muted">-</span>
                            {% endif %}
                        </td>
                    </tr>
                {% empty %}
                    <tr><td colspan="7" class="text-center py-4 text-muted">No mobile devices found. Register phones to start tracking serial numbers.</td></tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% endblock %}
"""
with open(os.path.join(BASE_DIR, "templates", "inventory", "imei_list.html"), "w", encoding="utf-8") as f:
    f.write(imei_list_html)

# templates/inventory/imei_form.html
imei_form_html = """{% extends 'base.html' %}

{% block title %}{{ title }} — {{ current_business.name }}{% endblock %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-lg-6">
        <div class="card p-4 shadow-sm">
            <h5 class="fw-bold mb-3 border-bottom pb-2"><i class="bi bi-upc-scan text-primary me-2"></i>{{ title }}</h5>
            <form method="post">
                {% csrf_token %}
                <div class="mb-3">
                    <label class="form-label small fw-bold">Select Phone Product *</label>
                    {{ form.product }}
                </div>
                <div class="row g-2 mb-3">
                    <div class="col-md-6">
                        <label class="form-label small fw-bold">Primary IMEI 1 *</label>
                        {{ form.imei_1 }}
                    </div>
                    <div class="col-md-6">
                        <label class="form-label small fw-bold">Secondary IMEI 2</label>
                        {{ form.imei_2 }}
                    </div>
                </div>
                <div class="row g-2 mb-3">
                    <div class="col-md-6">
                        <label class="form-label small fw-bold">Brand</label>
                        {{ form.brand }}
                    </div>
                    <div class="col-md-6">
                        <label class="form-label small fw-bold">Model / Color / RAM</label>
                        {{ form.model_name }}
                    </div>
                </div>
                <div class="row g-2 mb-3">
                    <div class="col-md-6">
                        <label class="form-label small fw-bold">Cost Price (₹)</label>
                        {{ form.purchase_price }}
                    </div>
                    <div class="col-md-6">
                        <label class="form-label small fw-bold">Selling Price (₹)</label>
                        {{ form.selling_price }}
                    </div>
                </div>
                <div class="mb-3">
                    <label class="form-label small fw-bold">Device Status</label>
                    {{ form.status }}
                </div>
                <div class="mb-4">
                    <label class="form-label small fw-bold">Notes / Serial No.</label>
                    {{ form.notes }}
                </div>
                <div class="d-flex gap-2">
                    <button type="submit" class="btn btn-primary fw-bold px-4">Save Device</button>
                    <a href="{% url 'inventory:imei_list' %}" class="btn btn-light border">Cancel</a>
                </div>
            </form>
        </div>
    </div>
</div>
{% endblock %}
"""
with open(os.path.join(BASE_DIR, "templates", "inventory", "imei_form.html"), "w", encoding="utf-8") as f:
    f.write(imei_form_html)

# templates/inventory/imei_search.html
imei_search_html = """{% extends 'base.html' %}
{% load dukaan_tags %}

{% block title %}Quick IMEI Search — {{ current_business.name }}{% endblock %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-lg-8">
        <div class="card p-4 shadow-sm mb-4">
            <h4 class="fw-bold mb-3"><i class="bi bi-search text-primary me-2"></i>Global IMEI & Device Lookup</h4>
            <p class="text-muted small">Enter any 15-digit IMEI number to instantly trace its complete history, purchase cost, sale invoice, customer, and warranty expiration.</p>
            
            <form method="get" class="d-flex gap-2">
                <input type="text" name="imei" class="form-control form-control-lg font-monospace" placeholder="Enter IMEI 1, IMEI 2 or Serial Number..." value="{{ query }}" required autofocus>
                <button type="submit" class="btn btn-primary btn-lg fw-bold px-4">Search</button>
            </form>
        </div>

        {% if query %}
            {% if device %}
                <div class="card p-4 shadow-sm border-success">
                    <div class="d-flex justify-content-between align-items-center border-bottom pb-3 mb-3">
                        <div>
                            <span class="badge bg-success mb-1">RECORD FOUND</span>
                            <h4 class="fw-bold mb-0">{{ device.product.name }}</h4>
                            <span class="text-muted">{{ device.brand|default:"" }} {{ device.model_name|default:"" }}</span>
                        </div>
                        <div class="text-end">
                            <div class="fs-5 fw-bold text-primary">{{ device.selling_price|inr }}</div>
                            <span class="badge bg-light text-dark border">{{ device.get_status_display }}</span>
                        </div>
                    </div>

                    <div class="row g-3 mb-3">
                        <div class="col-md-6">
                            <label class="text-muted small fw-bold text-uppercase">Primary IMEI 1</label>
                            <div class="font-monospace fs-5 fw-bold">{{ device.imei_1 }}</div>
                        </div>
                        {% if device.imei_2 %}
                        <div class="col-md-6">
                            <label class="text-muted small fw-bold text-uppercase">Secondary IMEI 2</label>
                            <div class="font-monospace fs-5">{{ device.imei_2 }}</div>
                        </div>
                        {% endif %}
                    </div>

                    <div class="row g-3 p-3 bg-light rounded border mb-3">
                        <div class="col-md-4">
                            <div class="text-muted small fw-bold">OWNER / CUSTOMER</div>
                            {% if device.customer %}
                                <div class="fw-bold"><a href="{% url 'customers:detail' device.customer.pk %}" class="text-decoration-none">{{ device.customer.name }}</a></div>
                                <div class="small text-muted">{{ device.customer.phone }}</div>
                            {% else %}
                                <div class="text-muted">Unsold in stock</div>
                            {% endif %}
                        </div>
                        <div class="col-md-4">
                            <div class="text-muted small fw-bold">SALE DATE</div>
                            <div class="fw-bold">{{ device.sale_date|date:"d-m-Y H:i"|default:"Not sold yet" }}</div>
                        </div>
                        <div class="col-md-4">
                            <div class="text-muted small fw-bold">WARRANTY STATUS</div>
                            {% if device.warranty_expiry_date %}
                                <div class="fw-bold text-success">Valid until {{ device.warranty_expiry_date|date:"d-m-Y" }}</div>
                            {% else %}
                                <div class="text-muted">No warranty attached</div>
                            {% endif %}
                        </div>
                    </div>

                    {% if device.sale_item and device.sale_item.sale %}
                        <div class="d-flex justify-content-between align-items-center">
                            <span>Associated Bill: <strong>#{{ device.sale_item.sale.invoice_number }}</strong></span>
                            <a href="{% url 'invoices:detail' device.sale_item.sale.pk %}" class="btn btn-outline-primary btn-sm"><i class="bi bi-receipt me-1"></i> View Invoice</a>
                        </div>
                    {% endif %}
                </div>
            {% else %}
                <div class="alert alert-warning text-center p-4">
                    <i class="bi bi-exclamation-circle fs-3 d-block mb-2"></i>
                    No device found matching IMEI: <strong>{{ query }}</strong>
                </div>
            {% endif %}
        {% endif %}
    </div>
</div>
{% endblock %}
"""
with open(os.path.join(BASE_DIR, "templates", "inventory", "imei_search.html"), "w", encoding="utf-8") as f:
    f.write(imei_search_html)

print("Phase 8c (CRM & Catalog Templates) created successfully!")
