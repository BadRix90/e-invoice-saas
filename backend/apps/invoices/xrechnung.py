"""
XRechnung Generator - EN 16931 / CII Format
Generiert XML nach Cross-Industry Invoice (CII) D16B Standard
"""
import xml.etree.ElementTree as ET
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import Invoice

# Namespaces für CII (Cross-Industry Invoice)
NAMESPACES = {
    'rsm': 'urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100',
    'ram': 'urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100',
    'qdt': 'urn:un:unece:uncefact:data:standard:QualifiedDataType:100',
    'udt': 'urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100',
}

# Registriere Namespaces
for prefix, uri in NAMESPACES.items():
    ET.register_namespace(prefix, uri)


def _ns(tag: str) -> str:
    """Erstellt vollqualifizierten Tag-Namen mit Namespace."""
    prefix, local = tag.split(':')
    return f'{{{NAMESPACES[prefix]}}}{local}'


def _add_text_element(parent: ET.Element, tag: str, text: str) -> ET.Element:
    """Fügt ein Text-Element hinzu."""
    elem = ET.SubElement(parent, _ns(tag))
    elem.text = str(text)
    return elem


def _add_id_element(parent: ET.Element, tag: str, value: str, scheme_id: str = None) -> ET.Element:
    """Fügt ein ID-Element mit optionalem schemeID hinzu."""
    elem = ET.SubElement(parent, _ns(tag))
    elem.text = str(value)
    if scheme_id:
        elem.set('schemeID', scheme_id)
    return elem


def _add_amount_element(parent: ET.Element, tag: str, amount: Decimal, currency: str = 'EUR') -> ET.Element:
    """Fügt ein Betrags-Element hinzu."""
    elem = ET.SubElement(parent, _ns(tag))
    elem.text = f'{amount:.2f}'
    elem.set('currencyID', currency)
    return elem


def _add_date_element(parent: ET.Element, tag: str, dt: date) -> ET.Element:
    """Fügt ein Datums-Element hinzu."""
    date_elem = ET.SubElement(parent, _ns(tag))
    _add_text_element(date_elem, 'udt:DateTimeString', dt.strftime('%Y%m%d')).set('format', '102')
    return date_elem


def _format_tax_rate(rate: Decimal) -> str:
    """Formatiert MwSt-Satz."""
    return f'{rate:.2f}'


class XRechnungGenerator:
    """Generator für XRechnung XML (CII Format)."""
    
    def __init__(self, invoice: 'Invoice'):
        self.invoice = invoice
        self.tenant = invoice.tenant
        self.customer = invoice.customer
        
    def generate(self) -> str:
        """Generiert das komplette XRechnung XML."""
        root = self._create_root()
        
        self._add_document_context(root)
        self._add_exchanged_document(root)
        self._add_supply_chain_trade_transaction(root)
        
        # XML als String
        ET.indent(root, space="  ")
        xml_declaration = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml_body = ET.tostring(root, encoding='unicode')
        
        return xml_declaration + xml_body
    
    def _create_root(self) -> ET.Element:
        """Erstellt das Root-Element."""
        return ET.Element(_ns('rsm:CrossIndustryInvoice'))
    
    def _add_document_context(self, root: ET.Element) -> None:
        """Fügt ExchangedDocumentContext hinzu (BG-2)."""
        context = ET.SubElement(root, _ns('rsm:ExchangedDocumentContext'))
        
        # Business Process (BT-23) - XRechnung
        bp = ET.SubElement(context, _ns('ram:BusinessProcessSpecifiedDocumentContextParameter'))
        _add_id_element(bp, 'ram:ID', 'urn:fdc:peppol.eu:2017:poacc:billing:01:1.0')
        
        # Guideline (BT-24) - XRechnung 3.0
        guide = ET.SubElement(context, _ns('ram:GuidelineSpecifiedDocumentContextParameter'))
        _add_id_element(guide, 'ram:ID', 'urn:cen.eu:en16931:2017#compliant#urn:xeinkauf.de:kosit:xrechnung_3.0')
    
    def _add_exchanged_document(self, root: ET.Element) -> None:
        """Fügt ExchangedDocument hinzu (BG-1)."""
        doc = ET.SubElement(root, _ns('rsm:ExchangedDocument'))
        
        # Rechnungsnummer (BT-1)
        _add_text_element(doc, 'ram:ID', self.invoice.invoice_number)
        
        # Rechnungstyp (BT-3) - 380 = Commercial Invoice
        _add_text_element(doc, 'ram:TypeCode', '380')
        
        # Rechnungsdatum (BT-2)
        _add_date_element(doc, 'ram:IssueDateTime', self.invoice.invoice_date)
        
        # Notizen (BT-22)
        if self.invoice.notes:
            note = ET.SubElement(doc, _ns('ram:IncludedNote'))
            _add_text_element(note, 'ram:Content', self.invoice.notes)
    
    def _add_supply_chain_trade_transaction(self, root: ET.Element) -> None:
        """Fügt SupplyChainTradeTransaction hinzu."""
        transaction = ET.SubElement(root, _ns('rsm:SupplyChainTradeTransaction'))
        
        # Positionen
        for item in self.invoice.items.all():
            self._add_line_item(transaction, item)
        
        # Header Trade Agreement (Verkäufer/Käufer)
        self._add_header_trade_agreement(transaction)
        
        # Header Trade Delivery
        self._add_header_trade_delivery(transaction)
        
        # Header Trade Settlement (Zahlungsbedingungen, Summen)
        self._add_header_trade_settlement(transaction)
    
    def _add_line_item(self, transaction: ET.Element, item) -> None:
        """Fügt eine Rechnungsposition hinzu (BG-25)."""
        line = ET.SubElement(transaction, _ns('ram:IncludedSupplyChainTradeLineItem'))
        
        # Positionsnummer (BT-126)
        doc = ET.SubElement(line, _ns('ram:AssociatedDocumentLineDocument'))
        _add_text_element(doc, 'ram:LineID', str(item.position))
        
        # Produkt (BG-31)
        product = ET.SubElement(line, _ns('ram:SpecifiedTradeProduct'))
        if item.sku:
            _add_id_element(product, 'ram:SellerAssignedID', item.sku)
        _add_text_element(product, 'ram:Name', item.description)
        
        # Preis (BG-29)
        agreement = ET.SubElement(line, _ns('ram:SpecifiedLineTradeAgreement'))
        price = ET.SubElement(agreement, _ns('ram:NetPriceProductTradePrice'))
        _add_amount_element(price, 'ram:ChargeAmount', item.unit_price)
        
        # Menge (BT-129, BT-130)
        delivery = ET.SubElement(line, _ns('ram:SpecifiedLineTradeDelivery'))
        qty = ET.SubElement(delivery, _ns('ram:BilledQuantity'))
        qty.text = f'{item.quantity:.3f}'
        qty.set('unitCode', item.unit)
        
        # Steuer & Summe
        settlement = ET.SubElement(line, _ns('ram:SpecifiedLineTradeSettlement'))
        
        # MwSt der Position (BG-30)
        tax = ET.SubElement(settlement, _ns('ram:ApplicableTradeTax'))
        _add_text_element(tax, 'ram:TypeCode', 'VAT')
        _add_text_element(tax, 'ram:CategoryCode', self._get_tax_category(item.vat_rate))
        _add_text_element(tax, 'ram:RateApplicablePercent', _format_tax_rate(item.vat_rate))
        
        # Positionssumme (BT-131)
        summation = ET.SubElement(settlement, _ns('ram:SpecifiedTradeSettlementLineMonetarySummation'))
        _add_amount_element(summation, 'ram:LineTotalAmount', item.line_total)
    
    def _add_header_trade_agreement(self, transaction: ET.Element) -> None:
        """Fügt Verkäufer und Käufer hinzu (BG-4, BG-7)."""
        agreement = ET.SubElement(transaction, _ns('ram:ApplicableHeaderTradeAgreement'))
        
        # Buyer Reference / Leitweg-ID (BT-10)
        if self.invoice.leitweg_id:
            _add_text_element(agreement, 'ram:BuyerReference', self.invoice.leitweg_id)
        elif self.invoice.buyer_reference:
            _add_text_element(agreement, 'ram:BuyerReference', self.invoice.buyer_reference)
        
        # Verkäufer (BG-4)
        seller = ET.SubElement(agreement, _ns('ram:SellerTradeParty'))
        _add_text_element(seller, 'ram:Name', self.tenant.name)
        
        # Verkäufer-Adresse (BG-5)
        seller_addr = ET.SubElement(seller, _ns('ram:PostalTradeAddress'))
        if self.tenant.street:
            _add_text_element(seller_addr, 'ram:LineOne', self.tenant.street)
        if self.tenant.zip_code:
            _add_text_element(seller_addr, 'ram:PostcodeCode', self.tenant.zip_code)
        if self.tenant.city:
            _add_text_element(seller_addr, 'ram:CityName', self.tenant.city)
        _add_text_element(seller_addr, 'ram:CountryID', self.tenant.country or 'DE')
        
        # Verkäufer-Steuer (BG-6)
        if self.tenant.vat_id:
            seller_tax = ET.SubElement(seller, _ns('ram:SpecifiedTaxRegistration'))
            _add_id_element(seller_tax, 'ram:ID', self.tenant.vat_id, 'VA')
        
        # Käufer (BG-7)
        buyer = ET.SubElement(agreement, _ns('ram:BuyerTradeParty'))
        _add_text_element(buyer, 'ram:Name', self.customer.display_name)
        
        # Käufer-Adresse (BG-8)
        buyer_addr = ET.SubElement(buyer, _ns('ram:PostalTradeAddress'))
        _add_text_element(buyer_addr, 'ram:LineOne', self.customer.street)
        _add_text_element(buyer_addr, 'ram:PostcodeCode', self.customer.zip_code)
        _add_text_element(buyer_addr, 'ram:CityName', self.customer.city)
        _add_text_element(buyer_addr, 'ram:CountryID', self.customer.country)
        
        # Käufer E-Mail (BT-49)
        if self.customer.email:
            buyer_contact = ET.SubElement(buyer, _ns('ram:URIUniversalCommunication'))
            _add_id_element(buyer_contact, 'ram:URIID', self.customer.email, 'EM')
        
        # Käufer-Steuer
        if self.customer.vat_id:
            buyer_tax = ET.SubElement(buyer, _ns('ram:SpecifiedTaxRegistration'))
            _add_id_element(buyer_tax, 'ram:ID', self.customer.vat_id, 'VA')
    
    def _add_header_trade_delivery(self, transaction: ET.Element) -> None:
        """Fügt Lieferinformationen hinzu (BG-13)."""
        delivery = ET.SubElement(transaction, _ns('ram:ApplicableHeaderTradeDelivery'))
        
        # Lieferdatum = Rechnungsdatum
        event = ET.SubElement(delivery, _ns('ram:ActualDeliverySupplyChainEvent'))
        _add_date_element(event, 'ram:OccurrenceDateTime', self.invoice.invoice_date)
    
    def _add_header_trade_settlement(self, transaction: ET.Element) -> None:
        """Fügt Zahlungsbedingungen und Summen hinzu."""
        settlement = ET.SubElement(transaction, _ns('ram:ApplicableHeaderTradeSettlement'))
        
        # Währung (BT-5)
        _add_text_element(settlement, 'ram:InvoiceCurrencyCode', 'EUR')
        
        # Zahlungsbedingungen (BT-20)
        if self.invoice.payment_terms:
            terms = ET.SubElement(settlement, _ns('ram:SpecifiedTradePaymentTerms'))
            _add_text_element(terms, 'ram:Description', self.invoice.payment_terms)
            if self.invoice.due_date:
                _add_date_element(terms, 'ram:DueDateDateTime', self.invoice.due_date)
        
        # MwSt-Aufschlüsselung (BG-23)
        vat_summary = self._calculate_vat_summary()
        for rate, data in vat_summary.items():
            tax = ET.SubElement(settlement, _ns('ram:ApplicableTradeTax'))
            _add_amount_element(tax, 'ram:CalculatedAmount', data['tax'])
            _add_text_element(tax, 'ram:TypeCode', 'VAT')
            _add_amount_element(tax, 'ram:BasisAmount', data['net'])
            _add_text_element(tax, 'ram:CategoryCode', self._get_tax_category(Decimal(rate)))
            _add_text_element(tax, 'ram:RateApplicablePercent', rate)
        
        # Gesamtsummen (BG-22)
        summation = ET.SubElement(settlement, _ns('ram:SpecifiedTradeSettlementHeaderMonetarySummation'))
        _add_amount_element(summation, 'ram:LineTotalAmount', self.invoice.subtotal)
        _add_amount_element(summation, 'ram:TaxBasisTotalAmount', self.invoice.subtotal)
        _add_amount_element(summation, 'ram:TaxTotalAmount', self.invoice.tax_amount).set('currencyID', 'EUR')
        _add_amount_element(summation, 'ram:GrandTotalAmount', self.invoice.total)
        _add_amount_element(summation, 'ram:DuePayableAmount', self.invoice.total)
    
    def _calculate_vat_summary(self) -> dict:
        """Berechnet MwSt-Aufschlüsselung nach Steuersatz."""
        summary = {}
        for item in self.invoice.items.all():
            rate = _format_tax_rate(item.vat_rate)
            if rate not in summary:
                summary[rate] = {'net': Decimal('0'), 'tax': Decimal('0')}
            summary[rate]['net'] += item.line_total
            summary[rate]['tax'] += item.tax_amount
        return summary
    
    def _get_tax_category(self, rate: Decimal) -> str:
        """Gibt die MwSt-Kategorie zurück."""
        if rate == Decimal('0'):
            return 'Z'  # Zero rated
        elif rate == Decimal('7'):
            return 'S'  # Standard rate (reduced)
        else:
            return 'S'  # Standard rate


def generate_xrechnung(invoice: 'Invoice') -> str:
    """Generiert XRechnung XML für eine Rechnung."""
    generator = XRechnungGenerator(invoice)
    return generator.generate()