"""
GoBD-Archivierung für Rechnungen
- Verschlüsselte Speicherung
- SHA-256 Integritätsprüfung
"""

import hashlib
import json
import zipfile
from io import BytesIO

from cryptography.fernet import Fernet
from django.conf import settings
from django.utils import timezone
from requests import Response



def get_encryption_key():
    key = getattr(settings, 'ARCHIVE_ENCRYPTION_KEY', '')

    if not key:
        return Fernet.generate_key()

    if len(key) != 44:
        import base64
        hash_bytes = hashlib.sha256(key.encode()).digest()
        return base64.urlsafe_b64encode(hash_bytes)

    return key.encode()


def calculate_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encrypt_data(data: bytes) -> bytes:
    fernet = Fernet(get_encryption_key())
    return fernet.encrypt(data)


def decrypt_data(encrypted_data: bytes) -> bytes:
    fernet = Fernet(get_encryption_key())
    return fernet.decrypt(encrypted_data)


def create_archive_zip(invoice) -> bytes:
    buffer = BytesIO()

    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        metadata = {
            'invoice_number': invoice.invoice_number,
            'invoice_date': str(invoice.invoice_date),
            'due_date': str(invoice.due_date),
            'status': invoice.status,
            'format': invoice.format,
            'customer': {
                'name': invoice.customer.company_name,
                'email': invoice.customer.email,
            },
            'subtotal': str(invoice.subtotal),
            'tax_amount': str(invoice.tax_amount),
            'total': str(invoice.total),
            'items': [
                {
                    'description': item.description,
                    'quantity': str(item.quantity),
                    'unit_price': str(item.unit_price),
                    'vat_rate': str(item.vat_rate),
                    'total': str(item.line_total),
                }
                for item in invoice.items.all()
            ],
            'archived_at': timezone.now().isoformat(),
        }

        zf.writestr('metadata.json', json.dumps(
            metadata, indent=2, ensure_ascii=False))

        if invoice.pdf_file:
            try:
                invoice.pdf_file.seek(0)
                zf.writestr('invoice.pdf', invoice.pdf_file.read())
            except Exception:
                pass

        if invoice.xml_file:
            try:
                invoice.xml_file.seek(0)
                zf.writestr('invoice.xml', invoice.xml_file.read())
            except Exception:
                pass

    return buffer.getvalue()


def archive_invoice(invoice) -> dict:
    from .models import InvoiceArchive

    if invoice.archived_at:
        raise ValueError(
            f"Rechnung {invoice.invoice_number} ist bereits archiviert.")

    if invoice.status == 'draft':
        raise ValueError("Entwürfe können nicht archiviert werden.")

    zip_data = create_archive_zip(invoice)
    data_hash = calculate_hash(zip_data)
    encrypted_data = encrypt_data(zip_data)

    archive = InvoiceArchive.objects.create(
        invoice=invoice,
        encrypted_data=encrypted_data,
        data_hash=data_hash,
        file_size=len(zip_data),
    )

    invoice.archived_at = timezone.now()
    invoice.archive_hash = data_hash
    invoice.save(update_fields=['archived_at', 'archive_hash'])

    return {
        'archive_id': archive.id,
        'hash': data_hash,
        'archived_at': invoice.archived_at.isoformat(),
        'file_size': len(zip_data),
    }


def verify_archive(invoice) -> dict:
    from .models import InvoiceArchive

    if not invoice.archived_at:
        return {'valid': False, 'error': 'Rechnung ist nicht archiviert.'}

    try:
        archive = InvoiceArchive.objects.get(invoice=invoice)
    except InvoiceArchive.DoesNotExist:
        return {'valid': False, 'error': 'Archiv-Eintrag nicht gefunden.'}

    try:
        decrypted_data = decrypt_data(archive.encrypted_data)
    except Exception as e:
        return {'valid': False, 'error': f'Entschlüsselung fehlgeschlagen: {e}'}

    current_hash = calculate_hash(decrypted_data)

    if current_hash != archive.data_hash:
        return {
            'valid': False,
            'error': 'Daten wurden manipuliert!',
            'expected_hash': archive.data_hash,
            'actual_hash': current_hash,
        }

    return {
        'valid': True,
        'hash': current_hash,
        'archived_at': archive.created_at.isoformat(),
        'file_size': archive.file_size,
    }


def download_archive(invoice) -> bytes:
    from .models import InvoiceArchive

    if not invoice.archived_at:
        return None

    try:
        archive = InvoiceArchive.objects.get(invoice=invoice)
        return decrypt_data(archive.encrypted_data)
    except Exception:
        return None

