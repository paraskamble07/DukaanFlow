import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# templates/accounts/login.html
login_html = """{% extends 'base.html' %}
{% load dukaan_tags %}

{% block title %}Login — DukaanFlow{% endblock %}

{% block public_content %}
<div class="container d-flex flex-column justify-content-center align-items-center flex-grow-1 py-5">
    <div class="card shadow-sm border p-4 p-md-5" style="max-width: 440px; width: 100%;">
        <div class="text-center mb-4">
            <a href="{% url 'landing:home' %}" class="text-decoration-none">
                <h3 class="fw-bold text-dark"><i class="bi bi-phone-vibrate text-primary"></i> DUKAAN<span class="text-primary">FLOW</span></h3>
            </a>
            <p class="text-muted small">Sign in to manage your mobile shop</p>
        </div>

        {% if messages %}
            {% for message in messages %}
                <div class="alert alert-{{ message.tags|default:'danger' }} py-2 small" role="alert">
                    {{ message }}
                </div>
            {% endfor %}
        {% endif %}

        <form method="post" action="{% url 'accounts:login' %}{% if request.GET.next %}?next={{ request.GET.next }}{% endif %}">
            {% csrf_token %}
            <div class="mb-3">
                <label class="form-label small fw-bold">Email Address or Username</label>
                {{ form.email }}
            </div>
            <div class="mb-4">
                <label class="form-label small fw-bold">Password</label>
                {{ form.password }}
            </div>
            <button type="submit" class="btn btn-primary w-100 fw-bold py-2 shadow-sm">Sign In to Dashboard</button>
        </form>

        <div class="text-center mt-4 border-top pt-3">
            <span class="text-muted small">Don't have an account?</span>
            <a href="{% url 'accounts:register' %}" class="fw-bold small text-primary text-decoration-none ms-1">Register Shop Free</a>
        </div>
    </div>
</div>
{% endblock %}
"""
with open(os.path.join(BASE_DIR, "templates", "accounts", "login.html"), "w", encoding="utf-8") as f:
    f.write(login_html)

# templates/accounts/register.html
register_html = """{% extends 'base.html' %}

{% block title %}Register Shop — DukaanFlow{% endblock %}

{% block public_content %}
<div class="container d-flex flex-column justify-content-center align-items-center flex-grow-1 py-5">
    <div class="card shadow-sm border p-4 p-md-5" style="max-width: 520px; width: 100%;">
        <div class="text-center mb-4">
            <a href="{% url 'landing:home' %}" class="text-decoration-none">
                <h3 class="fw-bold text-dark"><i class="bi bi-phone-vibrate text-primary"></i> DUKAAN<span class="text-primary">FLOW</span></h3>
            </a>
            <p class="text-muted small">Create your shop account in 60 seconds</p>
        </div>

        {% if form.errors %}
            <div class="alert alert-danger py-2 small" role="alert">
                Please correct the errors below.
                {{ form.errors }}
            </div>
        {% endif %}

        <form method="post" action="{% url 'accounts:register' %}">
            {% csrf_token %}
            <div class="mb-3">
                <label class="form-label small fw-bold">Owner Full Name</label>
                {{ form.full_name }}
            </div>
            <div class="mb-3">
                <label class="form-label small fw-bold">Shop / Business Name</label>
                {{ form.shop_name }}
            </div>
            <div class="row g-2 mb-3">
                <div class="col-md-6">
                    <label class="form-label small fw-bold">WhatsApp / Mobile No.</label>
                    {{ form.phone }}
                </div>
                <div class="col-md-6">
                    <label class="form-label small fw-bold">Email Address</label>
                    {{ form.email }}
                </div>
            </div>
            <div class="row g-2 mb-4">
                <div class="col-md-6">
                    <label class="form-label small fw-bold">Create Password</label>
                    {{ form.password }}
                </div>
                <div class="col-md-6">
                    <label class="form-label small fw-bold">Confirm Password</label>
                    {{ form.confirm_password }}
                </div>
            </div>
            <button type="submit" class="btn btn-primary w-100 fw-bold py-2 shadow-sm">Create Shop & Start Free</button>
        </form>

        <div class="text-center mt-4 border-top pt-3">
            <span class="text-muted small">Already have a shop account?</span>
            <a href="{% url 'accounts:login' %}" class="fw-bold small text-primary text-decoration-none ms-1">Sign In</a>
        </div>
    </div>
</div>
{% endblock %}
"""
with open(os.path.join(BASE_DIR, "templates", "accounts", "register.html"), "w", encoding="utf-8") as f:
    f.write(register_html)

# templates/accounts/profile.html
profile_html = """{% extends 'base.html' %}

{% block title %}My Profile — DukaanFlow{% endblock %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-lg-6">
        <div class="card p-4">
            <h5 class="fw-bold mb-3"><i class="bi bi-person-circle text-primary me-2"></i>User Profile</h5>
            <form method="post">
                {% csrf_token %}
                <div class="mb-3">
                    <label class="form-label small fw-bold">Username / Login ID</label>
                    <input type="text" class="form-control" value="{{ user.username }}" readonly disabled>
                </div>
                <div class="row g-2 mb-3">
                    <div class="col-md-6">
                        <label class="form-label small fw-bold">First Name</label>
                        <input type="text" name="first_name" class="form-control" value="{{ user.first_name }}">
                    </div>
                    <div class="col-md-6">
                        <label class="form-label small fw-bold">Last Name</label>
                        <input type="text" name="last_name" class="form-control" value="{{ user.last_name }}">
                    </div>
                </div>
                <div class="mb-3">
                    <label class="form-label small fw-bold">Contact Phone / WhatsApp</label>
                    <input type="text" name="phone" class="form-control" value="{{ profile.phone|default:'' }}">
                </div>
                <div class="mb-4">
                    <label class="form-label small fw-bold">Associated Shop</label>
                    <input type="text" class="form-control" value="{{ profile.business.name|default:'No business attached' }}" readonly disabled>
                </div>
                <button type="submit" class="btn btn-primary fw-bold px-4">Save Changes</button>
            </form>
        </div>
    </div>
</div>
{% endblock %}
"""
with open(os.path.join(BASE_DIR, "templates", "accounts", "profile.html"), "w", encoding="utf-8") as f:
    f.write(profile_html)

# templates/businesses/settings.html
settings_html = """{% extends 'base.html' %}

{% block title %}Shop Settings — DukaanFlow{% endblock %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-lg-8">
        <div class="card p-4 shadow-sm">
            <div class="d-flex justify-content-between align-items-center mb-3 border-bottom pb-2">
                <h5 class="fw-bold mb-0"><i class="bi bi-shop text-primary me-2"></i>{% if is_onboarding %}Setup Your Shop Profile{% else %}Shop & Invoice Settings{% endif %}</h5>
                {% if not is_onboarding %}
                    <span class="badge bg-primary">{{ business.get_plan_tier_display }}</span>
                {% endif %}
            </div>

            <form method="post" enctype="multipart/form-data">
                {% csrf_token %}
                <div class="row g-3 mb-3">
                    <div class="col-md-6">
                        <label class="form-label small fw-bold">Shop / Business Name *</label>
                        {{ form.name }}
                    </div>
                    <div class="col-md-6">
                        <label class="form-label small fw-bold">Owner Name *</label>
                        {{ form.owner_name }}
                    </div>
                </div>
                
                <div class="row g-3 mb-3">
                    <div class="col-md-6">
                        <label class="form-label small fw-bold">Mobile / WhatsApp Number *</label>
                        {{ form.phone }}
                    </div>
                    <div class="col-md-6">
                        <label class="form-label small fw-bold">Business Email *</label>
                        {{ form.email }}
                    </div>
                </div>

                <div class="mb-3">
                    <label class="form-label small fw-bold">Shop Address / Landmark</label>
                    {{ form.address }}
                </div>

                <div class="row g-3 mb-3">
                    <div class="col-md-4">
                        <label class="form-label small fw-bold">City</label>
                        {{ form.city }}
                    </div>
                    <div class="col-md-4">
                        <label class="form-label small fw-bold">State</label>
                        {{ form.state }}
                    </div>
                    <div class="col-md-4">
                        <label class="form-label small fw-bold">Pincode</label>
                        {{ form.pincode }}
                    </div>
                </div>

                <div class="row g-3 mb-3">
                    <div class="col-md-6">
                        <label class="form-label small fw-bold">GSTIN Number (Optional)</label>
                        {{ form.gstin }}
                    </div>
                    <div class="col-md-6">
                        <label class="form-label small fw-bold">Shop Logo (For Invoices)</label>
                        {{ form.logo }}
                    </div>
                </div>

                <hr class="my-4">
                <h6 class="fw-bold mb-3 text-secondary">Invoice Customization</h6>

                <div class="row g-3 mb-3">
                    <div class="col-md-4">
                        <label class="form-label small fw-bold">Invoice Prefix</label>
                        {{ form.invoice_prefix }}
                    </div>
                    <div class="col-md-8">
                        <label class="form-label small fw-bold">Invoice Terms / Footer Note</label>
                        {{ form.invoice_footer }}
                    </div>
                </div>

                <div class="mt-4">
                    <button type="submit" class="btn btn-primary fw-bold px-4 py-2">
                        <i class="bi bi-check2-circle me-1"></i> Save Shop Settings
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>
{% endblock %}
"""
with open(os.path.join(BASE_DIR, "templates", "businesses", "settings.html"), "w", encoding="utf-8") as f:
    f.write(settings_html)

# templates/businesses/plans.html
plans_html = """{% extends 'base.html' %}
{% load dukaan_tags %}

{% block title %}Subscription Plans — DukaanFlow{% endblock %}

{% block content %}
<div class="text-center mb-5">
    <span class="text-primary fw-bold text-uppercase">Subscription Management</span>
    <h3 class="fw-bold mt-1">Upgrade or Switch Plan</h3>
    <p class="text-muted">Currently Active Plan: <span class="badge bg-primary fs-6">{{ business.get_plan_tier_display }}</span></p>
</div>

<div class="row g-4 justify-content-center">
    {% for key, plan in plans.items %}
    <div class="col-lg-4 col-md-6">
        <div class="card h-100 p-4 border {% if current_plan == key %}border-primary border-3 shadow{% else %}shadow-sm{% endif %} position-relative">
            {% if current_plan == key %}
                <div class="position-absolute top-0 end-0 bg-primary text-white small fw-bold px-3 py-1 rounded-bottom-start">CURRENT ACTIVE</div>
            {% endif %}
            <h4 class="fw-bold">{{ plan.name }}</h4>
            <div class="display-6 fw-bold text-dark my-3">₹{{ plan.price }} <span class="fs-6 text-muted font-monospace">/ month</span></div>
            
            <ul class="list-unstyled d-flex flex-column gap-2 mb-4">
                <li><i class="bi bi-check2 text-success me-2"></i> {% if plan.max_customers > 10000 %}<strong>Unlimited</strong>{% else %}Up to {{ plan.max_customers }}{% endif %} Customers</li>
                <li><i class="bi bi-check2 text-success me-2"></i> {% if plan.max_products > 10000 %}<strong>Unlimited</strong>{% else %}Up to {{ plan.max_products }}{% endif %} Products</li>
                <li><i class="bi bi-check2 text-success me-2"></i> Dual IMEI Tracking</li>
                <li><i class="bi bi-check2 text-success me-2"></i> POS Billing & ReportLab PDF</li>
                <li><i class="bi bi-check2 text-success me-2"></i> Free WhatsApp Reminders</li>
                <li><i class="bi bi-check2 text-success me-2"></i> Up to {{ plan.max_staff }} Staff Accounts</li>
            </ul>

            <form method="post" class="mt-auto">
                {% csrf_token %}
                <input type="hidden" name="plan" value="{{ key }}">
                {% if current_plan == key %}
                    <button type="button" class="btn btn-secondary w-100 fw-bold disabled" disabled>Active Plan</button>
                {% else %}
                    <button type="submit" class="btn btn-primary w-100 fw-bold">Select {{ plan.name }}</button>
                {% endif %}
            </form>
        </div>
    </div>
    {% endfor %}
</div>
{% endblock %}
"""
with open(os.path.join(BASE_DIR, "templates", "businesses", "plans.html"), "w", encoding="utf-8") as f:
    f.write(plans_html)

# templates/dashboard/index.html
dashboard_html = """{% extends 'base.html' %}
{% load dukaan_tags %}

{% block title %}Dashboard — {{ current_business.name }}{% endblock %}

{% block extra_head %}
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
{% endblock %}

{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
    <div>
        <h4 class="fw-bold mb-0">Shop Performance Overview</h4>
        <span class="text-muted small">Today: {{ today|date:"l, d F Y" }}</span>
    </div>
    <div class="d-flex gap-2">
        <a href="{% url 'sales:pos' %}" class="btn btn-primary fw-bold shadow-sm d-flex align-items-center gap-1">
            <i class="bi bi-cart-plus-fill"></i> New POS Sale
        </a>
    </div>
</div>

<!-- Top KPI Cards Row -->
<div class="row g-3 mb-4">
    <div class="col-xl-3 col-md-6">
        <div class="stat-card bg-white">
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <div class="text-muted small fw-bold text-uppercase">Today's Sales</div>
                    <div class="fs-4 fw-bold text-dark">{{ today_sales|inr }}</div>
                    <span class="badge bg-primary-subtle text-primary mt-1">{{ today_sales_count }} bills generated</span>
                </div>
                <div class="stat-icon bg-primary-subtle text-primary">
                    <i class="bi bi-receipt"></i>
                </div>
            </div>
        </div>
    </div>

    <div class="col-xl-3 col-md-6">
        <div class="stat-card bg-white">
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <div class="text-muted small fw-bold text-uppercase">Today's Net Profit</div>
                    <div class="fs-4 fw-bold text-success">{{ today_net_profit|inr }}</div>
                    <span class="text-muted small">Gross: {{ today_gross_profit|inr }}</span>
                </div>
                <div class="stat-icon bg-success-subtle text-success">
                    <i class="bi bi-cash-coin"></i>
                </div>
            </div>
        </div>
    </div>

    <div class="col-xl-3 col-md-6">
        <div class="stat-card bg-white">
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <div class="text-muted small fw-bold text-uppercase">Customer Khata (Due)</div>
                    <div class="fs-4 fw-bold text-danger">{{ total_receivable|inr }}</div>
                    <span class="text-muted small">Market Udhar to Collect</span>
                </div>
                <div class="stat-icon bg-danger-subtle text-danger">
                    <i class="bi bi-person-exclamation"></i>
                </div>
            </div>
        </div>
    </div>

    <div class="col-xl-3 col-md-6">
        <div class="stat-card bg-white">
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <div class="text-muted small fw-bold text-uppercase">Supplier Payable</div>
                    <div class="fs-4 fw-bold text-warning">{{ total_payable|inr }}</div>
                    <span class="text-muted small">Vendor Outstanding</span>
                </div>
                <div class="stat-icon bg-warning-subtle text-warning">
                    <i class="bi bi-truck"></i>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Secondary Stats & Chart Row -->
<div class="row g-3 mb-4">
    <!-- 7-Day Trend Chart -->
    <div class="col-lg-8">
        <div class="card h-100">
            <div class="card-header d-flex justify-content-between align-items-center">
                <span class="fw-bold"><i class="bi bi-graph-up text-primary me-2"></i>Last 7 Days Sales & Expense Trend</span>
                <span class="badge bg-light text-dark border">Realtime DB Data</span>
            </div>
            <div class="card-body">
                <canvas id="salesTrendChart" style="max-height: 280px;"></canvas>
            </div>
        </div>
    </div>

    <!-- Quick Alerts & Stock Status -->
    <div class="col-lg-4">
        <div class="card h-100">
            <div class="card-header fw-bold">
                <i class="bi bi-bell-fill text-warning me-2"></i>Stock & Inventory Alerts
            </div>
            <div class="card-body p-0">
                <div class="p-3 border-bottom d-flex justify-content-between align-items-center">
                    <div>
                        <div class="fw-bold">Total Catalog Products</div>
                        <div class="text-muted small">Registered in catalog</div>
                    </div>
                    <span class="badge bg-secondary fs-6">{{ total_products_count }}</span>
                </div>
                <div class="p-3 border-bottom d-flex justify-content-between align-items-center bg-danger-subtle">
                    <div>
                        <div class="fw-bold text-danger">Low / Out of Stock Items</div>
                        <div class="text-muted small">Requires reorder</div>
                    </div>
                    <span class="badge bg-danger fs-6">{{ low_stock_count }}</span>
                </div>
                
                <div class="p-3">
                    <div class="small fw-bold text-muted mb-2">URGENT LOW STOCK ITEMS:</div>
                    {% if low_stock_products %}
                        <ul class="list-unstyled mb-0">
                            {% for p in low_stock_products %}
                                <li class="d-flex justify-content-between align-items-center mb-2 pb-1 border-bottom">
                                    <span class="small fw-bold">{{ p.name|truncatechars:22 }}</span>
                                    <span class="badge bg-danger">{{ p.stock_quantity }} left</span>
                                </li>
                            {% endfor %}
                        </ul>
                    {% else %}
                        <div class="text-success small"><i class="bi bi-check-circle-fill me-1"></i> All products have healthy inventory!</div>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Transactions & Pending Udhar Row -->
<div class="row g-3">
    <!-- Recent Sales -->
    <div class="col-lg-7">
        <div class="card">
            <div class="card-header d-flex justify-content-between align-items-center">
                <span class="fw-bold"><i class="bi bi-receipt me-2"></i>Recent Sales Transactions</span>
                <a href="{% url 'sales:list' %}" class="small text-primary text-decoration-none">View All</a>
            </div>
            <div class="table-responsive">
                <table class="table table-hover mb-0">
                    <thead>
                        <tr>
                            <th>Invoice</th>
                            <th>Customer</th>
                            <th>Total</th>
                            <th>Status</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for sale in recent_sales %}
                            <tr>
                                <td class="fw-bold text-primary">#{{ sale.invoice_number }}</td>
                                <td>{{ sale.customer.name }}</td>
                                <td class="fw-bold">{{ sale.total_amount|inr }}</td>
                                <td>
                                    {% if sale.payment_status == 'PAID' %}
                                        <span class="badge bg-success">Paid</span>
                                    {% elif sale.payment_status == 'PARTIAL' %}
                                        <span class="badge bg-warning text-dark">Partial</span>
                                    {% else %}
                                        <span class="badge bg-danger">Credit</span>
                                    {% endif %}
                                </td>
                                <td>
                                    <a href="{% url 'invoices:detail' sale.pk %}" class="btn btn-light btn-sm border"><i class="bi bi-eye"></i></a>
                                </td>
                            </tr>
                        {% empty %}
                            <tr><td colspan="5" class="text-center py-4 text-muted">No sales recorded yet. Click <strong>New POS Sale</strong> to create your first bill!</td></tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- Outstanding Customer Khata & WhatsApp Quick Reminders -->
    <div class="col-lg-5">
        <div class="card">
            <div class="card-header d-flex justify-content-between align-items-center">
                <span class="fw-bold"><i class="bi bi-whatsapp text-success me-2"></i>Pending Khata Collection</span>
                <a href="{% url 'customers:list' %}?due=yes" class="small text-primary text-decoration-none">All Dues</a>
            </div>
            <div class="p-0">
                {% if top_pending_customers %}
                    <ul class="list-group list-group-flush">
                        {% for item in top_pending_customers %}
                            <li class="list-group-item d-flex justify-content-between align-items-center py-3">
                                <div>
                                    <div class="fw-bold">{{ item.customer.name }}</div>
                                    <div class="small text-muted">{{ item.customer.phone }}</div>
                                    <div class="text-danger fw-bold small">Due: {{ item.due|inr }}</div>
                                </div>
                                <a href="{{ item.wa_url }}" target="_blank" class="btn btn-whatsapp btn-sm shadow-sm d-flex align-items-center gap-1">
                                    <i class="bi bi-whatsapp"></i> Remind
                                </a>
                            </li>
                        {% endfor %}
                    </ul>
                {% else %}
                    <div class="p-4 text-center text-muted">
                        <i class="bi bi-emoji-smile fs-3 text-success d-block mb-1"></i>
                        Zero pending customer dues! All Khata accounts settled.
                    </div>
                {% endif %}
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_scripts %}
<script>
document.addEventListener('DOMContentLoaded', function() {
    const ctx = document.getElementById('salesTrendChart').getContext('2d');
    const labels = {{ chart_labels|safe }};
    const salesData = {{ chart_sales_data|safe }};
    const expenseData = {{ chart_expense_data|safe }};

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Sales (₹)',
                    data: salesData,
                    backgroundColor: 'rgba(30, 64, 175, 0.85)',
                    borderRadius: 6,
                },
                {
                    label: 'Expenses (₹)',
                    data: expenseData,
                    backgroundColor: 'rgba(239, 68, 68, 0.75)',
                    borderRadius: 6,
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'top' },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ₹' + context.parsed.y.toLocaleString('en-IN');
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) { return '₹' + value.toLocaleString('en-IN'); }
                    }
                }
            }
        }
    });
});
</script>
{% endblock %}
"""
with open(os.path.join(BASE_DIR, "templates", "dashboard", "index.html"), "w", encoding="utf-8") as f:
    f.write(dashboard_html)

print("Phase 8b (Auth & Dashboard Templates) created successfully!")
