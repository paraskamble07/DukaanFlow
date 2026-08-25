from django.shortcuts import render, redirect, get_object_or_404
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
