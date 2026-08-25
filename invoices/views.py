from django.shortcuts import render, get_object_or_404
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
    wa_msg = f"Namaste {sale.customer.name},\n\nHere is your invoice *#{sale.invoice_number}* from *{business_name}*:\n"
    wa_msg += f"Total: *{format_inr(sale.total_amount)}*\nPaid: *{format_inr(sale.paid_amount)}*\n"
    if sale.due_amount > 0:
        wa_msg += f"Due: *{format_inr(sale.due_amount)}*\n"
    wa_msg += f"Date: {sale.sale_date.strftime('%d-%m-%Y')}\n\nThank you for shopping with us!"
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
