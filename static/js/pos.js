
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
