import io
from decimal import Decimal
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, HRFlowable
from core.utils import format_inr

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
