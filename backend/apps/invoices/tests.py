import pytest
from decimal import Decimal
from django.utils import timezone
from apps.users.models import User, Tenant
from apps.customers.models import Customer
from apps.invoices.models import Invoice, InvoiceItem


@pytest.fixture
def tenant(db):
    return Tenant.objects.create(
        name="Test GmbH",
        slug="test-gmbh",
    )


@pytest.fixture
def user(db, tenant):
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
        tenant=tenant,
    )


@pytest.fixture
def customer(db, tenant):
    return Customer.objects.create(
        tenant=tenant,
        customer_number="K-001",
        company_name="Kunde GmbH",
        email="kunde@example.com",
        street="Teststraße 1",
        zip_code="12345",
        city="Berlin",
        country="DE",
    )


@pytest.fixture
def invoice(db, tenant, customer, user):
    return Invoice.objects.create(
        tenant=tenant,
        invoice_number="RE-2025-0001",
        customer=customer,
        invoice_date=timezone.now().date(),
        due_date=timezone.now().date(),
        status="draft",
        format="xrechnung",
        created_by=user,
    )


class TestInvoiceModel:
    def test_create_invoice(self, invoice):
        assert invoice.id is not None
        assert invoice.status == "draft"

    def test_invoice_number(self, invoice):
        assert invoice.invoice_number == "RE-2025-0001"

    def test_calculate_totals(self, invoice):
        InvoiceItem.objects.create(
            invoice=invoice,
            description="Test Position",
            quantity=Decimal("2"),
            unit_price=Decimal("100.00"),
            vat_rate=Decimal("19.00"),
        )
        invoice.calculate_totals()
        
        assert invoice.subtotal == Decimal("200.00")
        assert invoice.tax_amount == Decimal("38.00")
        assert invoice.total == Decimal("238.00")


class TestInvoiceArchive:
    def test_archive_draft_fails(self, invoice):
        from apps.invoices.archive import archive_invoice
        
        with pytest.raises(ValueError, match="Entwürfe"):
            archive_invoice(invoice)

    def test_archive_finalized_invoice(self, invoice):
        from apps.invoices.archive import archive_invoice, verify_archive
        
        invoice.status = "final"
        invoice.save()
        
        result = archive_invoice(invoice)
        
        assert result["hash"] is not None
        assert invoice.archived_at is not None
        
        verify_result = verify_archive(invoice)
        assert verify_result["valid"] is True

    def test_archive_twice_fails(self, invoice):
        from apps.invoices.archive import archive_invoice
        
        invoice.status = "final"
        invoice.save()
        
        archive_invoice(invoice)
        
        with pytest.raises(ValueError, match="bereits archiviert"):
            archive_invoice(invoice)
            
class TestInvoiceAPI:
    def test_list_invoices(self, api_client, invoice):
        response = api_client.get("/api/invoices/")
        assert response.status_code == 200
        assert response.data["count"] == 1

    def test_get_invoice(self, api_client, invoice):
        response = api_client.get(f"/api/invoices/{invoice.id}/")
        assert response.status_code == 200
        assert response.data["invoice_number"] == "RE-2025-0001"

    def test_finalize_invoice(self, api_client, invoice_with_items):
        response = api_client.post(f"/api/invoices/{invoice_with_items.id}/finalize/")
        assert response.status_code == 200
        assert response.data["status"] == "final"

    def test_finalize_empty_invoice_fails(self, api_client, invoice):
        response = api_client.post(f"/api/invoices/{invoice.id}/finalize/")
        assert response.status_code == 400

    def test_mark_paid(self, api_client, finalized_invoice):
        response = api_client.post(f"/api/invoices/{finalized_invoice.id}/mark_paid/")
        assert response.status_code == 200
        assert response.data["status"] == "paid"

    def test_dashboard_stats(self, api_client, invoice):
        response = api_client.get("/api/invoices/dashboard_stats/")
        assert response.status_code == 200
        assert "total_invoices" in response.data

    def test_archive_invoice(self, api_client, finalized_invoice):
        response = api_client.post(f"/api/invoices/{finalized_invoice.id}/archive/")
        assert response.status_code == 200
        assert response.data["success"] is True

    def test_verify_archive(self, api_client, finalized_invoice):
        # Erst archivieren
        api_client.post(f"/api/invoices/{finalized_invoice.id}/archive/")
        # Dann verifizieren
        response = api_client.get(f"/api/invoices/{finalized_invoice.id}/verify/")
        assert response.status_code == 200
        assert response.data["success"] is True
        
class TestXRechnungGenerator:
    def test_generate_xrechnung(self, finalized_invoice):
        from apps.invoices.xrechnung import generate_xrechnung
        
        xml_content = generate_xrechnung(finalized_invoice)
        
        # Prüfe ob XML generiert wurde
        assert xml_content is not None
        assert len(xml_content) > 0
        
        # Prüfe ob es gültiges XML ist
        assert '<?xml version' in xml_content
        assert 'Invoice' in xml_content

    def test_xrechnung_contains_invoice_number(self, finalized_invoice):
        from apps.invoices.xrechnung import generate_xrechnung
        
        xml_content = generate_xrechnung(finalized_invoice)
        
        assert finalized_invoice.invoice_number in xml_content

    def test_xrechnung_contains_customer(self, finalized_invoice):
        from apps.invoices.xrechnung import generate_xrechnung
        
        xml_content = generate_xrechnung(finalized_invoice)
        
        assert finalized_invoice.customer.company_name in xml_content

    def test_xrechnung_contains_total(self, finalized_invoice):
        from apps.invoices.xrechnung import generate_xrechnung
        
        xml_content = generate_xrechnung(finalized_invoice)
        
        # Total sollte im XML sein
        assert str(finalized_invoice.total).replace('.', ',') in xml_content or str(finalized_invoice.total) in xml_content


class TestZUGFeRDGenerator:
    def test_generate_zugferd_pdf(self, finalized_invoice):
        from apps.invoices.zugferd import generate_zugferd_pdf
        
        pdf_content = generate_zugferd_pdf(finalized_invoice)
        
        # Prüfe ob PDF generiert wurde
        assert pdf_content is not None
        assert len(pdf_content) > 0
        
        # Prüfe PDF Header (Magic Bytes)
        assert pdf_content[:4] == b'%PDF'

    def test_zugferd_pdf_size(self, finalized_invoice):
        from apps.invoices.zugferd import generate_zugferd_pdf
        
        pdf_content = generate_zugferd_pdf(finalized_invoice)
        
        # PDF sollte mindestens 1KB sein
        assert len(pdf_content) > 1000


class TestDATEVExport:
    def test_generate_datev_export(self, finalized_invoice):
        from apps.invoices.datev import generate_datev_simple
        
        csv_content = generate_datev_simple([finalized_invoice])
        
        # Prüfe ob CSV generiert wurde
        assert csv_content is not None
        assert len(csv_content) > 0

    def test_datev_contains_invoice_data(self, finalized_invoice):
        from apps.invoices.datev import generate_datev_simple
        
        csv_content = generate_datev_simple([finalized_invoice])
        
        # Rechnungsnummer sollte enthalten sein
        assert finalized_invoice.invoice_number in csv_content