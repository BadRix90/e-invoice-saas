"""
ZUGFeRD 2.1 / Factur-X PDF Generator
PDF/A-3 mit eingebettetem XRechnung XML
"""
import io
import os
from datetime import date
from decimal import Decimal
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pypdf import PdfReader, PdfWriter
from django.conf import settings
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import Invoice

from .xrechnung import generate_xrechnung


def generate_zugferd_pdf(invoice: 'Invoice') -> bytes:
    """Generiert ZUGFeRD 2.1 PDF mit eingebettetem XML."""
    
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=10*mm,
        bottomMargin=20*mm
    )
    
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='InvoiceTitle',
        fontSize=18,
        spaceAfter=10*mm,
        fontName='Helvetica-Bold'
    ))
    
    elements = []
    tenant = invoice.tenant
    customer = invoice.customer
    
    # Logo + Absender Header
    logo_path = tenant.logo.path if tenant.logo else None
    
    sender_text = f"""
    <b>{tenant.name}</b><br/>
    {tenant.street}<br/>
    {tenant.zip_code} {tenant.city}<br/>
    USt-IdNr.: {tenant.vat_id or '-'}
    """
    
    if logo_path and os.path.exists(logo_path):
    # Logo mit Seitenverhältnis berechnen
        from reportlab.lib.utils import ImageReader
        img = ImageReader(logo_path)
        img_width, img_height = img.getSize()
        aspect = img_height / img_width
        
        logo_width = 50*mm
        logo_height = logo_width * aspect
        
        # Max-Höhe begrenzen
        if logo_height > 20*mm:
            logo_height = 20*mm
            logo_width = logo_height / aspect
        
        logo = Image(logo_path, width=logo_width, height=logo_height)
        logo.hAlign = 'RIGHT'
        
        header_table = Table(
            [[Paragraph(sender_text, styles['Normal']), logo]],
            colWidths=[110*mm, 60*mm]
        )
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ]))
        elements.append(header_table)
    else:
        elements.append(Paragraph(sender_text, styles['Normal']))
    
    elements.append(Spacer(1, 15*mm))
    
    # Rest bleibt gleich...
    # Empfänger
    recipient_text = f"""
    <b>{customer.display_name}</b><br/>
    {customer.street}<br/>
    {customer.zip_code} {customer.city}
    """
    elements.append(Paragraph(recipient_text, styles['Normal']))
    elements.append(Spacer(1, 15*mm))
    
    # Rechnungstitel
    elements.append(Paragraph(f"Rechnung {invoice.invoice_number}", styles['InvoiceTitle']))
    
    # Rechnungsdetails
    details = f"""
    Rechnungsdatum: {invoice.invoice_date.strftime('%d.%m.%Y')}<br/>
    Fällig bis: {invoice.due_date.strftime('%d.%m.%Y') if invoice.due_date else '-'}<br/>
    Kundennummer: {customer.customer_number or '-'}
    """
    elements.append(Paragraph(details, styles['Normal']))
    elements.append(Spacer(1, 10*mm))
    
    # Positionstabelle
    table_data = [['Pos.', 'Beschreibung', 'Menge', 'Einheit', 'Einzelpreis', 'MwSt', 'Gesamt']]
    
    for item in invoice.items.all():
        table_data.append([
            str(item.position),
            item.description,
            f"{item.quantity:.2f}",
            item.unit,
            f"{item.unit_price:.2f} €",
            f"{item.vat_rate:.0f}%",
            f"{item.line_total:.2f} €"
        ])
    
    table = Table(table_data, colWidths=[12*mm, 60*mm, 18*mm, 18*mm, 25*mm, 15*mm, 25*mm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f0f0f0')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 10*mm))
    
    # Summen
    summary_data = [
        ['Nettobetrag:', f"{invoice.subtotal:.2f} €"],
        ['MwSt:', f"{invoice.tax_amount:.2f} €"],
        ['Gesamtbetrag:', f"{invoice.total:.2f} €"],
    ]
    summary_table = Table(summary_data, colWidths=[140*mm, 30*mm])
    summary_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 15*mm))
    
    # Zahlungsinformationen
    payment_text = f"""
    <b>Zahlungsinformationen</b><br/>
    {invoice.payment_terms or 'Zahlbar sofort'}<br/><br/>
    Bankverbindung:<br/>
    IBAN: {tenant.iban or '-'}<br/>
    BIC: {tenant.bic or '-'}
    """
    elements.append(Paragraph(payment_text, styles['Normal']))
    elements.append(Spacer(1, 10*mm))
    
    # Footer
    footer_text = f"""
    <font size="8" color="grey">
    {tenant.name} | {tenant.street} | {tenant.zip_code} {tenant.city}<br/>
    Tel: {tenant.phone or '-'} | E-Mail: {tenant.email or '-'}<br/>
    USt-IdNr.: {tenant.vat_id or '-'}
    </font>
    """
    elements.append(Paragraph(footer_text, styles['Normal']))
    
    doc.build(elements)
    pdf_buffer.seek(0)
    
    xml_content = generate_xrechnung(invoice)
    pdf_with_xml = _embed_xml_in_pdf(pdf_buffer.getvalue(), xml_content, invoice.invoice_number)
    
    return pdf_with_xml


def _embed_xml_in_pdf(pdf_bytes: bytes, xml_content: str, invoice_number: str) -> bytes:
    """Bettet XRechnung XML als Anhang in PDF ein."""
    reader = PdfReader(io.BytesIO(pdf_bytes))
    writer = PdfWriter()
    
    for page in reader.pages:
        writer.add_page(page)
    
    writer.add_attachment(
        filename="factur-x.xml",
        data=xml_content.encode('utf-8')
    )
    
    writer.add_metadata({
        '/Title': f'Rechnung {invoice_number}',
        '/Subject': 'ZUGFeRD 2.1 / Factur-X Rechnung',
        '/Creator': 'E-Invoice Generator',
        '/Producer': 'ReportLab + pypdf',
    })
    
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()