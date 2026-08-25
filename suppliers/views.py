from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from core.utils import business_required
from .models import Supplier
from .forms import SupplierForm
from purchases.models import Purchase
from payments.models import Payment

@business_required
def supplier_list(request):
    business = request.business
    query = request.GET.get('q', '').strip()
    
    suppliers = Supplier.objects.filter(business=business)
    if query:
        suppliers = suppliers.filter(
            Q(name__icontains=query) | Q(company_name__icontains=query) | Q(phone__icontains=query)
        )
        
    sup_list = list(suppliers)
    for s in sup_list:
        s.total_purchases = s.get_total_purchases()
        s.total_paid_amt = s.get_total_paid()
        s.due_amt = s.get_outstanding_due()
        
    paginator = Paginator(sup_list, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    total_payable = sum(s.due_amt for s in sup_list)
    
    return render(request, 'suppliers/supplier_list.html', {
        'page_obj': page_obj,
        'query': query,
        'total_payable': total_payable,
    })

@business_required
def supplier_create(request):
    business = request.business
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            supplier = form.save(commit=False)
            supplier.business = business
            supplier.save()
            messages.success(request, f"Supplier '{supplier.company_name}' added successfully!")
            return redirect('suppliers:detail', pk=supplier.pk)
    else:
        form = SupplierForm()
    return render(request, 'suppliers/supplier_form.html', {'form': form, 'title': 'Add Supplier'})

@business_required
def supplier_update(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk, business=request.business)
    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            messages.success(request, f"Supplier '{supplier.company_name}' updated successfully!")
            return redirect('suppliers:detail', pk=supplier.pk)
    else:
        form = SupplierForm(instance=supplier)
    return render(request, 'suppliers/supplier_form.html', {'form': form, 'supplier': supplier, 'title': 'Edit Supplier'})

@business_required
def supplier_detail(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk, business=request.business)
    purchases = Purchase.objects.filter(supplier=supplier, business=request.business).order_by('-purchase_date')
    payments = Payment.objects.filter(supplier=supplier, business=request.business).order_by('-payment_date')
    
    total_purchases = supplier.get_total_purchases()
    total_paid = supplier.get_total_paid()
    due = supplier.get_outstanding_due()
    
    return render(request, 'suppliers/supplier_detail.html', {
        'supplier': supplier,
        'purchases': purchases,
        'payments': payments,
        'total_purchases': total_purchases,
        'total_paid': total_paid,
        'due': due,
    })

@business_required
def supplier_delete(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk, business=request.business)
    if request.method == 'POST':
        name = supplier.company_name
        supplier.delete()
        messages.success(request, f"Supplier '{name}' removed.")
        return redirect('suppliers:list')
    return render(request, 'suppliers/supplier_confirm_delete.html', {'supplier': supplier})
