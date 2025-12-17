"""
E-Mail Service für Rechnungsversand
"""
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from .zugferd import generate_zugferd_pdf
from .xrechnung import generate_xrechnung


def send_invoice_email(invoice, recipient_email: str = None) -> bool:
    """
    Versendet eine Rechnung per E-Mail.
    
    Args:
        invoice: Invoice Objekt
        recipient_email: Optional - überschreibt Kunden-E-Mail
    
    Returns:
        bool: True wenn erfolgreich
    """
    to_email = recipient_email or invoice.customer.email
    
    if not to_email:
        raise ValueError("Keine E-Mail-Adresse vorhanden")
    
    tenant = invoice.tenant
    subject = f"Rechnung {invoice.invoice_number} von {tenant.name}"
    
    # E-Mail Body
    body = f"""Sehr geehrte Damen und Herren,

anbei erhalten Sie die Rechnung {invoice.invoice_number}.

Rechnungsdatum: {invoice.invoice_date.strftime('%d.%m.%Y')}
Fällig bis: {invoice.due_date.strftime('%d.%m.%Y')}
Betrag: {invoice.total:.2f} €

Bitte überweisen Sie den Betrag auf folgendes Konto:
Bank: {tenant.bank_name or '-'}
IBAN: {tenant.iban or '-'}
BIC: {tenant.bic or '-'}
Verwendungszweck: {invoice.invoice_number}

Bei Fragen stehen wir Ihnen gerne zur Verfügung.

Mit freundlichen Grüßen
{tenant.name}

--
{tenant.street}
{tenant.zip_code} {tenant.city}
Tel: {tenant.phone or '-'}
E-Mail: {tenant.email or '-'}
"""
    
    email = EmailMessage(
        subject=subject,
        body=body,
        from_email=f"{tenant.name} <{tenant.email}>" if tenant.email else None,
        to=[to_email],
    )
    
    # Anhang je nach Format
    if invoice.format == 'zugferd':
        pdf_content = generate_zugferd_pdf(invoice)
        email.attach(
            f"{invoice.invoice_number}.pdf",
            pdf_content,
            'application/pdf'
        )
    else:
        xml_content = generate_xrechnung(invoice)
        email.attach(
            f"{invoice.invoice_number}.xml",
            xml_content,
            'application/xml'
        )
    
    email.send(fail_silently=False)
    return True