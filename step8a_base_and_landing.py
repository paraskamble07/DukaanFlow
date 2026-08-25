import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# static/css/custom.css
custom_css = """
:root {
    --df-primary: #1E40AF;
    --df-primary-hover: #1D4ED8;
    --df-secondary: #0D9488;
    --df-dark: #0F172A;
    --df-sidebar: #0F172A;
    --df-card-bg: #FFFFFF;
    --df-border: #E2E8F0;
    --df-success: #10B981;
    --df-danger: #EF4444;
    --df-warning: #F59E0B;
    --df-info: #0284C7;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    background-color: #F8FAFC;
    color: #1E293B;
    min-height: 100vh;
}

/* Sidebar Styling */
.sidebar {
    width: 260px;
    background-color: var(--df-sidebar);
    min-height: 100vh;
    transition: all 0.3s ease;
    z-index: 1040;
}

.sidebar .nav-link {
    color: #94A3B8;
    font-weight: 500;
    font-size: 0.95rem;
    padding: 0.65rem 1rem;
    border-radius: 0.5rem;
    margin-bottom: 0.25rem;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    transition: all 0.2s ease;
}

.sidebar .nav-link:hover {
    color: #FFFFFF;
    background-color: rgba(255, 255, 255, 0.08);
}

.sidebar .nav-link.active {
    color: #FFFFFF;
    background-color: var(--df-primary);
}

.sidebar .nav-link i {
    font-size: 1.15rem;
}

.sidebar-heading {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #64748B;
    padding: 0.75rem 1rem 0.25rem;
    font-weight: 700;
}

/* Main Content Area */
.main-content {
    flex: 1;
    min-width: 0;
    overflow-y: auto;
}

/* Card Styling */
.card {
    border: 1px solid var(--df-border);
    border-radius: 0.75rem;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
    background-color: #FFFFFF;
}

.card-header {
    background-color: #FFFFFF;
    border-bottom: 1px solid var(--df-border);
    padding: 1rem 1.25rem;
    font-weight: 600;
}

/* Stat Cards */
.stat-card {
    border-radius: 0.75rem;
    border: 1px solid var(--df-border);
    padding: 1.25rem;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.stat-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.stat-icon {
    width: 48px;
    height: 48px;
    border-radius: 0.5rem;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.5rem;
}

/* Indian Rupee highlight badges */
.inr-badge-due {
    background-color: #FEE2E2;
    color: #991B1B;
    font-weight: 600;
    padding: 0.25rem 0.5rem;
    border-radius: 0.375rem;
}

.inr-badge-success {
    background-color: #D1FAE5;
    color: #065F46;
    font-weight: 600;
    padding: 0.25rem 0.5rem;
    border-radius: 0.375rem;
}

/* WhatsApp Action Button */
.btn-whatsapp {
    background-color: #25D366;
    color: #FFFFFF;
    border: none;
    font-weight: 500;
}

.btn-whatsapp:hover {
    background-color: #1EBE5D;
    color: #FFFFFF;
}

/* Table Responsive */
.table th {
    font-size: 0.82rem;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    color: #64748B;
    font-weight: 600;
    background-color: #F8FAFC;
}

.table td {
    vertical-align: middle;
    font-size: 0.92rem;
}

/* Responsive adjustments */
@media (max-width: 991.98px) {
    .sidebar {
        display: none;
    }
}
"""
with open(os.path.join(BASE_DIR, "static", "css", "custom.css"), "w", encoding="utf-8") as f:
    f.write(custom_css)

# static/js/main.js
main_js = """
// DukaanFlow Global JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
});
"""
with open(os.path.join(BASE_DIR, "static", "js", "main.js"), "w", encoding="utf-8") as f:
    f.write(main_js)

# templates/base.html
base_html = """{% load static dukaan_tags %}
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}DukaanFlow — Mobile Shop SaaS{% endblock %}</title>
    <!-- Bootstrap 5 CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- Bootstrap Icons -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
    <!-- Custom CSS -->
    <link rel="stylesheet" href="{% static 'css/custom.css' %}">
    {% block extra_head %}{% endblock %}
</head>
<body>

{% if user.is_authenticated and current_business %}
<div class="d-flex min-vh-100">
    <!-- Desktop Sidebar -->
    <aside class="sidebar d-none d-lg-flex flex-column flex-shrink-0 p-3">
        <div class="d-flex align-items-center mb-3 mb-md-0 me-md-auto text-white text-decoration-none px-2">
            <i class="bi bi-phone-vibrate text-primary fs-3 me-2"></i>
            <div>
                <span class="fs-5 fw-bold tracking-tight">DUKAAN<span class="text-primary">FLOW</span></span>
                <div class="small text-muted" style="font-size: 0.75rem;">{{ current_business.name|truncatechars:20 }}</div>
            </div>
        </div>
        <hr class="border-secondary my-3">
        
        <div class="mb-2 px-2">
            <a href="{% url 'sales:pos' %}" class="btn btn-primary w-100 fw-bold shadow-sm d-flex align-items-center justify-content-center gap-2">
                <i class="bi bi-cart-plus-fill"></i> New POS Sale
            </a>
        </div>

        <ul class="nav nav-pills flex-column mb-auto">
            <li class="nav-item">
                <a href="{% url 'dashboard:index' %}" class="nav-link {% if request.resolver_match.app_name == 'dashboard' %}active{% endif %}">
                    <i class="bi bi-speedometer2"></i> Dashboard
                </a>
            </li>
            
            <div class="sidebar-heading">Billing & Sales</div>
            <li>
                <a href="{% url 'sales:list' %}" class="nav-link {% if request.resolver_match.app_name == 'sales' and request.resolver_match.url_name != 'pos' %}active{% endif %}">
                    <i class="bi bi-receipt"></i> Sales & Invoices
                </a>
            </li>
            <li>
                <a href="{% url 'customers:list' %}" class="nav-link {% if request.resolver_match.app_name == 'customers' %}active{% endif %}">
                    <i class="bi bi-people"></i> Customers & Khata
                </a>
            </li>
            <li>
                <a href="{% url 'payments:list' %}" class="nav-link {% if request.resolver_match.app_name == 'payments' %}active{% endif %}">
                    <i class="bi bi-cash-stack"></i> Payment Vouchers
                </a>
            </li>

            <div class="sidebar-heading">Inventory & Devices</div>
            <li>
                <a href="{% url 'products:list' %}" class="nav-link {% if request.resolver_match.app_name == 'products' %}active{% endif %}">
                    <i class="bi bi-box-seam"></i> Products & Stock
                </a>
            </li>
            <li>
                <a href="{% url 'inventory:imei_list' %}" class="nav-link {% if request.resolver_match.app_name == 'inventory' and request.resolver_match.url_name == 'imei_list' %}active{% endif %}">
                    <i class="bi bi-upc-scan"></i> IMEI Device Tracker
                </a>
            </li>
            <li>
                <a href="{% url 'inventory:imei_search' %}" class="nav-link {% if request.resolver_match.app_name == 'inventory' and request.resolver_match.url_name == 'imei_search' %}active{% endif %}">
                    <i class="bi bi-search"></i> Quick IMEI Search
                </a>
            </li>

            <div class="sidebar-heading">Vendors & Expenses</div>
            <li>
                <a href="{% url 'purchases:list' %}" class="nav-link {% if request.resolver_match.app_name == 'purchases' %}active{% endif %}">
                    <i class="bi bi-bag-check"></i> Stock Purchases
                </a>
            </li>
            <li>
                <a href="{% url 'suppliers:list' %}" class="nav-link {% if request.resolver_match.app_name == 'suppliers' %}active{% endif %}">
                    <i class="bi bi-truck"></i> Suppliers
                </a>
            </li>
            <li>
                <a href="{% url 'expenses:list' %}" class="nav-link {% if request.resolver_match.app_name == 'expenses' %}active{% endif %}">
                    <i class="bi bi-wallet2"></i> Daily Expenses
                </a>
            </li>

            <div class="sidebar-heading">Analytics & Settings</div>
            <li>
                <a href="{% url 'reports:index' %}" class="nav-link {% if request.resolver_match.app_name == 'reports' %}active{% endif %}">
                    <i class="bi bi-graph-up-arrow"></i> Reports & P&L
                </a>
            </li>
            <li>
                <a href="{% url 'businesses:settings' %}" class="nav-link {% if request.resolver_match.app_name == 'businesses' and request.resolver_match.url_name == 'settings' %}active{% endif %}">
                    <i class="bi bi-gear"></i> Shop Settings
                </a>
            </li>
            <li>
                <a href="{% url 'businesses:plans' %}" class="nav-link {% if request.resolver_match.app_name == 'businesses' and request.resolver_match.url_name == 'plans' %}active{% endif %}">
                    <i class="bi bi-stars text-warning"></i> Upgrade Plan
                </a>
            </li>
        </ul>
        
        <hr class="border-secondary my-2">
        <div class="dropdown">
            <a href="#" class="d-flex align-items-center text-white text-decoration-none dropdown-toggle px-2" id="dropdownUser1" data-bs-toggle="dropdown" aria-expanded="false">
                <div class="bg-primary text-white rounded-circle d-flex align-items-center justify-content-center me-2 fw-bold" style="width: 32px; height: 32px;">
                    {{ user.first_name|default:user.username|slice:":1"|upper }}
                </div>
                <div class="small">
                    <strong>{{ user.first_name|default:user.username }}</strong>
                    <div class="text-muted" style="font-size: 0.75rem;">{{ current_business.get_plan_tier_display }}</div>
                </div>
            </a>
            <ul class="dropdown-menu dropdown-menu-dark text-small shadow" aria-labelledby="dropdownUser1">
                <li><a class="dropdown-item" href="{% url 'accounts:profile' %}"><i class="bi bi-person me-2"></i>My Profile</a></li>
                <li><a class="dropdown-item" href="{% url 'businesses:settings' %}"><i class="bi bi-shop me-2"></i>Shop Profile</a></li>
                <li><hr class="dropdown-divider"></li>
                <li><a class="dropdown-item text-danger" href="{% url 'accounts:logout' %}"><i class="bi bi-box-arrow-right me-2"></i>Log Out</a></li>
            </ul>
        </div>
    </aside>

    <!-- Mobile Offcanvas Menu -->
    <div class="offcanvas offcanvas-start bg-dark text-white" tabindex="-1" id="mobileMenu" aria-labelledby="mobileMenuLabel">
        <div class="offcanvas-header border-bottom border-secondary">
            <h5 class="offcanvas-title text-white d-flex align-items-center" id="mobileMenuLabel">
                <i class="bi bi-phone-vibrate text-primary fs-4 me-2"></i> DUKAAN<span class="text-primary">FLOW</span>
            </h5>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="offcanvas" aria-label="Close"></button>
        </div>
        <div class="offcanvas-body p-3">
            <div class="mb-3">
                <a href="{% url 'sales:pos' %}" class="btn btn-primary w-100 fw-bold py-2">
                    <i class="bi bi-cart-plus-fill me-1"></i> New POS Sale
                </a>
            </div>
            <ul class="nav nav-pills flex-column mb-auto">
                <li class="nav-item"><a href="{% url 'dashboard:index' %}" class="nav-link text-white"><i class="bi bi-speedometer2 me-2"></i> Dashboard</a></li>
                <li><a href="{% url 'sales:list' %}" class="nav-link text-white"><i class="bi bi-receipt me-2"></i> Sales & Invoices</a></li>
                <li><a href="{% url 'customers:list' %}" class="nav-link text-white"><i class="bi bi-people me-2"></i> Customers & Khata</a></li>
                <li><a href="{% url 'payments:list' %}" class="nav-link text-white"><i class="bi bi-cash-stack me-2"></i> Payments</a></li>
                <li><a href="{% url 'products:list' %}" class="nav-link text-white"><i class="bi bi-box-seam me-2"></i> Products</a></li>
                <li><a href="{% url 'inventory:imei_list' %}" class="nav-link text-white"><i class="bi bi-upc-scan me-2"></i> IMEI Tracker</a></li>
                <li><a href="{% url 'inventory:imei_search' %}" class="nav-link text-white"><i class="bi bi-search me-2"></i> IMEI Search</a></li>
                <li><a href="{% url 'purchases:list' %}" class="nav-link text-white"><i class="bi bi-bag-check me-2"></i> Purchases</a></li>
                <li><a href="{% url 'suppliers:list' %}" class="nav-link text-white"><i class="bi bi-truck me-2"></i> Suppliers</a></li>
                <li><a href="{% url 'expenses:list' %}" class="nav-link text-white"><i class="bi bi-wallet2 me-2"></i> Expenses</a></li>
                <li><a href="{% url 'reports:index' %}" class="nav-link text-white"><i class="bi bi-graph-up-arrow me-2"></i> Reports & P&L</a></li>
                <li><a href="{% url 'businesses:settings' %}" class="nav-link text-white"><i class="bi bi-gear me-2"></i> Settings</a></li>
                <li><a href="{% url 'businesses:plans' %}" class="nav-link text-warning"><i class="bi bi-stars me-2"></i> Subscription Plans</a></li>
                <li class="mt-3"><a href="{% url 'accounts:logout' %}" class="nav-link text-danger"><i class="bi bi-box-arrow-right me-2"></i> Logout</a></li>
            </ul>
        </div>
    </div>

    <!-- Main Content Area -->
    <div class="main-content d-flex flex-column">
        <!-- Top Navbar -->
        <header class="bg-white border-bottom py-2 px-3 px-lg-4 d-flex align-items-center justify-content-between sticky-top">
            <div class="d-flex align-items-center gap-2">
                <button class="btn btn-outline-secondary d-lg-none" type="button" data-bs-toggle="offcanvas" data-bs-target="#mobileMenu">
                    <i class="bi bi-list fs-5"></i>
                </button>
                <div class="d-flex flex-column">
                    <span class="fw-bold fs-6 text-dark d-none d-sm-inline">{{ current_business.name }}</span>
                    <span class="text-muted small" style="font-size: 0.75rem;"><i class="bi bi-geo-alt"></i> {{ current_business.city|default:"India" }} | GSTIN: {{ current_business.gstin|default:"Unregistered" }}</span>
                </div>
            </div>
            
            <div class="d-flex align-items-center gap-2">
                <a href="{% url 'inventory:imei_search' %}" class="btn btn-light btn-sm border d-none d-md-flex align-items-center gap-1 text-muted">
                    <i class="bi bi-search"></i> Quick IMEI Search
                </a>
                <a href="{% url 'sales:pos' %}" class="btn btn-primary btn-sm fw-bold px-3 d-flex align-items-center gap-1">
                    <i class="bi bi-cart-plus"></i> <span class="d-none d-sm-inline">New</span> Sale
                </a>
            </div>
        </header>

        <!-- Messages Area -->
        <div class="container-fluid px-3 px-lg-4 pt-3">
            {% if messages %}
                {% for message in messages %}
                    <div class="alert alert-{{ message.tags|default:'info' }} alert-dismissible fade show shadow-sm" role="alert">
                        {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    </div>
                {% endfor %}
            {% endif %}
            
            {% block content %}{% endblock %}
        </div>

        <!-- Footer -->
        <footer class="mt-auto py-3 bg-white border-top text-center text-muted small">
            <div class="container-fluid">
                <span>© 2026 <strong>DukaanFlow</strong> — The Smarter Mobile Shop SaaS for Indian Retailers. Made with ❤️ in India.</span>
            </div>
        </footer>
    </div>
</div>
{% else %}
    <!-- Public Layout for Landing, Login, Registration -->
    <div class="min-vh-100 d-flex flex-column">
        {% block public_content %}{% endblock %}
    </div>
{% endif %}

<!-- Bootstrap 5 JS Bundle -->
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
<script src="{% static 'js/main.js' %}"></script>
{% block extra_scripts %}{% endblock %}
</body>
</html>
"""
with open(os.path.join(BASE_DIR, "templates", "base.html"), "w", encoding="utf-8") as f:
    f.write(base_html)

# templates/landing/index.html
landing_html = """{% extends 'base.html' %}
{% load static dukaan_tags %}

{% block title %}DukaanFlow — Run Your Mobile Shop Smarter{% endblock %}

{% block public_content %}
<!-- Navbar -->
<nav class="navbar navbar-expand-lg navbar-dark bg-dark sticky-top py-3">
    <div class="container">
        <a class="navbar-brand fw-bold fs-3" href="{% url 'landing:home' %}">
            <i class="bi bi-phone-vibrate text-primary me-2"></i>DUKAAN<span class="text-primary">FLOW</span>
        </a>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navContent">
            <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="navContent">
            <ul class="navbar-nav ms-auto mb-2 mb-lg-0 align-items-center gap-3">
                <li class="nav-item"><a class="nav-link text-white-50" href="#features">Features</a></li>
                <li class="nav-item"><a class="nav-link text-white-50" href="#how-it-works">How It Works</a></li>
                <li class="nav-item"><a class="nav-link text-white-50" href="#pricing">Pricing</a></li>
                <li class="nav-item"><a class="nav-link text-white-50" href="#faq">FAQ</a></li>
                <li class="nav-item"><a class="btn btn-outline-light btn-sm px-3" href="{% url 'accounts:login' %}">Login</a></li>
                <li class="nav-item"><a class="btn btn-primary btn-sm fw-bold px-4" href="{% url 'accounts:register' %}">Start Free</a></li>
            </ul>
        </div>
    </div>
</nav>

<!-- Hero Section -->
<section class="py-5 bg-dark text-white border-bottom border-secondary text-center text-lg-start">
    <div class="container py-lg-5">
        <div class="row align-items-center">
            <div class="col-lg-7">
                <div class="badge bg-primary-subtle text-primary px-3 py-2 rounded-pill mb-3 fw-bold">
                    🚀 India's #1 Dedicated Mobile Shop Management Platform
                </div>
                <h1 class="display-4 fw-bold lh-1 mb-3">
                    Run your mobile shop <span class="text-primary">smarter</span>, faster & error-free.
                </h1>
                <p class="lead text-secondary mb-4">
                    Replace notebooks and complex spreadsheets. Manage dual IMEI tracking, lightning-fast POS counter billing, customer Udhar/Khata ledgers, stock alerts, GST invoices, and 1-click WhatsApp payment reminders.
                </p>
                <div class="d-flex flex-column flex-sm-row gap-3 justify-content-center justify-content-lg-start">
                    <a href="{% url 'accounts:register' %}" class="btn btn-primary btn-lg fw-bold px-4 py-3 shadow">
                        <i class="bi bi-lightning-charge-fill me-1"></i> Start 100% Free Forever
                    </a>
                    <a href="{% url 'accounts:login' %}" class="btn btn-outline-light btn-lg px-4 py-3">
                        <i class="bi bi-box-arrow-in-right me-1"></i> Existing Shop Login
                    </a>
                </div>
                <div class="mt-4 text-muted small d-flex align-items-center justify-content-center justify-content-lg-start gap-4">
                    <span><i class="bi bi-check-circle-fill text-success me-1"></i> No Credit Card Required</span>
                    <span><i class="bi bi-check-circle-fill text-success me-1"></i> 2-Minute Setup</span>
                    <span><i class="bi bi-check-circle-fill text-success me-1"></i> 100% Data Privacy</span>
                </div>
            </div>
            <div class="col-lg-5 mt-5 mt-lg-0">
                <div class="card bg-secondary bg-opacity-10 border-secondary p-4 shadow-lg text-white">
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <span class="badge bg-success">LIVE POS PREVIEW</span>
                        <span class="text-muted small">Paras Mobile Hub</span>
                    </div>
                    <div class="p-3 bg-dark rounded border border-secondary mb-3">
                        <div class="d-flex justify-content-between">
                            <strong>Samsung Galaxy A56 5G</strong>
                            <span class="text-success fw-bold">₹28,999.00</span>
                        </div>
                        <div class="small text-primary">IMEI: 864521098765432</div>
                    </div>
                    <div class="p-3 bg-dark rounded border border-secondary mb-3">
                        <div class="d-flex justify-content-between">
                            <strong>25W Type-C Super Fast Charger</strong>
                            <span class="text-success fw-bold">₹1,299.00</span>
                        </div>
                    </div>
                    <div class="border-top border-secondary pt-2 d-flex justify-content-between fs-5 fw-bold">
                        <span>Total Payable:</span>
                        <span class="text-warning">₹30,298.00</span>
                    </div>
                    <button class="btn btn-success fw-bold mt-3 w-100 py-2">
                        <i class="bi bi-whatsapp me-2"></i> Print Bill & Send on WhatsApp
                    </button>
                </div>
            </div>
        </div>
    </div>
</section>

<!-- Core Features -->
<section id="features" class="py-5 bg-white">
    <div class="container py-4">
        <div class="text-center max-w-700 mx-auto mb-5">
            <span class="text-primary fw-bold text-uppercase">Built Specifically For Indian Mobile Retailers</span>
            <h2 class="fw-bold mt-2">Everything you need to grow your retail business</h2>
        </div>
        
        <div class="row g-4">
            <div class="col-md-4">
                <div class="card h-100 p-4 border shadow-sm">
                    <div class="stat-icon bg-primary-subtle text-primary mb-3">
                        <i class="bi bi-upc-scan"></i>
                    </div>
                    <h5 class="fw-bold">Dual IMEI & Serial Tracker</h5>
                    <p class="text-muted small">
                        Track every smartphone from purchase to sale. Instantly search any IMEI to find customer details, invoice, and manufacturer warranty status.
                    </p>
                </div>
            </div>
            
            <div class="col-md-4">
                <div class="card h-100 p-4 border shadow-sm">
                    <div class="stat-icon bg-success-subtle text-success mb-3">
                        <i class="bi bi-journal-text"></i>
                    </div>
                    <h5 class="fw-bold">Indian Khata / Udhar Ledger</h5>
                    <p class="text-muted small">
                        Keep exact track of customer credit, partial payments, and overdue balances. Automatically updates balances with zero math mistakes.
                    </p>
                </div>
            </div>
            
            <div class="col-md-4">
                <div class="card h-100 p-4 border shadow-sm">
                    <div class="stat-icon bg-info-subtle text-info mb-3">
                        <i class="bi bi-whatsapp"></i>
                    </div>
                    <h5 class="fw-bold">1-Click WhatsApp Reminders</h5>
                    <p class="text-muted small">
                        Send polite, pre-formatted payment reminders, invoice links, and digital receipts directly to customer WhatsApp with one tap. Zero API charges!
                    </p>
                </div>
            </div>
            
            <div class="col-md-4">
                <div class="card h-100 p-4 border shadow-sm">
                    <div class="stat-icon bg-warning-subtle text-warning mb-3">
                        <i class="bi bi-cart-check"></i>
                    </div>
                    <h5 class="fw-bold">Lightning Fast POS Counter</h5>
                    <p class="text-muted small">
                        Designed for busy shop counters. Complete sales in under 10 seconds with barcode/IMEI scanning, item discounts, and multi-mode payments (Cash, UPI, Card, Udhar).
                    </p>
                </div>
            </div>
            
            <div class="col-md-4">
                <div class="card h-100 p-4 border shadow-sm">
                    <div class="stat-icon bg-danger-subtle text-danger mb-3">
                        <i class="bi bi-calculator"></i>
                    </div>
                    <h5 class="fw-bold">True Gross & Net Profit</h5>
                    <p class="text-muted small">
                        Accurately calculates real profits based on True Cost of Goods Sold (COGS) and operational shop expenses like rent, salaries, and electricity.
                    </p>
                </div>
            </div>
            
            <div class="col-md-4">
                <div class="card h-100 p-4 border shadow-sm">
                    <div class="stat-icon bg-dark-subtle text-dark mb-3">
                        <i class="bi bi-file-earmark-pdf"></i>
                    </div>
                    <h5 class="fw-bold">GST Ready PDF Invoices</h5>
                    <p class="text-muted small">
                        Print beautiful, professional bills with your shop branding, logo, GSTIN, IMEI details, and payment summary on standard A4 or thermal receipt printers.
                    </p>
                </div>
            </div>
        </div>
    </div>
</section>

<!-- Pricing Plans -->
<section id="pricing" class="py-5 bg-light border-top">
    <div class="container py-4">
        <div class="text-center mb-5">
            <span class="text-primary fw-bold text-uppercase">Transparent, Affordable Pricing</span>
            <h2 class="fw-bold mt-2">Pick the plan that fits your shop</h2>
            <p class="text-muted">No hidden fees. Start free and upgrade as your business expands.</p>
        </div>
        
        <div class="row g-4 justify-content-center">
            <!-- Free Plan -->
            <div class="col-lg-4 col-md-6">
                <div class="card h-100 p-4 border shadow-sm">
                    <h4 class="fw-bold">Free Starter</h4>
                    <p class="text-muted small">Perfect for new single-counter mobile shops.</p>
                    <div class="display-5 fw-bold my-3">₹0 <span class="fs-6 text-muted font-monospace">/ month</span></div>
                    <ul class="list-unstyled d-flex flex-column gap-2 mb-4">
                        <li><i class="bi bi-check2-circle text-success me-2"></i> Up to 50 Customers</li>
                        <li><i class="bi bi-check2-circle text-success me-2"></i> Up to 100 Products</li>
                        <li><i class="bi bi-check2-circle text-success me-2"></i> Basic POS Billing</li>
                        <li><i class="bi bi-check2-circle text-success me-2"></i> IMEI Device Tracking</li>
                        <li><i class="bi bi-check2-circle text-success me-2"></i> PDF Invoicing & WhatsApp</li>
                    </ul>
                    <a href="{% url 'accounts:register' %}" class="btn btn-outline-primary fw-bold w-100 mt-auto py-2">Start Free</a>
                </div>
            </div>
            
            <!-- Pro Plan -->
            <div class="col-lg-4 col-md-6">
                <div class="card h-100 p-4 border-primary border-2 shadow position-relative">
                    <div class="position-absolute top-0 end-0 bg-primary text-white small fw-bold px-3 py-1 rounded-bottom-start">MOST POPULAR</div>
                    <h4 class="fw-bold">Pro Merchant</h4>
                    <p class="text-muted small">For growing mobile & electronics retail stores.</p>
                    <div class="display-5 fw-bold text-primary my-3">₹199 <span class="fs-6 text-muted font-monospace">/ month</span></div>
                    <ul class="list-unstyled d-flex flex-column gap-2 mb-4">
                        <li><i class="bi bi-check2-circle text-success me-2"></i> <strong>Unlimited</strong> Customers & Khata</li>
                        <li><i class="bi bi-check2-circle text-success me-2"></i> <strong>Unlimited</strong> Products & Accessories</li>
                        <li><i class="bi bi-check2-circle text-success me-2"></i> Advanced Profit & Loss Analytics</li>
                        <li><i class="bi bi-check2-circle text-success me-2"></i> Full Supplier & Purchase Management</li>
                        <li><i class="bi bi-check2-circle text-success me-2"></i> CSV Excel Data Exports</li>
                    </ul>
                    <a href="{% url 'accounts:register' %}" class="btn btn-primary fw-bold w-100 mt-auto py-2">Get Pro Access</a>
                </div>
            </div>
            
            <!-- Business Plan -->
            <div class="col-lg-4 col-md-6">
                <div class="card h-100 p-4 border shadow-sm">
                    <h4 class="fw-bold">Business Ultra</h4>
                    <p class="text-muted small">For busy retail hubs with staff members.</p>
                    <div class="display-5 fw-bold my-3">₹499 <span class="fs-6 text-muted font-monospace">/ month</span></div>
                    <ul class="list-unstyled d-flex flex-column gap-2 mb-4">
                        <li><i class="bi bi-check2-circle text-success me-2"></i> Everything in Pro Plan</li>
                        <li><i class="bi bi-check2-circle text-success me-2"></i> Up to 10 Multi-User Staff Logins</li>
                        <li><i class="bi bi-check2-circle text-success me-2"></i> Priority Dedicated Support</li>
                        <li><i class="bi bi-check2-circle text-success me-2"></i> Custom Invoice Branding</li>
                    </ul>
                    <a href="{% url 'accounts:register' %}" class="btn btn-outline-dark fw-bold w-100 mt-auto py-2">Get Business Ultra</a>
                </div>
            </div>
        </div>
    </div>
</section>

<!-- FAQ Section -->
<section id="faq" class="py-5 bg-white">
    <div class="container py-4 max-w-800">
        <h2 class="fw-bold text-center mb-5">Frequently Asked Questions</h2>
        <div class="accordion" id="faqAccordion">
            <div class="accordion-item mb-3 border rounded">
                <h2 class="accordion-header">
                    <button class="accordion-button collapsed fw-bold" type="button" data-bs-toggle="collapse" data-bs-target="#faq1">
                        Can other shop owners see my customer or sales data?
                    </button>
                </h2>
                <div id="faq1" class="accordion-collapse collapse" data-bs-parent="#faqAccordion">
                    <div class="accordion-body text-muted">
                        <strong>Never.</strong> DukaanFlow is built with strict multi-tenant database isolation. Every shop's data, IMEI numbers, customers, and financial records are completely private and accessible only by you.
                    </div>
                </div>
            </div>
            
            <div class="accordion-item mb-3 border rounded">
                <h2 class="accordion-header">
                    <button class="accordion-button collapsed fw-bold" type="button" data-bs-toggle="collapse" data-bs-target="#faq2">
                        Do I need a barcode scanner or expensive POS hardware?
                    </button>
                </h2>
                <div id="faq2" class="accordion-collapse collapse" data-bs-parent="#faqAccordion">
                    <div class="accordion-body text-muted">
                        No hardware required! You can use DukaanFlow on your mobile phone, laptop, or desktop computer. You can type or use standard USB barcode scanners directly.
                    </div>
                </div>
            </div>
            
            <div class="accordion-item mb-3 border rounded">
                <h2 class="accordion-header">
                    <button class="accordion-button collapsed fw-bold" type="button" data-bs-toggle="collapse" data-bs-target="#faq3">
                        How does WhatsApp reminder work? Is it free?
                    </button>
                </h2>
                <div id="faq3" class="accordion-collapse collapse" data-bs-parent="#faqAccordion">
                    <div class="accordion-body text-muted">
                        Yes, 100% free! DukaanFlow formats customized polite WhatsApp messages with your shop name, invoice amount, and due balance. Clicking the WhatsApp button opens WhatsApp Web or your phone's WhatsApp app with the message pre-typed.
                    </div>
                </div>
            </div>
        </div>
    </div>
</section>

<!-- CTA Section -->
<section class="py-5 bg-primary text-white text-center">
    <div class="container py-4">
        <h2 class="display-6 fw-bold">Ready to modernize your mobile shop?</h2>
        <p class="lead opacity-75 mb-4">Join thousands of Indian retailers running smarter with DukaanFlow.</p>
        <a href="{% url 'accounts:register' %}" class="btn btn-light btn-lg fw-bold px-5 py-3 shadow">
            Create Free Account Now
        </a>
    </div>
</section>
{% endblock %}
"""
with open(os.path.join(BASE_DIR, "templates", "landing", "index.html"), "w", encoding="utf-8") as f:
    f.write(landing_html)

print("Phase 8a (Base, Landing & Static) created successfully!")
