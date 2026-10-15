import io
from datetime import datetime
from decimal import Decimal
from django.utils import timezone
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, HRFlowable
from core.utils import format_inr
from sales.models import Sale
from payments.models import Payment

def generate_invoice_pdf(sale):
    """Generates a pixel-perfect, GST-ready Indian Invoice PDF using ReportLab."""
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


# ---------------------------------------------------------------------------
# Customer ledger (Khata) statement
# ---------------------------------------------------------------------------
#
# All arithmetic is Decimal and server-side. Every row's running balance is
# derived from the database rows themselves — nothing the client sent is
# trusted or echoed back unvalidated.

def _ledger_rows(customer, from_date, to_date):
    """Return (opening_balance, rows) for a customer's ledger.

    rows: chronological list of {date, particulars, debit, credit, balance}
    covering [from_date, to_date] inclusive. opening_balance is the net
    balance carried in from all transactions strictly before from_date
    (Decimal('0.00') when no lower bound is applied).
    """
    sales = list(Sale.objects.filter(customer=customer).order_by('sale_date'))
    payments = list(Payment.objects.filter(
        customer=customer, payment_type='CUSTOMER_PAYMENT').order_by('payment_date'))

    def _as_date(d):
        # sale_date is a DateTimeField, payment_date a DateField — the
        # statement writes a single calendar day per row.
        return d.date() if isinstance(d, datetime) else d

    events = [(_as_date(s.sale_date), 'sale', s) for s in sales] + \
             [(_as_date(p.payment_date), 'payment', p) for p in payments]
    # Stable chronological order; 'payment' sorts before 'sale' on the same
    # date, matching the "paid on the same day" bookkeeping convention.
    events.sort(key=lambda e: (e[0], e[1]))

    def _before_period(d):
        return bool(from_date) and d < from_date

    opening = Decimal('0.00')
    rows = []
    for when, kind, obj in events:
        # Anything after the statement date does not exist yet "as of" this
        # statement: exclude it entirely — it must never touch the figures.
        if to_date and when > to_date:
            continue
        if kind == 'sale':
            amount = obj.total_amount or Decimal('0.00')
            if _before_period(when):
                opening += amount
                continue
            particulars = "Invoice %s" % obj.invoice_number
            if obj.get_payment_method_display():
                particulars += " (%s)" % obj.get_payment_method_display()
            rows.append({'date': when, 'particulars': particulars,
                         'debit': amount, 'credit': Decimal('0.00')})
        else:
            amount = obj.amount or Decimal('0.00')
            if _before_period(when):
                opening -= amount
                continue
            particulars = "Payment received (%s)" % obj.get_payment_method_display()
            if obj.reference_number:
                particulars += " Ref: %s" % obj.reference_number
            rows.append({'date': when, 'particulars': particulars,
                         'debit': Decimal('0.00'), 'credit': amount})

    running = opening
    for row in rows:
        running = running + row['debit'] - row['credit']
        row['balance'] = running

    return opening, rows


def generate_ledger_pdf(customer, from_date=None, to_date=None):
    """Generate a customer ledger (Khata) statement PDF as a BytesIO buffer.

    Totals are computed from the database with Decimal arithmetic. With no
    date filters the closing balance always equals the customer's current
    outstanding due — tests assert this invariant.
    """
    business = customer.business
    opening, rows = _ledger_rows(customer, from_date, to_date)

    total_debit = opening + sum((r['debit'] for r in rows), Decimal('0.00'))
    total_credit = sum((r['credit'] for r in rows), Decimal('0.00'))
    closing = total_debit - total_credit

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=18*mm, leftMargin=18*mm,
        topMargin=15*mm, bottomMargin=15*mm,
        title="Ledger Statement - %s" % customer.name,
        author=business.name if business else 'DukaanFlow',
    )
    styles = getSampleStyleSheet()
    normal_style = ParagraphStyle(
        'LedgerNormal', parent=styles['Normal'], fontSize=9, leading=13,
        textColor=colors.HexColor('#334155'))
    cell_style = ParagraphStyle(
        'LedgerCell', parent=styles['Normal'], fontSize=8.5, leading=11.5,
        textColor=colors.HexColor('#334155'))
    bold_style = ParagraphStyle(
        'LedgerBold', parent=styles['Normal'], fontSize=9, leading=13,
        textColor=colors.HexColor('#0F172A'), fontName='Helvetica-Bold')
    footer_style = ParagraphStyle(
        'LedgerFooter', parent=styles['Normal'], fontSize=8, leading=11,
        textColor=colors.HexColor('#64748B'), alignment=1)

    elements = []

    # ---- Header -----------------------------------------------------------
    shop_info = ""
    if business:
        shop_info = "<b>%s</b><br/>" % business.name
        if business.address:
            shop_info += "%s<br/>" % business.address
        if business.city or business.state:
            shop_info += "%s, %s - %s<br/>" % (
                business.city or '', business.state or '', business.pincode or '')
        if business.phone:
            shop_info += "Phone: %s<br/>" % business.phone
        if business.email:
            shop_info += "Email: %s" % business.email
        if business.gstin:
            shop_info += "<br/><b>GSTIN: %s</b>" % business.gstin

    if from_date or to_date:
        period = "%s to %s" % (
            from_date.strftime('%d-%m-%Y') if from_date else 'Beginning',
            to_date.strftime('%d-%m-%Y') if to_date else 'Till date')
    else:
        period = "Full account history"

    meta = "<b>LEDGER / KHATA STATEMENT</b><br/>"
    meta += "<b>Statement Period:</b> %s<br/>" % period
    meta += "<b>Generated On:</b> %s<br/>" % timezone.now().strftime('%d-%m-%Y %I:%M %p')
    meta += "<b>Closing Balance:</b> %s" % format_inr(closing)

    header_table = Table(
        [[Paragraph(shop_info, normal_style), Paragraph(meta, normal_style)]],
        colWidths=[95*mm, 79*mm])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 8))
    elements.append(HRFlowable(width="100%", thickness=1,
                               color=colors.HexColor('#CBD5E1'), spaceAfter=8))

    # ---- Customer block ---------------------------------------------------
    cust_info = "<b>CUSTOMER:</b> %s<br/>Mobile: %s<br/>" % (customer.name, customer.phone)
    if customer.address:
        cust_info += "Address: %s<br/>" % customer.address
    if customer.email:
        cust_info += "Email: %s" % customer.email
    elements.append(Paragraph(cust_info, normal_style))
    elements.append(Spacer(1, 10))

    # ---- Ledger table -----------------------------------------------------
    table_data = [[
        Paragraph("<b>Date</b>", bold_style),
        Paragraph("<b>Particulars</b>", bold_style),
        Paragraph("<b>Debit (Invoice)</b>", bold_style),
        Paragraph("<b>Credit (Paid)</b>", bold_style),
        Paragraph("<b>Balance Due</b>", bold_style),
    ]]

    if not rows and (from_date or to_date):
        table_data.append([
            Paragraph("-", cell_style),
            Paragraph("<i>No transactions in the selected period.</i>", cell_style),
            Paragraph("-", cell_style),
            Paragraph("-", cell_style),
            Paragraph(format_inr(opening), cell_style),
        ])
    else:
        if opening != 0:
            table_data.append([
                Paragraph(from_date.strftime('%d-%m-%Y') if from_date else '-', cell_style),
                Paragraph("<b>Opening balance carried forward</b>", cell_style),
                Paragraph(format_inr(opening) if opening > 0 else '-', cell_style),
                Paragraph(format_inr(-opening) if opening < 0 else '-', cell_style),
                Paragraph(format_inr(opening), cell_style),
            ])
        for r in rows:
            table_data.append([
                Paragraph(r['date'].strftime('%d-%m-%Y'), cell_style),
                Paragraph(r['particulars'], cell_style),
                Paragraph(format_inr(r['debit']) if r['debit'] else '-', cell_style),
                Paragraph(format_inr(r['credit']) if r['credit'] else '-', cell_style),
                Paragraph(format_inr(r['balance']), cell_style),
            ])

    ledger_table = Table(
        table_data,
        colWidths=[22*mm, 66*mm, 28*mm, 28*mm, 30*mm],
        repeatRows=1)
    ledger_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F1F5F9')),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(ledger_table)
    elements.append(Spacer(1, 10))

    # ---- Summary ----------------------------------------------------------
    closing_color = '#DC2626' if closing > 0 else '#059669'
    summary_data = [
        [Paragraph("<b>Total Invoices (incl. opening):</b>", bold_style),
         Paragraph("<b>%s</b>" % format_inr(total_debit), bold_style)],
        [Paragraph("<b>Total Payments Received:</b>", bold_style),
         Paragraph("<b>%s</b>" % format_inr(total_credit), bold_style)],
        [Paragraph("<b>Closing Balance Payable by %s:</b>" % customer.name, bold_style),
         Paragraph("<font color='%s'><b>%s</b></font>" % (closing_color, format_inr(closing)),
                   bold_style)],
    ]
    summary_table = Table(summary_data, colWidths=[120*mm, 54*mm])
    summary_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LINEABOVE', (0, 0), (-1, 0), 0.75, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 14))

    elements.append(HRFlowable(width="100%", thickness=0.75,
                               color=colors.HexColor('#E2E8F0'), spaceAfter=6))
    elements.append(Paragraph(
        "This is a computer-generated ledger statement from DukaanFlow POS. "
        "Amounts are computed from the shop's recorded invoices and payments.",
        footer_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer
