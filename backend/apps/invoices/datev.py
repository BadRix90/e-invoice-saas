"""
DATEV Export Generator
CSV-Format für Buchhalter/Steuerberater
"""
import csv
import io
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from .models import Invoice


def generate_datev_export(invoices: List['Invoice']) -> str:
    """
    Generiert DATEV-kompatibles CSV für Buchungsstapel.
    Format: DATEV Buchungsstapel (ASCII)
    """
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_MINIMAL)
    
    # DATEV Header
    writer.writerow([
        'Umsatz (ohne Soll/Haben-Kz)',
        'Soll/Haben-Kennzeichen',
        'WKZ Umsatz',
        'Kurs',
        'Basis-Umsatz',
        'WKZ Basis-Umsatz',
        'Konto',
        'Gegenkonto (ohne BU-Schlüssel)',
        'BU-Schlüssel',
        'Belegdatum',
        'Belegfeld 1',
        'Belegfeld 2',
        'Skonto',
        'Buchungstext',
        'Postensperre',
        'Diverse Adressnummer',
        'Geschäftspartnerbank',
        'Sachverhalt',
        'Zinssperre',
        'Beleglink',
        'Beleginfo - Art 1',
        'Beleginfo - Inhalt 1',
        'Beleginfo - Art 2',
        'Beleginfo - Inhalt 2',
        'Beleginfo - Art 3',
        'Beleginfo - Inhalt 3',
        'Beleginfo - Art 4',
        'Beleginfo - Inhalt 4',
        'Beleginfo - Art 5',
        'Beleginfo - Inhalt 5',
        'Beleginfo - Art 6',
        'Beleginfo - Inhalt 6',
        'Beleginfo - Art 7',
        'Beleginfo - Inhalt 7',
        'Beleginfo - Art 8',
        'Beleginfo - Inhalt 8',
        'KOST1 - Kostenstelle',
        'KOST2 - Kostenstelle',
        'Kost-Menge',
        'EU-Land u. UStID',
        'EU-Steuersatz',
        'Abw. Versteuerungsart',
        'Sachverhalt L+L',
        'Funktionsergänzung L+L',
        'BU 49 Hauptfunktionstyp',
        'BU 49 Hauptfunktionsnummer',
        'BU 49 Funktionsergänzung',
        'Zusatzinformation - Art 1',
        'Zusatzinformation - Inhalt 1',
        'Zusatzinformation - Art 2',
        'Zusatzinformation - Inhalt 2',
        'Zusatzinformation - Art 3',
        'Zusatzinformation - Inhalt 3',
        'Zusatzinformation - Art 4',
        'Zusatzinformation - Inhalt 4',
        'Zusatzinformation - Art 5',
        'Zusatzinformation - Inhalt 5',
        'Zusatzinformation - Art 6',
        'Zusatzinformation - Inhalt 6',
        'Zusatzinformation - Art 7',
        'Zusatzinformation - Inhalt 7',
        'Zusatzinformation - Art 8',
        'Zusatzinformation - Inhalt 8',
        'Zusatzinformation - Art 9',
        'Zusatzinformation - Inhalt 9',
        'Zusatzinformation - Art 10',
        'Zusatzinformation - Inhalt 10',
        'Zusatzinformation - Art 11',
        'Zusatzinformation - Inhalt 11',
        'Zusatzinformation - Art 12',
        'Zusatzinformation - Inhalt 12',
        'Zusatzinformation - Art 13',
        'Zusatzinformation - Inhalt 13',
        'Zusatzinformation - Art 14',
        'Zusatzinformation - Inhalt 14',
        'Zusatzinformation - Art 15',
        'Zusatzinformation - Inhalt 15',
        'Zusatzinformation - Art 16',
        'Zusatzinformation - Inhalt 16',
        'Zusatzinformation - Art 17',
        'Zusatzinformation - Inhalt 17',
        'Zusatzinformation - Art 18',
        'Zusatzinformation - Inhalt 18',
        'Zusatzinformation - Art 19',
        'Zusatzinformation - Inhalt 19',
        'Zusatzinformation - Art 20',
        'Zusatzinformation - Inhalt 20',
        'Stück',
        'Gewicht',
        'Zahlweise',
        'Fälligkeit',
        'Skontotyp',
        'Auftragsnummer',
        'Buchungstyp',
        'USt-Schlüssel (Anzahlungen)',
        'EU-Land (Anzahlungen)',
        'Sachverhalt L+L (Anzahlungen)',
        'EU-Steuersatz (Anzahlungen)',
        'Erlöskonto (Anzahlungen)',
        'Herkunft-Kz',
        'Buchungs GUID',
        'KOST-Datum',
        'SEPA-Mandatsreferenz',
        'Skontosperre',
        'Gesellschaftername',
        'Beteiligtennummer',
        'Identifikationsnummer',
        'Zeichnernummer',
        'Postensperre bis',
        'Bezeichnung SoBil-Sachverhalt',
        'Kennzeichen SoBil-Buchung',
        'Festschreibung',
        'Leistungsdatum',
        'Datum Zuord. Steuerperiode',
        'Fälligkeit',
        'Generalumkehr (GU)',
        'Steuersatz',
        'Land',
    ])
    
    for invoice in invoices:
        if invoice.status == 'draft':
            continue
            
        # Debitorenkonto aus Kundennummer (10000 + ID)
        debitor_konto = 10000 + invoice.customer.id
        
        # Erlöskonto (Standard: 8400 für Erlöse 19% USt)
        erlos_konto = _get_erlos_konto(invoice)
        
        # Belegdatum formatieren (DDMM)
        beleg_datum = invoice.invoice_date.strftime('%d%m')
        
        # Bruttobetrag
        umsatz = f"{invoice.total:.2f}".replace('.', ',')
        
        writer.writerow([
            umsatz,                          # Umsatz
            'S',                             # Soll
            'EUR',                           # Währung
            '',                              # Kurs
            '',                              # Basis-Umsatz
            '',                              # WKZ Basis
            debitor_konto,                   # Konto (Debitor)
            erlos_konto,                     # Gegenkonto (Erlös)
            '',                              # BU-Schlüssel
            beleg_datum,                     # Belegdatum
            invoice.invoice_number,          # Belegfeld 1
            '',                              # Belegfeld 2
            '',                              # Skonto
            f"RE {invoice.customer.display_name[:20]}",  # Buchungstext
            '',                              # Postensperre
            '',                              # Diverse Adressnummer
            '',                              # Geschäftspartnerbank
            '',                              # Sachverhalt
            '',                              # Zinssperre
            '',                              # Beleglink
            # Rest leer...
            '', '', '', '', '', '', '', '', '', '',
            '', '', '', '', '', '', '', '', '', '',
            '', '', '', '', '', '', '', '', '', '',
            '', '', '', '', '', '', '', '', '', '',
            '', '', '', '', '', '', '', '', '', '',
            '', '', '', '', '', '', '', '', '', '',
            '', '', '', '', '', '', '', '', '', '',
            '', '', '', '', '', '', '', '', '', '',
            '', '', '', '', '', '', '', '', '', '',
            '', '', '', '',
        ])
    
    return output.getvalue()


def generate_datev_simple(invoices: List['Invoice']) -> str:
    """
    Vereinfachtes DATEV-Format für einfachen Import.
    """
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_MINIMAL)
    
    # Header
    writer.writerow([
        'Rechnungsnummer',
        'Rechnungsdatum',
        'Fälligkeitsdatum',
        'Kundenname',
        'Kundennummer',
        'Nettobetrag',
        'MwSt-Betrag',
        'MwSt-Satz',
        'Bruttobetrag',
        'Währung',
        'Status',
        'Zahlungsbedingungen',
    ])
    
    for invoice in invoices:
        if invoice.status == 'draft':
            continue
        
        # Haupt-MwSt-Satz ermitteln
        vat_rate = Decimal('19')
        if invoice.items.exists():
            vat_rate = invoice.items.first().vat_rate
        
        writer.writerow([
            invoice.invoice_number,
            invoice.invoice_date.strftime('%d.%m.%Y'),
            invoice.due_date.strftime('%d.%m.%Y') if invoice.due_date else '',
            invoice.customer.display_name,
            invoice.customer.customer_number or '',
            f"{invoice.subtotal:.2f}".replace('.', ','),
            f"{invoice.tax_amount:.2f}".replace('.', ','),
            f"{vat_rate:.0f}",
            f"{invoice.total:.2f}".replace('.', ','),
            'EUR',
            invoice.get_status_display(),
            invoice.payment_terms or '',
        ])
    
    return output.getvalue()


def _get_erlos_konto(invoice: 'Invoice') -> int:
    """Ermittelt das Erlöskonto basierend auf MwSt-Satz."""
    if not invoice.items.exists():
        return 8400  # Standard 19%
    
    vat_rate = invoice.items.first().vat_rate
    
    if vat_rate == Decimal('19'):
        return 8400  # Erlöse 19% USt
    elif vat_rate == Decimal('7'):
        return 8300  # Erlöse 7% USt
    elif vat_rate == Decimal('0'):
        return 8100  # Steuerfreie Erlöse
    else:
        return 8400  # Fallback