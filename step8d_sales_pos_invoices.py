import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# static/js/pos.js
pos_js = """
// DukaanFlow POS Engine
let cart = [];

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function formatINR(number) {
    return '₹' + parseFloat(number || 0).toLocaleString('en-IN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

function addToCart(productId, name, price, maxStock, isImeiTracked) {
    price = parseFloat(price);
    const existingIndex = cart.findIndex(item => item.productId === productId && !item.deviceId);
    
    if (isImeiTracked) {
        // Need device selection modal or selector
        const deviceSelect = document.getElementById('device-select-' + productId);
        let selectedDeviceId = null;
        let selectedImei = '';
        if (deviceSelect && deviceSelect.value) {
            selectedDeviceId = deviceSelect.value;
            selectedImei = deviceSelect.options[deviceSelect.selectedIndex].text;
        }
        
        cart.push({
            productId: productId,
            name: name + (selectedImei ? ' (' + selectedImei + ')' : ''),
            unitPrice: price,
            quantity: 1,
            discount: 0,
            maxStock: maxStock,
            deviceId: selectedDeviceId,
            isImeiTracked: true
        });
    } else {
        if (existingIndex > -1) {
            if (cart[existingIndex].quantity < maxStock) {
                cart[existingIndex].quantity += 1;
            } else {
                alert('Maximum available stock reached for this item (' + maxStock + ')');
                return;
            }
        } else {
            cart.push({
                productId: productId,
                name: name,
                unitPrice: price,
                quantity: 1,
                discount: 0,
                maxStock: maxStock,
                deviceId: null,
                isImeiTracked: false
            });
        }
    }
    
    renderCart();
}

function updateQuantity(index, newQty) {
    newQty = parseInt(newQty);
    if (newQty <= 0) {
        removeFromCart(index);
        return;
    }
    if (newQty > cart[index].maxStock && !cart[index].isImeiTracked) {
        alert('Cannot exceed stock of ' + cart[index].maxStock);
        newQty = cart[index].maxStock;
    }
    cart[index].quantity = newQty;
    renderCart();
}

function updateItemDiscount(index, disc) {
    disc = parseFloat(disc) || 0;
    cart[index].discount = disc;
    renderCart();
}

function removeFromCart(index) {
    cart.splice(index, 1);
    renderCart();
}

function clearCart() {
    cart = [];
    renderCart();
}

function renderCart() {
    const tbody = document.getElementById('cart-table-body');
    const emptyState = document.getElementById('cart-empty-state');
    const cartWrapper = document.getElementById('cart-content-wrapper');
    
    if (!tbody) return;
    
    if (cart.length === 0) {
        tbody.innerHTML = '';
        if (emptyState) emptyState.classList.remove('d-none');
        if (cartWrapper) cartWrapper.classList.add('d-none');
        updateTotals();
        return;
    }
    
    if (emptyState) emptyState.classList.add('d-none');
    if (cartWrapper) cartWrapper.classList.remove('d-none');
    
    let html = '';
    cart.forEach((item, index) => {
        const itemTotal = Math.max(0, (item.unitPrice * item.quantity) - item.discount);
        html += `
            <tr>
                <td>
                    <div class="fw-bold">${item.name}</div>
                    <div class="text-muted small">${formatINR(item.unitPrice)} each</div>
                </td>
                <td style="width: 100px;">
                    ${item.isImeiTracked ? 
                        `<span class="badge bg-secondary">1 unit</span>` : 
                        `<input type="number" min="1" max="${item.maxStock}" class="form-control form-control-sm text-center" value="${item.quantity}" onchange="updateQuantity(${index}, this.value)">`
                    }
                </td>
                <td style="width: 90px;">
                    <input type="number" min="0" step="1" class="form-control form-control-sm text-end" value="${item.discount}" onchange="updateItemDiscount(${index}, this.value)">
                </td>
                <td class="text-end fw-bold">${formatINR(itemTotal)}</td>
                <td class="text-center" style="width: 40px;">
                    <button class="btn btn-outline-danger btn-sm p-1" onclick="removeFromCart(${index})"><i class="bi bi-trash"></i></button>
                </td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html;
    updateTotals();
}

function updateTotals() {
    let subtotal = 0;
    cart.forEach(item => {
        subtotal += Math.max(0, (item.unitPrice * item.quantity) - item.discount);
    });
    
    const extraDisc = parseFloat(document.getElementById('pos-discount')?.value || 0);
    const taxAmt = parseFloat(document.getElementById('pos-tax')?.value || 0);
    
    const grandTotal = Math.max(0, (subtotal - extraDisc) + taxAmt);
    
    const subtotalEl = document.getElementById('pos-subtotal');
    const grandTotalEl = document.getElementById('pos-grand-total');
    const grandTotalModalEl = document.getElementById('modal-grand-total');
    const paidInput = document.getElementById('pos-paid-amount');
    
    if (subtotalEl) subtotalEl.innerText = formatINR(subtotal);
    if (grandTotalEl) grandTotalEl.innerText = formatINR(grandTotal);
    if (grandTotalModalEl) grandTotalModalEl.innerText = formatINR(grandTotal);
    
    // Auto sync paid amount if cash/upi/card
    const method = document.getElementById('pos-payment-method')?.value;
    if (paidInput) {
        if (method === 'CREDIT') {
            paidInput.value = '0';
        } else if (paidInput.getAttribute('data-manual') !== 'true') {
            paidInput.value = grandTotal.toFixed(2);
        }
        calculateDue(grandTotal);
    }
}

function calculateDue(grandTotal) {
    const paid = parseFloat(document.getElementById('pos-paid-amount')?.value || 0);
    const due = Math.max(0, grandTotal - paid);
    const dueEl = document.getElementById('pos-due-amount');
    if (dueEl) {
        dueEl.innerText = formatINR(due);
        if (due > 0) {
            dueEl.className = 'text-danger fw-bold';
        } else {
            dueEl.className = 'text-success fw-bold';
        }
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const paidInput = document.getElementById('pos-paid-amount');
    if (paidInput) {
        paidInput.addEventListener('input', function() {
            paidInput.setAttribute('data-manual', 'true');
            updateTotals();
        });
    }
    
    const discInput = document.getElementById('pos-discount');
    if (discInput) discInput.addEventListener('input', updateTotals);
    
    const taxInput = document.getElementById('pos-tax');
    if (taxInput) taxInput.addEventListener('input', updateTotals);
    
    const methodSelect = document.getElementById('pos-payment-method');
    if (methodSelect) {
        methodSelect.addEventListener('change', function() {
            if (this.value === 'CREDIT') {
                if (paidInput) paidInput.value = '0';
            } else {
                if (paidInput) paidInput.removeAttribute('data-manual');
            }
            updateTotals();
        });
    }
    
    // Product Search Filter in POS
    const searchInput = document.getElementById('pos-search-product');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const val = this.value.toLowerCase().trim();
            const cards = document.querySelectorAll('.pos-product-item');
            cards.forEach(card => {
                const name = card.getAttribute('data-name').toLowerCase();
                const sku = card.getAttribute('data-sku').toLowerCase();
                if (name.includes(val) || sku.includes(val)) {
                    card.classList.remove('d-none');
                } else {
                    card.classList.add('d-none');
                }
            });
        });
    }
});

async function submitPOSCheckout() {
    if (cart.length === 0) {
        alert('Cart is empty. Please add items to checkout.');
        return;
    }
    
    const customerId = document.getElementById('pos-customer-select')?.value;
    const newCustName = document.getElementById('new-cust-name')?.value;
    const newCustPhone = document.getElementById('new-cust-phone')?.value;
    const paymentMethod = document.getElementById('pos-payment-method')?.value;
    const discount = document.getElementById('pos-discount')?.value || 0;
    const tax = document.getElementById('pos-tax')?.value || 0;
    const paidAmount = document.getElementById('pos-paid-amount')?.value || 0;
    const notes = document.getElementById('pos-notes')?.value || '';
    
    const payload = {
        customer_id: customerId || null,
        new_customer_name: newCustName || '',
        new_customer_phone: newCustPhone || '',
        payment_method: paymentMethod,
        discount: discount,
        tax: tax,
        paid_amount: paidAmount,
        notes: notes,
        items: cart.map(item => ({
            product_id: item.productId,
            quantity: item.quantity,
            unit_price: item.unitPrice,
            discount: item.discount,
            device_id: item.deviceId
        }))
    };
    
    const btn = document.getElementById('btn-complete-sale');
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Processing...';
    }
    
    try {
        const response = await fetch('/sales/api/checkout/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(payload)
        });
        
        const data = await response.json();
        if (data.success) {
            // Show Success Modal
            const modalEl = document.getElementById('checkoutSuccessModal');
            if (modalEl) {
                document.getElementById('success-invoice-no').innerText = '#' + data.invoice_number;
                document.getElementById('success-total-amt').innerText = formatINR(data.total_amount);
                document.getElementById('success-paid-amt').innerText = formatINR(data.paid_amount);
                document.getElementById('success-due-amt').innerText = formatINR(data.due_amount);
                document.getElementById('success-view-btn').href = data.invoice_url;
                document.getElementById('success-print-btn').href = data.print_url;
                
                const bsModal = new bootstrap.Modal(modalEl);
                bsModal.show();
            } else {
                window.location.href = data.invoice_url;
            }
            clearCart();
        } else {
            alert('Error: ' + (data.error || 'Failed to complete transaction'));
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = '<i class="bi bi-check2-circle me-1"></i> Complete Sale & Bill';
            }
        }
    } catch (err) {
        alert('Network or server error: ' + err.message);
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-check2-circle me-1"></i> Complete Sale & Bill';
        }
    }
}
"""
with open(os.path.join(BASE_DIR, "static", "js", "pos.js"), "w", encoding="utf-8") as f:
    f.write(pos_js)

# templates/sales/pos.html
pos_html = """{% extends 'base.html' %}
{% load static dukaan_tags %}

{% block title %}POS Billing Counter — {{ current_business.name }}{% endblock %}

{% block content %}
<div class="row g-3">
    <!-- Left Column: Product Selection Catalog -->
    <div class="col-lg-7">
        <div class="card h-100">
            <div class="card-header p-3">
                <div class="input-group">
                    <span class="input-group-text bg-light"><i class="bi bi-search"></i></span>
                    <input type="text" id="pos-search-product" class="form-control" placeholder="Search phone, charger, brand or scan barcode..." autofocus>
                </div>
            </div>
            <div class="card-body p-3" style="max-height: calc(100vh - 200px); overflow-y: auto;">
                <div class="row g-2" id="pos-product-grid">
                    {% for p in products %}
                        <div class="col-sm-6 col-md-4 pos-product-item" data-name="{{ p.name }} {{ p.brand }}" data-sku="{{ p.sku|default:'' }} {{ p.barcode|default:'' }}">
                            <div class="card h-100 p-2 border hover-shadow" style="cursor: pointer;">
                                <div class="fw-bold small text-truncate" title="{{ p.name }}">{{ p.name }}</div>
                                <div class="d-flex justify-content-between align-items-center mt-1">
                                    <span class="text-primary fw-bold">{{ p.selling_price|inr }}</span>
                                    <span class="badge {% if p.stock_quantity <= p.min_stock %}bg-warning text-dark{% else %}bg-light text-dark border{% endif %} small">
                                        {{ p.stock_quantity }} left
                                    </span>
                                </div>

                                {% if p.is_imei_tracked %}
                                    <div class="mt-2">
                                        <select class="form-select form-select-sm" id="device-select-{{ p.id }}" onclick="event.stopPropagation();">
                                            <option value="">-- Pick IMEI --</option>
                                            {% for dev in available_devices %}
                                                {% if dev.product_id == p.id %}
                                                    <option value="{{ dev.id }}">{{ dev.imei_1 }}</option>
                                                {% endif %}
                                            {% endfor %}
                                        </select>
                                    </div>
                                {% endif %}

                                <button class="btn btn-outline-primary btn-sm fw-bold mt-2 w-100" onclick="addToCart({{ p.id }}, '{{ p.name|escapejs }}', {{ p.selling_price }}, {{ p.stock_quantity }}, {{ p.is_imei_tracked|lower }})">
                                    <i class="bi bi-plus-lg"></i> Add
                                </button>
                            </div>
                        </div>
                    {% empty %}
                        <div class="col-12 text-center py-5 text-muted">
                            <i class="bi bi-box-seam fs-2 d-block mb-2"></i>
                            No products available in stock. <a href="{% url 'products:create' %}">Add products</a> or <a href="{% url 'purchases:create' %}">receive purchase</a>.
                        </div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>

    <!-- Right Column: Live Billing Cart & Checkout -->
    <div class="col-lg-5">
        <div class="card h-100 d-flex flex-column">
            <!-- Customer Selection Header -->
            <div class="card-header p-3 bg-light">
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <label class="form-label small fw-bold mb-0"><i class="bi bi-person-fill me-1"></i>Customer</label>
                    <button class="btn btn-link btn-sm p-0 text-decoration-none" data-bs-toggle="collapse" data-bs-target="#newCustCollapse">
                        + Quick New Customer
                    </button>
                </div>
                <select id="pos-customer-select" class="form-select form-select-sm">
                    <option value="">-- Cash / Walk-in Customer --</option>
                    {% for c in customers %}
                        <option value="{{ c.id }}">{{ c.name }} ({{ c.phone }})</option>
                    {% endfor %}
                </select>

                <!-- Quick New Customer Fields (Collapsible) -->
                <div class="collapse mt-2" id="newCustCollapse">
                    <div class="p-2 bg-white rounded border">
                        <div class="row g-2">
                            <div class="col-6">
                                <input type="text" id="new-cust-name" class="form-control form-control-sm" placeholder="Customer Name">
                            </div>
                            <div class="col-6">
                                <input type="text" id="new-cust-phone" class="form-control form-control-sm" placeholder="10-digit Mobile">
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Cart Items Table Area -->
            <div class="card-body p-0 flex-grow-1" style="max-height: 250px; overflow-y: auto;">
                <div id="cart-empty-state" class="text-center py-5 text-muted">
                    <i class="bi bi-cart3 fs-1 d-block mb-1 opacity-50"></i>
                    Cart is empty. Click items from catalog to add.
                </div>
                <div id="cart-content-wrapper" class="d-none">
                    <table class="table table-sm align-middle mb-0">
                        <thead class="bg-light">
                            <tr>
                                <th>Item</th>
                                <th class="text-center">Qty</th>
                                <th class="text-end">Disc(₹)</th>
                                <th class="text-end">Total</th>
                                <th></th>
                            </tr>
                        </thead>
                        <tbody id="cart-table-body"></tbody>
                    </table>
                </div>
            </div>

            <!-- Checkout Financial Summary Footer -->
            <div class="card-footer p-3 bg-white border-top">
                <div class="d-flex justify-content-between small text-muted mb-1">
                    <span>Subtotal:</span>
                    <span id="pos-subtotal" class="fw-bold text-dark">₹0.00</span>
                </div>
                <div class="row g-2 mb-2">
                    <div class="col-6">
                        <div class="input-group input-group-sm">
                            <span class="input-group-text small">Disc ₹</span>
                            <input type="number" id="pos-discount" class="form-control form-control-sm" value="0" min="0">
                        </div>
                    </div>
                    <div class="col-6">
                        <div class="input-group input-group-sm">
                            <span class="input-group-text small">GST ₹</span>
                            <input type="number" id="pos-tax" class="form-control form-control-sm" value="0" min="0">
                        </div>
                    </div>
                </div>

                <div class="d-flex justify-content-between fs-5 fw-bold text-dark border-top pt-2 mb-2">
                    <span>Grand Total:</span>
                    <span id="pos-grand-total" class="text-primary">₹0.00</span>
                </div>

                <div class="row g-2 mb-2">
                    <div class="col-6">
                        <label class="small fw-bold">Payment Method</label>
                        <select id="pos-payment-method" class="form-select form-select-sm">
                            <option value="CASH">Cash</option>
                            <option value="UPI">UPI (GPay/PhonePe)</option>
                            <option value="CARD">Debit/Credit Card</option>
                            <option value="BANK">Bank Transfer</option>
                            <option value="CREDIT">Customer Khata (Udhar)</option>
                        </select>
                    </div>
                    <div class="col-6">
                        <label class="small fw-bold">Paid Amount (₹)</label>
                        <input type="number" id="pos-paid-amount" class="form-control form-control-sm fw-bold text-success" step="0.01" value="0">
                    </div>
                </div>

                <div class="d-flex justify-content-between small mb-3">
                    <span class="text-muted">Balance Due (Khata):</span>
                    <span id="pos-due-amount" class="fw-bold">₹0.00</span>
                </div>

                <div class="d-flex gap-2">
                    <button class="btn btn-outline-secondary btn-sm" onclick="clearCart()"><i class="bi bi-trash"></i></button>
                    <button id="btn-complete-sale" class="btn btn-primary fw-bold flex-grow-1 py-2 shadow-sm" onclick="submitPOSCheckout()">
                        <i class="bi bi-check2-circle me-1"></i> Complete Sale & Bill
                    </button>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Modal: Checkout Success Confirmation -->
<div class="modal fade" id="checkoutSuccessModal" data-bs-backdrop="static" tabindex="-1">
    <div class="modal-dialog modal-dialog-centered">
        <div class="card modal-content p-4 text-center">
            <div class="stat-icon bg-success-subtle text-success mx-auto mb-3" style="width: 60px; height: 60px; font-size: 2rem;">
                <i class="bi bi-check2"></i>
            </div>
            <h4 class="fw-bold">Sale Completed Successfully!</h4>
            <div class="text-muted mb-3">Invoice <strong id="success-invoice-no">#INV-1001</strong> generated.</div>
            
            <div class="p-3 bg-light rounded border mb-4 text-start">
                <div class="d-flex justify-content-between mb-1">
                    <span>Grand Total:</span>
                    <strong id="success-total-amt">₹0.00</strong>
                </div>
                <div class="d-flex justify-content-between text-success mb-1">
                    <span>Paid:</span>
                    <strong id="success-paid-amt">₹0.00</strong>
                </div>
                <div class="d-flex justify-content-between text-danger">
                    <span>Balance Due:</span>
                    <strong id="success-due-amt">₹0.00</strong>
                </div>
            </div>

            <div class="d-grid gap-2">
                <a id="success-view-btn" href="#" class="btn btn-primary fw-bold py-2"><i class="bi bi-file-earmark-pdf me-1"></i> View & Download Invoice</a>
                <a id="success-print-btn" href="#" target="_blank" class="btn btn-outline-secondary py-2"><i class="bi bi-printer me-1"></i> Instant Print Thermal Bill</a>
                <button type="button" class="btn btn-light border py-2" data-bs-dismiss="modal" onclick="window.location.reload();">Next Sale</button>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_scripts %}
<script src="{% static 'js/pos.js' %}"></script>
{% endblock %}
"""
with open(os.path.join(BASE_DIR, "templates", "sales", "pos.html"), "w", encoding="utf-8") as f:
    f.write(pos_html)

# templates/sales/sale_list.html
sale_list_html = """{% extends 'base.html' %}
{% load dukaan_tags %}

{% block title %}Sales History — {{ current_business.name }}{% endblock %}

{% block content %}
<div class="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2">
    <div>
        <h4 class="fw-bold mb-0">Sales Orders & Invoices</h4>
        <span class="text-muted small">Complete invoice records and billing transactions</span>
    </div>
    <a href="{% url 'sales:pos' %}" class="btn btn-primary fw-bold"><i class="bi bi-cart-plus-fill me-1"></i> New Sale</a>
</div>

<div class="card p-3 mb-3">
    <form method="get" class="row g-2">
        <div class="col-md-6">
            <div class="input-group">
                <span class="input-group-text"><i class="bi bi-search"></i></span>
                <input type="text" name="q" class="form-control" placeholder="Search by Invoice #, Customer name or phone..." value="{{ query }}">
            </div>
        </div>
        <div class="col-md-3">
            <select name="status" class="form-select">
                <option value="">All Payment Statuses</option>
                <option value="PAID" {% if status_filter == 'PAID' %}selected{% endif %}>Paid</option>
                <option value="PARTIAL" {% if status_filter == 'PARTIAL' %}selected{% endif %}>Partial</option>
                <option value="UNPAID" {% if status_filter == 'UNPAID' %}selected{% endif %}>Credit / Unpaid</option>
            </select>
        </div>
        <div class="col-md-3 d-flex gap-2">
            <button type="submit" class="btn btn-secondary flex-grow-1">Filter</button>
            <a href="{% url 'sales:list' %}" class="btn btn-outline-secondary">Reset</a>
        </div>
    </form>
</div>

<div class="card">
    <div class="table-responsive">
        <table class="table table-hover mb-0">
            <thead>
                <tr>
                    <th>Invoice No</th>
                    <th>Date & Time</th>
                    <th>Customer</th>
                    <th>Total (₹)</th>
                    <th>Paid (₹)</th>
                    <th>Due (₹)</th>
                    <th>Status</th>
                    <th class="text-end">Actions</th>
                </tr>
            </thead>
            <tbody>
                {% for s in page_obj %}
                    <tr>
                        <td class="fw-bold text-primary">#{{ s.invoice_number }}</td>
                        <td class="small">{{ s.sale_date|date:"d-m-Y H:i" }}</td>
                        <td>
                            <a href="{% url 'customers:detail' s.customer.pk %}" class="text-decoration-none fw-bold">{{ s.customer.name }}</a>
                            <div class="text-muted small">{{ s.customer.phone }}</div>
                        </td>
                        <td class="fw-bold">{{ s.total_amount|inr }}</td>
                        <td class="text-success">{{ s.paid_amount|inr }}</td>
                        <td>
                            {% if s.due_amount > 0 %}
                                <span class="inr-badge-due">{{ s.due_amount|inr }}</span>
                            {% else %}
                                <span class="badge bg-success-subtle text-success">₹0.00</span>
                            {% endif %}
                        </td>
                        <td>
                            {% if s.payment_status == 'PAID' %}
                                <span class="badge bg-success">Paid</span>
                            {% elif s.payment_status == 'PARTIAL' %}
                                <span class="badge bg-warning text-dark">Partial</span>
                            {% else %}
                                <span class="badge bg-danger">Credit</span>
                            {% endif %}
                        </td>
                        <td class="text-end">
                            <div class="btn-group btn-group-sm">
                                <a href="{% url 'invoices:detail' s.pk %}" class="btn btn-outline-secondary" title="View Invoice"><i class="bi bi-eye"></i></a>
                                <a href="{% url 'invoices:pdf' s.pk %}" class="btn btn-outline-secondary" title="Download PDF"><i class="bi bi-file-earmark-pdf"></i></a>
                                <a href="{% url 'invoices:print' s.pk %}" target="_blank" class="btn btn-outline-secondary" title="Print Bill"><i class="bi bi-printer"></i></a>
                            </div>
                        </td>
                    </tr>
                {% empty %}
                    <tr><td colspan="8" class="text-center py-4 text-muted">No sales orders found.</td></tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% endblock %}
"""
with open(os.path.join(BASE_DIR, "templates", "sales", "sale_list.html"), "w", encoding="utf-8") as f:
    f.write(sale_list_html)

# templates/sales/sale_detail.html
sale_detail_html = """{% extends 'base.html' %}
{% load dukaan_tags %}

{% block title %}Invoice #{{ sale.invoice_number }} — {{ current_business.name }}{% endblock %}

{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
    <div>
        <a href="{% url 'sales:list' %}" class="text-muted text-decoration-none small"><i class="bi bi-arrow-left"></i> Back to Sales</a>
        <h4 class="fw-bold mb-0 mt-1">Invoice #{{ sale.invoice_number }}</h4>
        <span class="text-muted small">Date: {{ sale.sale_date|date:"d-m-Y H:i" }} | Customer: <strong>{{ sale.customer.name }}</strong></span>
    </div>
    <div class="d-flex gap-2">
        <a href="{% url 'invoices:pdf' sale.pk %}" class="btn btn-outline-secondary"><i class="bi bi-download me-1"></i> PDF</a>
        <a href="{% url 'invoices:print' sale.pk %}" target="_blank" class="btn btn-secondary"><i class="bi bi-printer me-1"></i> Print</a>
        <a href="{% url 'invoices:detail' sale.pk %}" class="btn btn-primary fw-bold"><i class="bi bi-receipt me-1"></i> View Full Bill</a>
    </div>
</div>
{% endblock %}
"""
with open(os.path.join(BASE_DIR, "templates", "sales", "sale_detail.html"), "w", encoding="utf-8") as f:
    f.write(sale_detail_html)

# templates/purchases/purchase_list.html
purchase_list_html = """{% extends 'base.html' %}
{% load dukaan_tags %}

{% block title %}Stock Purchases — {{ current_business.name }}{% endblock %}

{% block content %}
<div class="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2">
    <div>
        <h4 class="fw-bold mb-0">Supplier Purchase Orders</h4>
        <span class="text-muted small">Inward stock receiving and vendor billing</span>
    </div>
    <a href="{% url 'purchases:create' %}" class="btn btn-primary fw-bold"><i class="bi bi-plus-circle-fill me-1"></i> Inward Purchase</a>
</div>

<div class="card">
    <div class="table-responsive">
        <table class="table table-hover mb-0">
            <thead>
                <tr>
                    <th>Bill / PO #</th>
                    <th>Date</th>
                    <th>Supplier</th>
                    <th>Total (₹)</th>
                    <th>Paid (₹)</th>
                    <th>Due (₹)</th>
                    <th>Payment Mode</th>
                    <th class="text-end">Actions</th>
                </tr>
            </thead>
            <tbody>
                {% for p in page_obj %}
                    <tr>
                        <td class="fw-bold text-primary">#{{ p.invoice_number }}</td>
                        <td>{{ p.purchase_date|date:"d-m-Y" }}</td>
                        <td>
                            <a href="{% url 'suppliers:detail' p.supplier.pk %}" class="text-decoration-none fw-bold">{{ p.supplier.company_name }}</a>
                        </td>
                        <td class="fw-bold">{{ p.total_amount|inr }}</td>
                        <td class="text-success">{{ p.paid_amount|inr }}</td>
                        <td>
                            {% if p.due_amount > 0 %}
                                <span class="inr-badge-due">{{ p.due_amount|inr }}</span>
                            {% else %}
                                <span class="badge bg-success-subtle text-success">Cleared</span>
                            {% endif %}
                        </td>
                        <td><span class="badge bg-light text-dark border">{{ p.get_payment_method_display }}</span></td>
                        <td class="text-end">
                            <a href="{% url 'purchases:detail' p.pk %}" class="btn btn-outline-secondary btn-sm"><i class="bi bi-eye"></i></a>
                        </td>
                    </tr>
                {% empty %}
                    <tr><td colspan="8" class="text-center py-4 text-muted">No purchase orders registered.</td></tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% endblock %}
"""
with open(os.path.join(BASE_DIR, "templates", "purchases", "purchase_list.html"), "w", encoding="utf-8") as f:
    f.write(purchase_list_html)

# templates/purchases/purchase_form.html
purchase_form_html = """{% extends 'base.html' %}

{% block title %}New Stock Purchase — {{ current_business.name }}{% endblock %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-lg-9">
        <div class="card p-4 shadow-sm">
            <h5 class="fw-bold mb-3 border-bottom pb-2"><i class="bi bi-bag-plus text-primary me-2"></i>Inward Stock Purchase Order</h5>
            <form method="post" id="purchaseForm">
                {% csrf_token %}
                <div class="row g-3 mb-3">
                    <div class="col-md-6">
                        <label class="form-label small fw-bold">Supplier / Distributor *</label>
                        <select name="supplier" class="form-select" required>
                            <option value="">-- Select Supplier --</option>
                            {% for s in suppliers %}
                                <option value="{{ s.id }}">{{ s.company_name }} ({{ s.name }})</option>
                            {% endfor %}
                        </select>
                    </div>
                    <div class="col-md-3">
                        <label class="form-label small fw-bold">Supplier Bill / Invoice #</label>
                        <input type="text" name="invoice_number" class="form-control" placeholder="e.g. BILL-9872">
                    </div>
                    <div class="col-md-3">
                        <label class="form-label small fw-bold">Purchase Date *</label>
                        <input type="date" name="purchase_date" class="form-control" value="{{ today|date:'Y-m-d' }}" required>
                    </div>
                </div>

                <div class="card p-3 mb-3 bg-light border">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <span class="fw-bold small">Purchased Items & Quantities</span>
                        <button type="button" class="btn btn-outline-primary btn-sm fw-bold" onclick="addPurchaseRow()">+ Add Item</button>
                    </div>
                    <table class="table table-sm align-middle mb-0" id="purchaseItemsTable">
                        <thead>
                            <tr>
                                <th>Product</th>
                                <th style="width: 120px;">Qty</th>
                                <th style="width: 150px;">Unit Cost (₹)</th>
                                <th style="width: 40px;"></th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>
                                    <select name="product_id[]" class="form-select form-select-sm" required>
                                        <option value="">-- Choose Product --</option>
                                        {% for p in products %}
                                            <option value="{{ p.id }}">{{ p.name }} (Current Stock: {{ p.stock_quantity }})</option>
                                        {% endfor %}
                                    </select>
                                </td>
                                <td><input type="number" name="quantity[]" min="1" value="1" class="form-control form-control-sm" required></td>
                                <td><input type="number" name="unit_cost[]" step="0.01" min="0" placeholder="0.00" class="form-control form-control-sm" required></td>
                                <td><button type="button" class="btn btn-outline-danger btn-sm p-1" onclick="this.closest('tr').remove()"><i class="bi bi-trash"></i></button></td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <div class="row g-3 mb-3">
                    <div class="col-md-6">
                        <label class="form-label small fw-bold">Payment Method</label>
                        <select name="payment_method" class="form-select">
                            <option value="CASH">Cash</option>
                            <option value="UPI">UPI / Online</option>
                            <option value="BANK">Bank Transfer / NEFT</option>
                            <option value="CREDIT">Supplier Credit (Khata)</option>
                        </select>
                    </div>
                    <div class="col-md-6">
                        <label class="form-label small fw-bold">Amount Paid Now (₹)</label>
                        <input type="number" name="paid_amount" step="0.01" min="0" value="0" class="form-control">
                    </div>
                </div>

                <div class="mb-4">
                    <label class="form-label small fw-bold">Notes / Transport details</label>
                    <textarea name="notes" class="form-control" rows="2"></textarea>
                </div>

                <div class="d-flex gap-2">
                    <button type="submit" class="btn btn-primary fw-bold px-4 py-2">Save Purchase & Add Stock</button>
                    <a href="{% url 'purchases:list' %}" class="btn btn-light border">Cancel</a>
                </div>
            </form>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_scripts %}
<script>
function addPurchaseRow() {
    const table = document.getElementById('purchaseItemsTable').getElementsByTagName('tbody')[0];
    const row = table.rows[0].cloneNode(true);
    row.querySelector('select').value = '';
    row.querySelectorAll('input')[0].value = '1';
    row.querySelectorAll('input')[1].value = '';
    table.appendChild(row);
}
</script>
{% endblock %}
"""
with open(os.path.join(BASE_DIR, "templates", "purchases", "purchase_form.html"), "w", encoding="utf-8") as f:
    f.write(purchase_form_html)

# templates/purchases/purchase_detail.html
purchase_detail_html = """{% extends 'base.html' %}
{% load dukaan_tags %}

{% block title %}Purchase #{{ purchase.invoice_number }} — Details{% endblock %}

{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
    <div>
        <a href="{% url 'purchases:list' %}" class="text-muted text-decoration-none small"><i class="bi bi-arrow-left"></i> Back to Purchases</a>
        <h4 class="fw-bold mb-0 mt-1">Purchase Order #{{ purchase.invoice_number }}</h4>
        <span class="text-muted small">Supplier: <strong>{{ purchase.supplier.company_name }}</strong> | Date: {{ purchase.purchase_date|date:"d-m-Y" }}</span>
    </div>
</div>

<div class="row g-3 mb-4">
    <div class="col-md-4">
        <div class="card p-3">
            <div class="text-muted small fw-bold">TOTAL PURCHASE AMOUNT</div>
            <div class="fs-4 fw-bold text-dark">{{ purchase.total_amount|inr }}</div>
        </div>
    </div>
    <div class="col-md-4">
        <div class="card p-3">
            <div class="text-muted small fw-bold">AMOUNT PAID</div>
            <div class="fs-4 fw-bold text-success">{{ purchase.paid_amount|inr }}</div>
        </div>
    </div>
    <div class="col-md-4">
        <div class="card p-3">
            <div class="text-muted small fw-bold">SUPPLIER DUE</div>
            <div class="fs-4 fw-bold text-danger">{{ purchase.due_amount|inr }}</div>
        </div>
    </div>
</div>

<div class="card">
    <div class="card-header fw-bold">Received Line Items</div>
    <div class="table-responsive">
        <table class="table table-hover mb-0">
            <thead>
                <tr>
                    <th>Product</th>
                    <th>Quantity</th>
                    <th>Unit Cost (₹)</th>
                    <th>Total Cost (₹)</th>
                </tr>
            </thead>
            <tbody>
                {% for item in items %}
                    <tr>
                        <td class="fw-bold">{{ item.product.name }}</td>
                        <td>{{ item.quantity }}</td>
                        <td>{{ item.unit_cost|inr }}</td>
                        <td class="fw-bold">{{ item.total_cost|inr }}</td>
                    </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% endblock %}
"""
with open(os.path.join(BASE_DIR, "templates", "purchases", "purchase_detail.html"), "w", encoding="utf-8") as f:
    f.write(purchase_detail_html)

# templates/suppliers/supplier_list.html
supplier_list_html = """{% extends 'base.html' %}
{% load dukaan_tags %}

{% block title %}Suppliers & Distributors — {{ current_business.name }}{% endblock %}

{% block content %}
<div class="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2">
    <div>
        <h4 class="fw-bold mb-0">Suppliers & Distributors</h4>
        <span class="text-muted small">Total Vendor Payable: <strong class="text-warning">{{ total_payable|inr }}</strong></span>
    </div>
    <a href="{% url 'suppliers:create' %}" class="btn btn-primary fw-bold"><i class="bi bi-truck me-1"></i> Add Supplier</a>
</div>

<div class="card">
    <div class="table-responsive">
        <table class="table table-hover mb-0">
            <thead>
                <tr>
                    <th>Company / Distributor</th>
                    <th>Contact Person</th>
                    <th>Phone</th>
                    <th>Total Purchases</th>
                    <th>Total Paid</th>
                    <th>Balance Due</th>
                    <th class="text-end">Actions</th>
                </tr>
            </thead>
            <tbody>
                {% for s in page_obj %}
                    <tr>
                        <td class="fw-bold text-dark">{{ s.company_name }}</td>
                        <td>{{ s.name }}</td>
                        <td>{{ s.phone }}</td>
                        <td class="fw-bold">{{ s.total_purchases|inr }}</td>
                        <td class="text-success">{{ s.total_paid_amt|inr }}</td>
                        <td>
                            {% if s.due_amt > 0 %}
                                <span class="inr-badge-due">{{ s.due_amt|inr }}</span>
                            {% else %}
                                <span class="badge bg-success-subtle text-success">Cleared</span>
                            {% endif %}
                        </td>
                        <td class="text-end">
                            <div class="btn-group btn-group-sm">
                                <a href="{% url 'payments:supplier_add' %}?supplier={{ s.pk }}" class="btn btn-outline-success" title="Pay Supplier"><i class="bi bi-cash"></i> Pay</a>
                                <a href="{% url 'suppliers:detail' s.pk %}" class="btn btn-outline-secondary"><i class="bi bi-eye"></i></a>
                                <a href="{% url 'suppliers:update' s.pk %}" class="btn btn-outline-secondary"><i class="bi bi-pencil"></i></a>
                            </div>
                        </td>
                    </tr>
                {% empty %}
                    <tr><td colspan="7" class="text-center py-4 text-muted">No suppliers added yet.</td></tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% endblock %}
"""
with open(os.path.join(BASE_DIR, "templates", "suppliers", "supplier_list.html"), "w", encoding="utf-8") as f:
    f.write(supplier_list_html)

# templates/suppliers/supplier_form.html
supplier_form_html = """{% extends 'base.html' %}

{% block title %}{{ title }} — {{ current_business.name }}{% endblock %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-lg-6">
        <div class="card p-4 shadow-sm">
            <h5 class="fw-bold mb-3 border-bottom pb-2"><i class="bi bi-truck text-primary me-2"></i>{{ title }}</h5>
            <form method="post">
                {% csrf_token %}
                <div class="mb-3">
                    <label class="form-label small fw-bold">Company / Distributor Name *</label>
                    {{ form.company_name }}
                </div>
                <div class="row g-2 mb-3">
                    <div class="col-md-6">
                        <label class="form-label small fw-bold">Contact Person *</label>
                        {{ form.name }}
                    </div>
                    <div class="col-md-6">
                        <label class="form-label small fw-bold">Phone Number *</label>
                        {{ form.phone }}
                    </div>
                </div>
                <div class="row g-2 mb-3">
                    <div class="col-md-6">
                        <label class="form-label small fw-bold">Email</label>
                        {{ form.email }}
                    </div>
                    <div class="col-md-6">
                        <label class="form-label small fw-bold">Supplier GSTIN</label>
                        {{ form.gstin }}
                    </div>
                </div>
                <div class="mb-3">
                    <label class="form-label small fw-bold">Address</label>
                    {{ form.address }}
                </div>
                <div class="mb-4">
                    <label class="form-label small fw-bold">Notes</label>
                    {{ form.notes }}
                </div>
                <div class="d-flex gap-2">
                    <button type="submit" class="btn btn-primary fw-bold px-4">Save Supplier</button>
                    <a href="{% url 'suppliers:list' %}" class="btn btn-light border">Cancel</a>
                </div>
            </form>
        </div>
    </div>
</div>
{% endblock %}
"""
with open(os.path.join(BASE_DIR, "templates", "suppliers", "supplier_form.html"), "w", encoding="utf-8") as f:
    f.write(supplier_form_html)

# templates/suppliers/supplier_detail.html
supplier_detail_html = """{% extends 'base.html' %}
{% load dukaan_tags %}

{% block title %}{{ supplier.company_name }} — Ledger{% endblock %}

{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
    <div>
        <a href="{% url 'suppliers:list' %}" class="text-muted text-decoration-none small"><i class="bi bi-arrow-left"></i> Back to Suppliers</a>
        <h4 class="fw-bold mb-0 mt-1">{{ supplier.company_name }}</h4>
        <span class="text-muted small">Contact: {{ supplier.name }} | Phone: {{ supplier.phone }} | GSTIN: {{ supplier.gstin|default:"N/A" }}</span>
    </div>
    <div class="d-flex gap-2">
        <a href="{% url 'payments:supplier_add' %}?supplier={{ supplier.pk }}" class="btn btn-success fw-bold">
            <i class="bi bi-cash me-1"></i> Make Payment
        </a>
        <a href="{% url 'purchases:create' %}" class="btn btn-primary fw-bold">
            <i class="bi bi-plus-lg me-1"></i> Inward Purchase
        </a>
    </div>
</div>

<div class="row g-3 mb-4">
    <div class="col-md-4">
        <div class="card p-3">
            <div class="text-muted small fw-bold">TOTAL PURCHASES</div>
            <div class="fs-4 fw-bold text-dark">{{ total_purchases|inr }}</div>
        </div>
    </div>
    <div class="col-md-4">
        <div class="card p-3">
            <div class="text-muted small fw-bold">TOTAL PAID</div>
            <div class="fs-4 fw-bold text-success">{{ total_paid|inr }}</div>
        </div>
    </div>
    <div class="col-md-4">
        <div class="card p-3">
            <div class="text-muted small fw-bold">OUTSTANDING PAYABLE</div>
            <div class="fs-4 fw-bold text-danger">{{ due|inr }}</div>
        </div>
    </div>
</div>
{% endblock %}
"""
with open(os.path.join(BASE_DIR, "templates", "suppliers", "supplier_detail.html"), "w", encoding="utf-8") as f:
    f.write(supplier_detail_html)

# templates/expenses/expense_list.html
expense_list_html = """{% extends 'base.html' %}
{% load dukaan_tags %}

{% block title %}Daily Expenses — {{ current_business.name }}{% endblock %}

{% block content %}
<div class="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2">
    <div>
        <h4 class="fw-bold mb-0">Daily Shop Expenses</h4>
        <span class="text-muted small">Total Filtered Expenses: <strong class="text-danger">{{ total_expenses|inr }}</strong></span>
    </div>
    <a href="{% url 'expenses:create' %}" class="btn btn-primary fw-bold"><i class="bi bi-plus-circle-fill me-1"></i> Record Expense</a>
</div>

<div class="card p-3 mb-3">
    <form method="get" class="row g-2">
        <div class="col-md-4">
            <input type="text" name="q" class="form-control" placeholder="Search expense title..." value="{{ query }}">
        </div>
        <div class="col-md-3">
            <select name="category" class="form-select">
                <option value="">All Expense Categories</option>
                {% for cat in categories %}
                    <option value="{{ cat.id }}" {% if selected_category == cat.id|stringformat:"i" %}selected{% endif %}>{{ cat.name }}</option>
                {% endfor %}
            </select>
        </div>
        <div class="col-md-2">
            <input type="date" name="start_date" class="form-control" value="{{ start_date }}">
        </div>
        <div class="col-md-2">
            <input type="date" name="end_date" class="form-control" value="{{ end_date }}">
        </div>
        <div class="col-md-1">
            <button type="submit" class="btn btn-secondary w-100">Filter</button>
        </div>
    </form>
</div>

<div class="card">
    <div class="table-responsive">
        <table class="table table-hover mb-0">
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Expense Description</th>
                    <th>Category</th>
                    <th>Amount (₹)</th>
                    <th>Payment Mode</th>
                    <th>Notes</th>
                    <th class="text-end">Actions</th>
                </tr>
            </thead>
            <tbody>
                {% for exp in page_obj %}
                    <tr>
                        <td>{{ exp.expense_date|date:"d-m-Y" }}</td>
                        <td class="fw-bold text-dark">{{ exp.title }}</td>
                        <td><span class="badge bg-light text-dark border">{{ exp.category.name|default:"General" }}</span></td>
                        <td class="fw-bold text-danger">{{ exp.amount|inr }}</td>
                        <td><span class="badge bg-secondary-subtle text-secondary">{{ exp.get_payment_method_display }}</span></td>
                        <td class="small text-muted">{{ exp.notes|default:"-" }}</td>
                        <td class="text-end">
                            <form method="post" action="{% url 'expenses:delete' exp.pk %}" class="d-inline" onsubmit="return confirm('Delete this expense?');">
                                {% csrf_token %}
                                <button type="submit" class="btn btn-outline-danger btn-sm p-1"><i class="bi bi-trash"></i></button>
                            </form>
                        </td>
                    </tr>
                {% empty %}
                    <tr><td colspan="7" class="text-center py-4 text-muted">No expenses recorded.</td></tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% endblock %}
"""
with open(os.path.join(BASE_DIR, "templates", "expenses", "expense_list.html"), "w", encoding="utf-8") as f:
    f.write(expense_list_html)

# templates/expenses/expense_form.html
expense_form_html = """{% extends 'base.html' %}

{% block title %}{{ title }} — {{ current_business.name }}{% endblock %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-lg-6">
        <div class="card p-4 shadow-sm">
            <h5 class="fw-bold mb-3 border-bottom pb-2"><i class="bi bi-wallet2 text-primary me-2"></i>{{ title }}</h5>
            <form method="post" enctype="multipart/form-data">
                {% csrf_token %}
                <div class="mb-3">
                    <label class="form-label small fw-bold">Expense Title / Reason *</label>
                    {{ form.title }}
                </div>
                <div class="row g-2 mb-3">
                    <div class="col-md-6">
                        <label class="form-label small fw-bold">Category</label>
                        {{ form.category }}
                    </div>
                    <div class="col-md-6">
                        <label class="form-label small fw-bold">Or New Category</label>
                        {{ form.category_name }}
                    </div>
                </div>
                <div class="row g-2 mb-3">
                    <div class="col-md-6">
                        <label class="form-label small fw-bold">Amount (₹) *</label>
                        {{ form.amount }}
                    </div>
                    <div class="col-md-6">
                        <label class="form-label small fw-bold">Payment Method</label>
                        {{ form.payment_method }}
                    </div>
                </div>
                <div class="mb-3">
                    <label class="form-label small fw-bold">Expense Date</label>
                    {{ form.expense_date }}
                </div>
                <div class="mb-4">
                    <label class="form-label small fw-bold">Notes / Receipt Ref</label>
                    {{ form.notes }}
                </div>
                <div class="d-flex gap-2">
                    <button type="submit" class="btn btn-primary fw-bold px-4">Record Expense</button>
                    <a href="{% url 'expenses:list' %}" class="btn btn-light border">Cancel</a>
                </div>
            </form>
        </div>
    </div>
</div>
{% endblock %}
"""
with open(os.path.join(BASE_DIR, "templates", "expenses", "expense_form.html"), "w", encoding="utf-8") as f:
    f.write(expense_form_html)

# templates/payments/payment_list.html
payment_list_html = """{% extends 'base.html' %}
{% load dukaan_tags %}

{% block title %}Payment Vouchers — {{ current_business.name }}{% endblock %}

{% block content %}
<div class="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2">
    <div>
        <h4 class="fw-bold mb-0">Payment Ledger & Receipts</h4>
        <span class="text-muted small">Inflow Receipts: <strong class="text-success">{{ total_received|inr }}</strong> | Outflows: <strong class="text-danger">{{ total_paid_out|inr }}</strong></span>
    </div>
    <div class="d-flex gap-2">
        <a href="{% url 'payments:customer_add' %}" class="btn btn-success fw-bold"><i class="bi bi-plus-circle me-1"></i> Receive Customer Khata</a>
        <a href="{% url 'payments:supplier_add' %}" class="btn btn-outline-danger fw-bold"><i class="bi bi-arrow-up-right me-1"></i> Pay Supplier</a>
    </div>
</div>

<div class="card">
    <div class="table-responsive">
        <table class="table table-hover mb-0">
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Type</th>
                    <th>Party (Customer / Supplier)</th>
                    <th>Amount (₹)</th>
                    <th>Payment Method</th>
                    <th>Txn Ref / UTR</th>
                    <th>Notes</th>
                </tr>
            </thead>
            <tbody>
                {% for p in page_obj %}
                    <tr>
                        <td>{{ p.payment_date|date:"d-m-Y" }}</td>
                        <td>
                            {% if p.payment_type == 'CUSTOMER_PAYMENT' %}
                                <span class="badge bg-success-subtle text-success"><i class="bi bi-arrow-down-left me-1"></i>Inflow (Khata)</span>
                            {% else %}
                                <span class="badge bg-danger-subtle text-danger"><i class="bi bi-arrow-up-right me-1"></i>Outflow (Vendor)</span>
                            {% endif %}
                        </td>
                        <td class="fw-bold">
                            {% if p.customer %}
                                <a href="{% url 'customers:detail' p.customer.pk %}" class="text-decoration-none">{{ p.customer.name }}</a>
                            {% elif p.supplier %}
                                <a href="{% url 'suppliers:detail' p.supplier.pk %}" class="text-decoration-none">{{ p.supplier.company_name }}</a>
                            {% else %}
                                -
                            {% endif %}
                        </td>
                        <td class="fw-bold {% if p.payment_type == 'CUSTOMER_PAYMENT' %}text-success{% else %}text-danger{% endif %}">
                            {{ p.amount|inr }}
                        </td>
                        <td><span class="badge bg-light text-dark border">{{ p.get_payment_method_display }}</span></td>
                        <td class="small text-muted font-monospace">{{ p.reference_number|default:"-" }}</td>
                        <td class="small text-muted">{{ p.notes|default:"-" }}</td>
                    </tr>
                {% empty %}
                    <tr><td colspan="7" class="text-center py-4 text-muted">No payment vouchers found.</td></tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% endblock %}
"""
with open(os.path.join(BASE_DIR, "templates", "payments", "payment_list.html"), "w", encoding="utf-8") as f:
    f.write(payment_list_html)

# templates/payments/customer_payment_form.html
cust_pay_html = """{% extends 'base.html' %}

{% block title %}Receive Customer Payment — {{ current_business.name }}{% endblock %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-lg-6">
        <div class="card p-4 shadow-sm">
            <h5 class="fw-bold mb-3 border-bottom pb-2"><i class="bi bi-cash-stack text-success me-2"></i>Receive Customer Khata Payment</h5>
            <form method="post">
                {% csrf_token %}
                <div class="mb-3">
                    <label class="form-label small fw-bold">Select Customer *</label>
                    {{ form.customer }}
                </div>
                <div class="row g-2 mb-3">
                    <div class="col-md-6">
                        <label class="form-label small fw-bold">Amount Received (₹) *</label>
                        {{ form.amount }}
                    </div>
                    <div class="col-md-6">
                        <label class="form-label small fw-bold">Payment Method</label>
                        {{ form.payment_method }}
                    </div>
                </div>
                <div class="row g-2 mb-3">
                    <div class="col-md-6">
                        <label class="form-label small fw-bold">Payment Date</label>
                        {{ form.payment_date }}
                    </div>
                    <div class="col-md-6">
                        <label class="form-label small fw-bold">UPI Ref / UTR / Cheque</label>
                        {{ form.reference_number }}
                    </div>
                </div>
                <div class="mb-4">
                    <label class="form-label small fw-bold">Notes</label>
                    {{ form.notes }}
                </div>
                <div class="d-flex gap-2">
                    <button type="submit" class="btn btn-success fw-bold px-4">Record Payment & Generate Receipt</button>
                    <a href="{% url 'customers:list' %}" class="btn btn-light border">Cancel</a>
                </div>
            </form>
        </div>
    </div>
</div>
{% endblock %}
"""
with open(os.path.join(BASE_DIR, "templates", "payments", "customer_payment_form.html"), "w", encoding="utf-8") as f:
    f.write(cust_pay_html)

# templates/payments/payment_receipt_success.html
pay_rec_html = """{% extends 'base.html' %}
{% load dukaan_tags %}

{% block title %}Payment Receipt Recorded{% endblock %}

{% block content %}
<div class="row justify-content-center py-4">
    <div class="col-lg-6">
        <div class="card p-4 shadow-sm text-center">
            <div class="stat-icon bg-success-subtle text-success mx-auto mb-3" style="width: 60px; height: 60px; font-size: 2rem;">
                <i class="bi bi-check2"></i>
            </div>
            <h4 class="fw-bold">Payment Received Successfully!</h4>
            <p class="text-muted">Recorded voucher for <strong>{{ customer.name }}</strong></p>

            <div class="p-3 bg-light rounded border mb-4 text-start">
                <div class="d-flex justify-content-between mb-2">
                    <span>Amount Received:</span>
                    <strong class="text-success fs-5">{{ payment.amount|inr }}</strong>
                </div>
                <div class="d-flex justify-content-between mb-2">
                    <span>Payment Mode:</span>
                    <span>{{ payment.get_payment_method_display }}</span>
                </div>
                <div class="d-flex justify-content-between text-danger">
                    <span>Remaining Outstanding Khata:</span>
                    <strong>{{ remaining_due|inr }}</strong>
                </div>
            </div>

            <div class="d-grid gap-2">
                {% if wa_url %}
                    <a href="{{ wa_url }}" target="_blank" class="btn btn-whatsapp fw-bold py-2">
                        <i class="bi bi-whatsapp me-1"></i> Send Receipt on WhatsApp
                    </a>
                {% endif %}
                <a href="{% url 'customers:detail' customer.pk %}" class="btn btn-outline-secondary py-2">View Customer Ledger</a>
                <a href="{% url 'payments:list' %}" class="btn btn-light border py-2">All Payment Vouchers</a>
            </div>
        </div>
    </div>
</div>
{% endblock %}
"""
with open(os.path.join(BASE_DIR, "templates", "payments", "payment_receipt_success.html"), "w", encoding="utf-8") as f:
    f.write(pay_rec_html)

# templates/payments/supplier_payment_form.html
sup_pay_html = """{% extends 'base.html' %}

{% block title %}Pay Supplier — {{ current_business.name }}{% endblock %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-lg-6">
        <div class="card p-4 shadow-sm">
            <h5 class="fw-bold mb-3 border-bottom pb-2"><i class="bi bi-truck text-primary me-2"></i>Record Supplier Payment Voucher</h5>
            <form method="post">
                {% csrf_token %}
                <div class="mb-3">
                    <label class="form-label small fw-bold">Select Supplier *</label>
                    {{ form.supplier }}
                </div>
                <div class="row g-2 mb-3">
                    <div class="col-md-6">
                        <label class="form-label small fw-bold">Amount Paid (₹) *</label>
                        {{ form.amount }}
                    </div>
                    <div class="col-md-6">
                        <label class="form-label small fw-bold">Payment Method</label>
                        {{ form.payment_method }}
                    </div>
                </div>
                <div class="row g-2 mb-3">
                    <div class="col-md-6">
                        <label class="form-label small fw-bold">Payment Date</label>
                        {{ form.payment_date }}
                    </div>
                    <div class="col-md-6">
                        <label class="form-label small fw-bold">Bank Reference / Cheque No.</label>
                        {{ form.reference_number }}
                    </div>
                </div>
                <div class="mb-4">
                    <label class="form-label small fw-bold">Notes</label>
                    {{ form.notes }}
                </div>
                <div class="d-flex gap-2">
                    <button type="submit" class="btn btn-primary fw-bold px-4">Record Supplier Payment</button>
                    <a href="{% url 'suppliers:list' %}" class="btn btn-light border">Cancel</a>
                </div>
            </form>
        </div>
    </div>
</div>
{% endblock %}
"""
with open(os.path.join(BASE_DIR, "templates", "payments", "supplier_payment_form.html"), "w", encoding="utf-8") as f:
    f.write(sup_pay_html)

# templates/invoices/invoice_detail.html
inv_detail_html = """{% extends 'base.html' %}
{% load dukaan_tags %}

{% block title %}Invoice #{{ sale.invoice_number }} — {{ current_business.name }}{% endblock %}

{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
    <div>
        <a href="{% url 'sales:list' %}" class="text-muted text-decoration-none small"><i class="bi bi-arrow-left"></i> Back to Sales</a>
        <h4 class="fw-bold mb-0 mt-1">Invoice #{{ sale.invoice_number }}</h4>
    </div>
    <div class="d-flex gap-2">
        {% if wa_url %}
            <a href="{{ wa_url }}" target="_blank" class="btn btn-whatsapp fw-bold shadow-sm">
                <i class="bi bi-whatsapp me-1"></i> Share on WhatsApp
            </a>
        {% endif %}
        <a href="{% url 'invoices:pdf' sale.pk %}" class="btn btn-outline-primary fw-bold">
            <i class="bi bi-file-earmark-pdf me-1"></i> Download PDF
        </a>
        <a href="{% url 'invoices:print' sale.pk %}" target="_blank" class="btn btn-secondary">
            <i class="bi bi-printer me-1"></i> Print Bill
        </a>
    </div>
</div>

<div class="card p-4 shadow-sm bg-white" style="max-width: 850px; margin: auto;">
    <!-- Shop & Bill Header -->
    <div class="d-flex justify-content-between align-items-start border-bottom pb-4 mb-4">
        <div>
            <h3 class="fw-bold text-dark mb-1">{{ current_business.name }}</h3>
            <div class="text-muted small">
                {{ current_business.address|default:"" }}<br/>
                {{ current_business.city|default:"" }}, {{ current_business.state|default:"Maharashtra" }} - {{ current_business.pincode|default:"" }}<br/>
                Phone: {{ current_business.phone }} | Email: {{ current_business.email }}<br/>
                {% if current_business.gstin %}<strong>GSTIN: {{ current_business.gstin }}</strong>{% endif %}
            </div>
        </div>
        <div class="text-end">
            <span class="badge bg-primary fs-6 mb-2">TAX INVOICE</span>
            <div class="fw-bold fs-5">#{{ sale.invoice_number }}</div>
            <div class="text-muted small">Date: {{ sale.sale_date|date:"d-m-Y H:i" }}</div>
            <div class="text-muted small">Mode: {{ sale.get_payment_method_display }}</div>
        </div>
    </div>

    <!-- Billed To -->
    <div class="mb-4">
        <div class="text-muted small fw-bold text-uppercase">Billed To (Customer):</div>
        <h5 class="fw-bold mb-1">{{ sale.customer.name }}</h5>
        <div class="text-muted small">Mobile: {{ sale.customer.phone }} {% if sale.customer.address %}| Address: {{ sale.customer.address }}{% endif %}</div>
    </div>

    <!-- Items Table -->
    <div class="table-responsive mb-4">
        <table class="table table-bordered align-middle">
            <thead class="bg-light">
                <tr>
                    <th style="width: 40px;">#</th>
                    <th>Item Description / Serial / IMEI</th>
                    <th class="text-center" style="width: 80px;">Qty</th>
                    <th class="text-end" style="width: 120px;">Rate (₹)</th>
                    <th class="text-end" style="width: 100px;">Disc (₹)</th>
                    <th class="text-end" style="width: 130px;">Amount (₹)</th>
                </tr>
            </thead>
            <tbody>
                {% for item in items %}
                    <tr>
                        <td>{{ forloop.counter }}</td>
                        <td>
                            <strong>{{ item.product.name }}</strong>
                            {% if item.product.brand %}<span class="text-muted small">({{ item.product.brand }})</span>{% endif %}
                            {% if item.imei_numbers %}
                                <div class="text-primary small font-monospace">{{ item.imei_numbers }}</div>
                            {% endif %}
                            {% if item.product.warranty_months > 0 %}
                                <div class="text-success small"><i class="bi bi-shield-check"></i> {{ item.product.warranty_months }} Months Warranty</div>
                            {% endif %}
                        </td>
                        <td class="text-center">{{ item.quantity }}</td>
                        <td class="text-end">{{ item.unit_price|inr }}</td>
                        <td class="text-end">{{ item.discount|inr }}</td>
                        <td class="text-end fw-bold">{{ item.total_price|inr }}</td>
                    </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    <!-- Summary Box -->
    <div class="row justify-content-end mb-4">
        <div class="col-md-5">
            <table class="table table-sm table-borderless">
                <tr>
                    <td class="text-muted">Subtotal:</td>
                    <td class="text-end fw-bold">{{ sale.subtotal|inr }}</td>
                </tr>
                {% if sale.discount > 0 %}
                <tr>
                    <td class="text-muted">Discount:</td>
                    <td class="text-end text-danger">-{{ sale.discount|inr }}</td>
                </tr>
                {% endif %}
                {% if sale.tax_amount > 0 %}
                <tr>
                    <td class="text-muted">GST / Tax:</td>
                    <td class="text-end">{{ sale.tax_amount|inr }}</td>
                </tr>
                {% endif %}
                <tr class="border-top fs-5">
                    <td class="fw-bold">Grand Total:</td>
                    <td class="text-end fw-bold text-primary">{{ sale.total_amount|inr }}</td>
                </tr>
                <tr>
                    <td class="text-muted">Paid Amount:</td>
                    <td class="text-end text-success fw-bold">{{ sale.paid_amount|inr }}</td>
                </tr>
                <tr>
                    <td class="text-muted">Balance Due (Khata):</td>
                    <td class="text-end fw-bold {% if sale.due_amount > 0 %}text-danger{% else %}text-success{% endif %}">{{ sale.due_amount|inr }}</td>
                </tr>
            </table>
        </div>
    </div>

    <!-- Footer Note -->
    <div class="border-top pt-3 text-center text-muted small">
        <div class="fw-bold">Terms & Conditions:</div>
        <div>{{ current_business.invoice_footer }}</div>
        <div class="mt-2" style="font-size: 0.75rem;">Generated using DukaanFlow Mobile Shop SaaS.</div>
    </div>
</div>
{% endblock %}
"""
with open(os.path.join(BASE_DIR, "templates", "invoices", "invoice_detail.html"), "w", encoding="utf-8") as f:
    f.write(inv_detail_html)

# templates/invoices/invoice_print.html
inv_print_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Print Bill #{{ sale.invoice_number }}</title>
    <style>
        body { font-family: monospace, sans-serif; font-size: 12px; margin: 0; padding: 15px; color: #000; width: 80mm; }
        .text-center { text-align: center; }
        .text-end { text-align: right; }
        .fw-bold { font-weight: bold; }
        hr { border: none; border-top: 1px dashed #000; margin: 6px 0; }
        table { width: 100%; border-collapse: collapse; }
        td, th { padding: 3px 0; }
        @media print {
            body { padding: 0; }
            @page { margin: 0; size: 80mm auto; }
        }
    </style>
</head>
<body onload="window.print();">
    <div class="text-center">
        <div class="fw-bold" style="font-size: 16px;">{{ current_business.name }}</div>
        <div>{{ current_business.address|default:"" }}</div>
        <div>Ph: {{ current_business.phone }}</div>
        {% if current_business.gstin %}<div>GSTIN: {{ current_business.gstin }}</div>{% endif %}
    </div>
    <hr>
    <div>
        <div>Bill No: #{{ sale.invoice_number }}</div>
        <div>Date: {{ sale.sale_date|date:"d/m/Y H:i" }}</div>
        <div>Cust: {{ sale.customer.name }} ({{ sale.customer.phone }})</div>
    </div>
    <hr>
    <table>
        <thead>
            <tr>
                <th style="text-align: left;">Item</th>
                <th class="text-center">Qty</th>
                <th class="text-end">Amt</th>
            </tr>
        </thead>
        <tbody>
            {% for item in items %}
                <tr>
                    <td>
                        {{ item.product.name|truncatechars:18 }}
                        {% if item.imei_numbers %}<br/><small>{{ item.imei_numbers }}</small>{% endif %}
                    </td>
                    <td class="text-center">{{ item.quantity }}</td>
                    <td class="text-end">{{ item.total_price }}</td>
                </tr>
            {% endfor %}
        </tbody>
    </table>
    <hr>
    <table>
        <tr>
            <td>Total:</td>
            <td class="text-end fw-bold">₹{{ sale.total_amount }}</td>
        </tr>
        <tr>
            <td>Paid:</td>
            <td class="text-end">₹{{ sale.paid_amount }}</td>
        </tr>
        <tr>
            <td>Due:</td>
            <td class="text-end fw-bold">₹{{ sale.due_amount }}</td>
        </tr>
    </table>
    <hr>
    <div class="text-center" style="font-size: 10px;">
        {{ current_business.invoice_footer }}<br/>
        *** Thank You Visit Again ***
    </div>
</body>
</html>
"""
with open(os.path.join(BASE_DIR, "templates", "invoices", "invoice_print.html"), "w", encoding="utf-8") as f:
    f.write(inv_print_html)

# --- REPORTS TEMPLATES ---
# templates/reports/index.html
rep_idx_html = """{% extends 'base.html' %}

{% block title %}Reports & P&L Analytics — {{ current_business.name }}{% endblock %}

{% block content %}
<div class="mb-4">
    <h4 class="fw-bold mb-0">Business Intelligence & Financial Reports</h4>
    <span class="text-muted small">Exportable profit & loss statements, sales audits, and inventory valuations</span>
</div>

<div class="row g-3">
    <div class="col-md-6 col-lg-3">
        <div class="card p-4 h-100 shadow-sm text-center">
            <div class="stat-icon bg-primary-subtle text-primary mx-auto mb-3">
                <i class="bi bi-graph-up-arrow"></i>
            </div>
            <h5 class="fw-bold">Sales Analysis</h5>
            <p class="text-muted small">Detailed sales bills by date ranges with CSV export.</p>
            <a href="{% url 'reports:sales' %}" class="btn btn-outline-primary btn-sm fw-bold mt-auto">View Sales Report</a>
        </div>
    </div>

    <div class="col-md-6 col-lg-3">
        <div class="card p-4 h-100 shadow-sm text-center">
            <div class="stat-icon bg-success-subtle text-success mx-auto mb-3">
                <i class="bi bi-calculator"></i>
            </div>
            <h5 class="fw-bold">True Profit & Loss</h5>
            <p class="text-muted small">Calculates Real Gross Margin (Revenue - COGS) & Net Profit after Expenses.</p>
            <a href="{% url 'reports:profit_loss' %}" class="btn btn-outline-success btn-sm fw-bold mt-auto">View P&L Report</a>
        </div>
    </div>

    <div class="col-md-6 col-lg-3">
        <div class="card p-4 h-100 shadow-sm text-center">
            <div class="stat-icon bg-danger-subtle text-danger mx-auto mb-3">
                <i class="bi bi-journal-text"></i>
            </div>
            <h5 class="fw-bold">Customer Khata Dues</h5>
            <p class="text-muted small">Outstanding credit balances and WhatsApp collection links.</p>
            <a href="{% url 'reports:khata' %}" class="btn btn-outline-danger btn-sm fw-bold mt-auto">View Khata Report</a>
        </div>
    </div>

    <div class="col-md-6 col-lg-3">
        <div class="card p-4 h-100 shadow-sm text-center">
            <div class="stat-icon bg-warning-subtle text-warning mx-auto mb-3">
                <i class="bi bi-box-seam"></i>
            </div>
            <h5 class="fw-bold">Stock Valuation</h5>
            <p class="text-muted small">Inventory stock valuation at cost vs retail MRP with reorder flags.</p>
            <a href="{% url 'reports:inventory' %}" class="btn btn-outline-warning btn-sm fw-bold mt-auto">View Stock Report</a>
        </div>
    </div>
</div>
{% endblock %}
"""
with open(os.path.join(BASE_DIR, "templates", "reports", "index.html"), "w", encoding="utf-8") as f:
    f.write(rep_idx_html)

# templates/reports/sales_report.html
rep_sales_html = """{% extends 'base.html' %}
{% load dukaan_tags %}

{% block title %}Sales Report — {{ current_business.name }}{% endblock %}

{% block content %}
<div class="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2">
    <div>
        <a href="{% url 'reports:index' %}" class="text-muted text-decoration-none small"><i class="bi bi-arrow-left"></i> Back to Reports</a>
        <h4 class="fw-bold mb-0 mt-1">Sales Performance Report</h4>
    </div>
    <a href="{% url 'reports:sales' %}?period={{ period }}&start_date={{ start_date }}&end_date={{ end_date }}&export=csv" class="btn btn-outline-secondary">
        <i class="bi bi-download me-1"></i> Export to CSV
    </a>
</div>

<div class="card p-3 mb-3">
    <form method="get" class="row g-2 align-items-end">
        <div class="col-md-4">
            <label class="form-label small fw-bold">Period</label>
            <select name="period" class="form-select">
                <option value="today" {% if period == 'today' %}selected{% endif %}>Today</option>
                <option value="yesterday" {% if period == 'yesterday' %}selected{% endif %}>Yesterday</option>
                <option value="this_week" {% if period == 'this_week' %}selected{% endif %}>This Week</option>
                <option value="this_month" {% if period == 'this_month' %}selected{% endif %}>This Month</option>
                <option value="last_month" {% if period == 'last_month' %}selected{% endif %}>Last Month</option>
                <option value="custom" {% if period == 'custom' %}selected{% endif %}>Custom Date Range</option>
            </select>
        </div>
        <div class="col-md-3">
            <label class="form-label small fw-bold">Start Date</label>
            <input type="date" name="start_date" class="form-control" value="{{ start_date }}">
        </div>
        <div class="col-md-3">
            <label class="form-label small fw-bold">End Date</label>
            <input type="date" name="end_date" class="form-control" value="{{ end_date }}">
        </div>
        <div class="col-md-2">
            <button type="submit" class="btn btn-primary w-100">Apply</button>
        </div>
    </form>
</div>

<div class="row g-3 mb-4">
    <div class="col-md-4">
        <div class="card p-3">
            <div class="text-muted small fw-bold text-uppercase">Total Sales Revenue</div>
            <div class="fs-4 fw-bold text-primary">{{ total_sales|inr }}</div>
        </div>
    </div>
    <div class="col-md-4">
        <div class="card p-3">
            <div class="text-muted small fw-bold text-uppercase">Collected Cash/UPI</div>
            <div class="fs-4 fw-bold text-success">{{ total_paid|inr }}</div>
        </div>
    </div>
    <div class="col-md-4">
        <div class="card p-3">
            <div class="text-muted small fw-bold text-uppercase">Credit Generated</div>
            <div class="fs-4 fw-bold text-danger">{{ total_due|inr }}</div>
        </div>
    </div>
</div>

<div class="card">
    <div class="table-responsive">
        <table class="table table-hover mb-0">
            <thead>
                <tr>
                    <th>Invoice No</th>
                    <th>Date</th>
                    <th>Customer</th>
                    <th>Total</th>
                    <th>Paid</th>
                    <th>Due</th>
                    <th>Mode</th>
                </tr>
            </thead>
            <tbody>
                {% for s in sales %}
                    <tr>
                        <td class="fw-bold text-primary">#{{ s.invoice_number }}</td>
                        <td>{{ s.sale_date|date:"d-m-Y" }}</td>
                        <td>{{ s.customer.name }}</td>
                        <td class="fw-bold">{{ s.total_amount|inr }}</td>
                        <td class="text-success">{{ s.paid_amount|inr }}</td>
                        <td>{{ s.due_amount|inr }}</td>
                        <td><span class="badge bg-light text-dark border">{{ s.get_payment_method_display }}</span></td>
                    </tr>
                {% empty %}
                    <tr><td colspan="7" class="text-center py-4 text-muted">No sales orders found in this period.</td></tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% endblock %}
"""
with open(os.path.join(BASE_DIR, "templates", "reports", "sales_report.html"), "w", encoding="utf-8") as f:
    f.write(rep_sales_html)

# templates/reports/profit_loss.html
rep_pl_html = """{% extends 'base.html' %}
{% load dukaan_tags %}

{% block title %}Profit & Loss Statement — {{ current_business.name }}{% endblock %}

{% block content %}
<div class="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2">
    <div>
        <a href="{% url 'reports:index' %}" class="text-muted text-decoration-none small"><i class="bi bi-arrow-left"></i> Back to Reports</a>
        <h4 class="fw-bold mb-0 mt-1">True Profit & Loss Statement</h4>
    </div>
</div>

<div class="card p-3 mb-4">
    <form method="get" class="row g-2 align-items-end">
        <div class="col-md-4">
            <label class="form-label small fw-bold">Period</label>
            <select name="period" class="form-select">
                <option value="today" {% if period == 'today' %}selected{% endif %}>Today</option>
                <option value="this_week" {% if period == 'this_week' %}selected{% endif %}>This Week</option>
                <option value="this_month" {% if period == 'this_month' %}selected{% endif %}>This Month</option>
                <option value="last_month" {% if period == 'last_month' %}selected{% endif %}>Last Month</option>
                <option value="custom" {% if period == 'custom' %}selected{% endif %}>Custom Range</option>
            </select>
        </div>
        <div class="col-md-3">
            <label class="form-label small fw-bold">Start Date</label>
            <input type="date" name="start_date" class="form-control" value="{{ start_date }}">
        </div>
        <div class="col-md-3">
            <label class="form-label small fw-bold">End Date</label>
            <input type="date" name="end_date" class="form-control" value="{{ end_date }}">
        </div>
        <div class="col-md-2">
            <button type="submit" class="btn btn-primary w-100">Calculate P&L</button>
        </div>
    </form>
</div>

<!-- P&L Financial Cards -->
<div class="row g-3 mb-4">
    <div class="col-md-6 col-lg-3">
        <div class="card p-3">
            <div class="text-muted small fw-bold">1. SALES REVENUE</div>
            <div class="fs-4 fw-bold text-dark">{{ total_revenue|inr }}</div>
            <span class="text-muted small">Total billed sales</span>
        </div>
    </div>
    <div class="col-md-6 col-lg-3">
        <div class="card p-3">
            <div class="text-muted small fw-bold">2. COST OF GOODS SOLD (COGS)</div>
            <div class="fs-4 fw-bold text-secondary">{{ total_cogs|inr }}</div>
            <span class="text-muted small">Actual product purchase cost</span>
        </div>
    </div>
    <div class="col-md-6 col-lg-3">
        <div class="card p-3 bg-primary-subtle border-primary">
            <div class="text-primary small fw-bold">3. GROSS PROFIT</div>
            <div class="fs-4 fw-bold text-primary">{{ gross_profit|inr }}</div>
            <span class="text-primary small fw-bold">Margin: {{ gross_margin }}%</span>
        </div>
    </div>
    <div class="col-md-6 col-lg-3">
        <div class="card p-3 bg-success-subtle border-success">
            <div class="text-success small fw-bold">4. REAL NET PROFIT</div>
            <div class="fs-4 fw-bold text-success">{{ net_profit|inr }}</div>
            <span class="text-success small fw-bold">Net Margin: {{ net_margin }}%</span>
        </div>
    </div>
</div>

<div class="row g-3">
    <!-- P&L Math Breakdown -->
    <div class="col-lg-7">
        <div class="card">
            <div class="card-header fw-bold">Accounting Formula Breakdown</div>
            <div class="card-body">
                <table class="table table-bordered mb-0">
                    <tbody>
                        <tr>
                            <td><strong>Total Selling Revenue</strong></td>
                            <td class="text-end fw-bold">{{ total_revenue|inr }}</td>
                        </tr>
                        <tr class="text-muted">
                            <td>Less: Cost of Goods Sold (Purchase Cost of Items Sold)</td>
                            <td class="text-end">-{{ total_cogs|inr }}</td>
                        </tr>
                        <tr class="table-primary">
                            <td><strong>= Gross Profit</strong></td>
                            <td class="text-end fw-bold">{{ gross_profit|inr }}</td>
                        </tr>
                        <tr class="text-danger">
                            <td>Less: Total Business Expenses (Rent, Bills, Staff Salaries, etc.)</td>
                            <td class="text-end">-{{ total_expenses|inr }}</td>
                        </tr>
                        <tr class="table-success fs-5">
                            <td><strong>= Net Shop Profit</strong></td>
                            <td class="text-end fw-bold">{{ net_profit|inr }}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- Expense Categories Breakdown -->
    <div class="col-lg-5">
        <div class="card">
            <div class="card-header fw-bold">Expense Breakdown (This Period)</div>
            <div class="table-responsive">
                <table class="table table-hover mb-0">
                    <thead>
                        <tr>
                            <th>Category</th>
                            <th class="text-end">Amount</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for eb in expense_breakdown %}
                            <tr>
                                <td>{{ eb.category__name|default:"General / Other" }}</td>
                                <td class="text-end fw-bold text-danger">₹{{ eb.total }}</td>
                            </tr>
                        {% empty %}
                            <tr><td colspan="2" class="text-center py-3 text-muted">No expenses in this period.</td></tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>
{% endblock %}
"""
with open(os.path.join(BASE_DIR, "templates", "reports", "profit_loss.html"), "w", encoding="utf-8") as f:
    f.write(rep_pl_html)

# templates/reports/khata_report.html
rep_khata_html = """{% extends 'base.html' %}
{% load dukaan_tags %}

{% block title %}Customer Khata Dues Report — {{ current_business.name }}{% endblock %}

{% block content %}
<div class="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2">
    <div>
        <a href="{% url 'reports:index' %}" class="text-muted text-decoration-none small"><i class="bi bi-arrow-left"></i> Back to Reports</a>
        <h4 class="fw-bold mb-0 mt-1">Outstanding Customer Khata Dues</h4>
        <span class="text-muted small">Total Market Udhar: <strong class="text-danger">{{ total_due_all|inr }}</strong></span>
    </div>
    <a href="{% url 'reports:khata' %}?export=csv" class="btn btn-outline-secondary">
        <i class="bi bi-download me-1"></i> Export to CSV
    </a>
</div>

<div class="card">
    <div class="table-responsive">
        <table class="table table-hover mb-0">
            <thead>
                <tr>
                    <th>Customer Name</th>
                    <th>Mobile</th>
                    <th>Total Purchases</th>
                    <th>Total Paid</th>
                    <th>Pending Due</th>
                    <th class="text-end">Action</th>
                </tr>
            </thead>
            <tbody>
                {% for k in khata_list %}
                    <tr>
                        <td class="fw-bold"><a href="{% url 'customers:detail' k.customer.pk %}" class="text-decoration-none">{{ k.customer.name }}</a></td>
                        <td>{{ k.customer.phone }}</td>
                        <td>{{ k.total_purchases|inr }}</td>
                        <td class="text-success">{{ k.total_paid|inr }}</td>
                        <td><span class="inr-badge-due">{{ k.due|inr }}</span></td>
                        <td class="text-end">
                            {% if k.wa_url %}
                                <a href="{{ k.wa_url }}" target="_blank" class="btn btn-whatsapp btn-sm"><i class="bi bi-whatsapp me-1"></i> Remind</a>
                            {% endif %}
                        </td>
                    </tr>
                {% empty %}
                    <tr><td colspan="6" class="text-center py-4 text-muted">All customer accounts are 100% cleared! No outstanding dues.</td></tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% endblock %}
"""
with open(os.path.join(BASE_DIR, "templates", "reports", "khata_report.html"), "w", encoding="utf-8") as f:
    f.write(rep_khata_html)

# templates/reports/inventory_report.html
rep_inv_html = """{% extends 'base.html' %}
{% load dukaan_tags %}

{% block title %}Inventory & Stock Report — {{ current_business.name }}{% endblock %}

{% block content %}
<div class="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2">
    <div>
        <a href="{% url 'reports:index' %}" class="text-muted text-decoration-none small"><i class="bi bi-arrow-left"></i> Back to Reports</a>
        <h4 class="fw-bold mb-0 mt-1">Inventory Valuation Report</h4>
    </div>
    <a href="{% url 'reports:inventory' %}?export=csv" class="btn btn-outline-secondary">
        <i class="bi bi-download me-1"></i> Export to CSV
    </a>
</div>

<div class="row g-3 mb-4">
    <div class="col-md-4">
        <div class="card p-3">
            <div class="text-muted small fw-bold">TOTAL STOCK ITEMS</div>
            <div class="fs-4 fw-bold text-dark">{{ total_items }} units</div>
        </div>
    </div>
    <div class="col-md-4">
        <div class="card p-3">
            <div class="text-muted small fw-bold">STOCK VALUATION (PURCHASE COST)</div>
            <div class="fs-4 fw-bold text-secondary">{{ total_cost_val|inr }}</div>
        </div>
    </div>
    <div class="col-md-4">
        <div class="card p-3">
            <div class="text-muted small fw-bold">STOCK VALUATION (RETAIL MRP)</div>
            <div class="fs-4 fw-bold text-primary">{{ total_mrp_val|inr }}</div>
        </div>
    </div>
</div>

<div class="card">
    <div class="table-responsive">
        <table class="table table-hover mb-0">
            <thead>
                <tr>
                    <th>Product Name & Brand</th>
                    <th>Category</th>
                    <th>Cost Price</th>
                    <th>Selling Price</th>
                    <th>Qty</th>
                    <th>Valuation (Cost)</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                {% for p in products %}
                    <tr>
                        <td class="fw-bold">{{ p.name }}</td>
                        <td>{{ p.category.name|default:"General" }}</td>
                        <td>{{ p.purchase_price|inr }}</td>
                        <td>{{ p.selling_price|inr }}</td>
                        <td class="fw-bold">{{ p.stock_quantity }}</td>
                        <td>{{ p.stock_quantity|multiply:p.purchase_price|inr }}</td>
                        <td>
                            {% if p.is_out_of_stock %}
                                <span class="badge bg-danger">Out of Stock</span>
                            {% elif p.is_low_stock %}
                                <span class="badge bg-warning text-dark">Low Stock</span>
                            {% else %}
                                <span class="badge bg-success-subtle text-success">In Stock</span>
                            {% endif %}
                        </td>
                    </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% endblock %}
"""
with open(os.path.join(BASE_DIR, "templates", "reports", "inventory_report.html"), "w", encoding="utf-8") as f:
    f.write(rep_inv_html)

print("Phase 8d (POS, Purchases, Payments, Invoices, Reports Templates & JS) created successfully!")
