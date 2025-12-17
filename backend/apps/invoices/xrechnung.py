"""
XRechnung Generator - EN 16931 / CII Format
"""
import xml.etree.ElementTree as ET
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import Invoice

NAMESPACES = {
    'rsm': 'urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100',
    'ram': 'urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100',
    'qdt': 'urn:un:unece:uncefact:data:standard:QualifiedDataType:100',
    'udt': 'urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100',
}

for prefix, uri in NAMESPACES.items():
    ET.register_namespace(prefix, uri)


def _ns(tag: str) -> str:
    prefix, local = tag.split(':')
    return f'{{{NAMESPACES[prefix]}}}{local}'


def _text(parent: ET.Element, tag: str, text: str) -> ET.Element:
    elem = ET.SubElement(parent, _ns(tag))
    elem.text = str(text)
    return elem


def _id(parent: ET.Element, tag: str, value: str, scheme: str = None) -> ET.Element:
    elem = ET.SubElement(parent, _ns(tag))
    elem.text = str(value)
    if scheme:
        elem.set('schemeID', scheme)
    return elem


def _amount(parent: ET.Element, tag: str, amount: Decimal) -> ET.Element:
    """Betrag OHNE currencyID"""
    elem = ET.SubElement(parent, _ns(tag))
    elem.text = f'{amount:.2f}'
    return elem


def _date(parent: ET.Element, tag: str, dt: date) -> ET.Element:
    date_elem = ET.SubElement(parent, _ns(tag))
    ts = ET.SubElement(date_elem, _ns('udt:DateTimeString'))
    ts.text = dt.strftime('%Y%m%d')
    ts.set('format', '102')
    return date_elem


class XRechnungGenerator:
    def __init__(self, invoice: 'Invoice'):
        self.invoice = invoice
        self.tenant = invoice.tenant
        self.customer = invoice.customer

    def generate(self) -> str:
        root = ET.Element(_ns('rsm:CrossIndustryInvoice'))
        self._add_context(root)
        self._add_document(root)
        self._add_transaction(root)
        ET.indent(root, space="  ")
        return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding='unicode')

    def _add_context(self, root: ET.Element) -> None:
        ctx = ET.SubElement(root, _ns('rsm:ExchangedDocumentContext'))
        bp = ET.SubElement(ctx, _ns('ram:BusinessProcessSpecifiedDocumentContextParameter'))
        _id(bp, 'ram:ID', 'urn:fdc:peppol.eu:2017:poacc:billing:01:1.0')
        gl = ET.SubElement(ctx, _ns('ram:GuidelineSpecifiedDocumentContextParameter'))
        _id(gl, 'ram:ID', 'urn:cen.eu:en16931:2017#compliant#urn:xeinkauf.de:kosit:xrechnung_3.0')

    def _add_document(self, root: ET.Element) -> None:
        doc = ET.SubElement(root, _ns('rsm:ExchangedDocument'))
        _text(doc, 'ram:ID', self.invoice.invoice_number)
        _text(doc, 'ram:TypeCode', '380')
        _date(doc, 'ram:IssueDateTime', self.invoice.invoice_date)
        if self.invoice.notes:
            note = ET.SubElement(doc, _ns('ram:IncludedNote'))
            _text(note, 'ram:Content', self.invoice.notes)

    def _add_transaction(self, root: ET.Element) -> None:
        tx = ET.SubElement(root, _ns('rsm:SupplyChainTradeTransaction'))
        for item in self.invoice.items.all():
            self._add_line(tx, item)
        self._add_agreement(tx)
        self._add_delivery(tx)
        self._add_settlement(tx)

    def _add_line(self, tx: ET.Element, item) -> None:
        line = ET.SubElement(tx, _ns('ram:IncludedSupplyChainTradeLineItem'))
        
        doc = ET.SubElement(line, _ns('ram:AssociatedDocumentLineDocument'))
        _text(doc, 'ram:LineID', str(item.position))
        
        prod = ET.SubElement(line, _ns('ram:SpecifiedTradeProduct'))
        if item.sku:
            _id(prod, 'ram:SellerAssignedID', item.sku)
        _text(prod, 'ram:Name', item.description)
        
        agr = ET.SubElement(line, _ns('ram:SpecifiedLineTradeAgreement'))
        price = ET.SubElement(agr, _ns('ram:NetPriceProductTradePrice'))
        _amount(price, 'ram:ChargeAmount', item.unit_price)
        
        dlv = ET.SubElement(line, _ns('ram:SpecifiedLineTradeDelivery'))
        qty = ET.SubElement(dlv, _ns('ram:BilledQuantity'))
        qty.text = f'{item.quantity:.3f}'
        qty.set('unitCode', item.unit)
        
        stl = ET.SubElement(line, _ns('ram:SpecifiedLineTradeSettlement'))
        tax = ET.SubElement(stl, _ns('ram:ApplicableTradeTax'))
        _text(tax, 'ram:TypeCode', 'VAT')
        _text(tax, 'ram:CategoryCode', 'S' if item.vat_rate > 0 else 'Z')
        _text(tax, 'ram:RateApplicablePercent', f'{item.vat_rate:.2f}')
        
        summ = ET.SubElement(stl, _ns('ram:SpecifiedTradeSettlementLineMonetarySummation'))
        _amount(summ, 'ram:LineTotalAmount', item.line_total)

    def _add_agreement(self, tx: ET.Element) -> None:
        agr = ET.SubElement(tx, _ns('ram:ApplicableHeaderTradeAgreement'))
        
        if self.invoice.leitweg_id:
            _text(agr, 'ram:BuyerReference', self.invoice.leitweg_id)
        elif self.invoice.buyer_reference:
            _text(agr, 'ram:BuyerReference', self.invoice.buyer_reference)
        
        # Seller
        seller = ET.SubElement(agr, _ns('ram:SellerTradeParty'))
        _text(seller, 'ram:Name', self.tenant.name)
        
        # SELLER CONTACT (BG-6) - Pflicht!
        contact = ET.SubElement(seller, _ns('ram:DefinedTradeContact'))
        _text(contact, 'ram:PersonName', self.tenant.name)
        if self.tenant.phone:
            phone = ET.SubElement(contact, _ns('ram:TelephoneUniversalCommunication'))
            _text(phone, 'ram:CompleteNumber', self.tenant.phone)
        if self.tenant.email:
            email = ET.SubElement(contact, _ns('ram:EmailURIUniversalCommunication'))
            _id(email, 'ram:URIID', self.tenant.email)
        
        # Adresse
        addr = ET.SubElement(seller, _ns('ram:PostalTradeAddress'))
        if self.tenant.zip_code:
            _text(addr, 'ram:PostcodeCode', self.tenant.zip_code)
        if self.tenant.street:
            _text(addr, 'ram:LineOne', self.tenant.street)
        if self.tenant.city:
            _text(addr, 'ram:CityName', self.tenant.city)
        _text(addr, 'ram:CountryID', self.tenant.country or 'DE')
        
        # E-Mail als URI
        if self.tenant.email:
            uri = ET.SubElement(seller, _ns('ram:URIUniversalCommunication'))
            _id(uri, 'ram:URIID', self.tenant.email, 'EM')
        
        # USt-ID
        if self.tenant.vat_id:
            tax_reg = ET.SubElement(seller, _ns('ram:SpecifiedTaxRegistration'))
            _id(tax_reg, 'ram:ID', self.tenant.vat_id, 'VA')
        
        # Buyer
        buyer = ET.SubElement(agr, _ns('ram:BuyerTradeParty'))
        _text(buyer, 'ram:Name', self.customer.display_name)
        addr = ET.SubElement(buyer, _ns('ram:PostalTradeAddress'))
        _text(addr, 'ram:PostcodeCode', self.customer.zip_code)
        _text(addr, 'ram:LineOne', self.customer.street)
        _text(addr, 'ram:CityName', self.customer.city)
        _text(addr, 'ram:CountryID', self.customer.country)
        if self.customer.email:
            uri = ET.SubElement(buyer, _ns('ram:URIUniversalCommunication'))
            _id(uri, 'ram:URIID', self.customer.email, 'EM')
        if self.customer.vat_id:
            tax_reg = ET.SubElement(buyer, _ns('ram:SpecifiedTaxRegistration'))
            _id(tax_reg, 'ram:ID', self.customer.vat_id, 'VA')

    def _add_delivery(self, tx: ET.Element) -> None:
        dlv = ET.SubElement(tx, _ns('ram:ApplicableHeaderTradeDelivery'))
        evt = ET.SubElement(dlv, _ns('ram:ActualDeliverySupplyChainEvent'))
        _date(evt, 'ram:OccurrenceDateTime', self.invoice.invoice_date)

    def _add_settlement(self, tx: ET.Element) -> None:
        stl = ET.SubElement(tx, _ns('ram:ApplicableHeaderTradeSettlement'))
        _text(stl, 'ram:InvoiceCurrencyCode', 'EUR')
        
        # 0. Payment Instructions (BG-16) - PFLICHT für XRechnung!
        payment = ET.SubElement(stl, _ns('ram:SpecifiedTradeSettlementPaymentMeans'))
        _text(payment, 'ram:TypeCode', '58')  # 58 = SEPA Überweisung
        if self.tenant.iban:
            account = ET.SubElement(payment, _ns('ram:PayeePartyCreditorFinancialAccount'))
            _id(account, 'ram:IBANID', self.tenant.iban)
            if self.tenant.bic:
                institution = ET.SubElement(payment, _ns('ram:PayeeSpecifiedCreditorFinancialInstitution'))
                _id(institution, 'ram:BICID', self.tenant.bic)
        
        # 1. Tax breakdown
        vat = {}
        for item in self.invoice.items.all():
            rate = f'{item.vat_rate:.2f}'
            if rate not in vat:
                vat[rate] = {'net': Decimal('0'), 'tax': Decimal('0')}
            vat[rate]['net'] += item.line_total
            vat[rate]['tax'] += item.tax_amount
        
        for rate, data in vat.items():
            tax = ET.SubElement(stl, _ns('ram:ApplicableTradeTax'))
            _amount(tax, 'ram:CalculatedAmount', data['tax'])
            _text(tax, 'ram:TypeCode', 'VAT')
            _amount(tax, 'ram:BasisAmount', data['net'])
            _text(tax, 'ram:CategoryCode', 'S' if Decimal(rate) > 0 else 'Z')
            _text(tax, 'ram:RateApplicablePercent', rate)
        
        # 2. Payment terms
        if self.invoice.payment_terms:
            terms = ET.SubElement(stl, _ns('ram:SpecifiedTradePaymentTerms'))
            _text(terms, 'ram:Description', self.invoice.payment_terms)
            if self.invoice.due_date:
                _date(terms, 'ram:DueDateDateTime', self.invoice.due_date)
        
        # 3. Totals
        summ = ET.SubElement(stl, _ns('ram:SpecifiedTradeSettlementHeaderMonetarySummation'))
        _amount(summ, 'ram:LineTotalAmount', self.invoice.subtotal)
        _amount(summ, 'ram:TaxBasisTotalAmount', self.invoice.subtotal)
        
        tax_total = ET.SubElement(summ, _ns('ram:TaxTotalAmount'))
        tax_total.text = f'{self.invoice.tax_amount:.2f}'
        tax_total.set('currencyID', 'EUR')
        
        _amount(summ, 'ram:GrandTotalAmount', self.invoice.total)
        _amount(summ, 'ram:DuePayableAmount', self.invoice.total)


def generate_xrechnung(invoice: 'Invoice') -> str:
    return XRechnungGenerator(invoice).generate()