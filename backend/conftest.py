import pytest
from decimal import Decimal
from django.utils import timezone
from rest_framework.test import APIClient

from apps.users.models import User, Tenant
from apps.customers.models import Customer
from apps.products.models import Product
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
def api_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def customer(db, tenant):
    return Customer.objects.create(
        tenant=tenant,
        customer_number="K-001",
        company_name="Kunde GmbH",
        email="kunde@example.com",
        street="Kundenstr. 1",
        zip_code="12345",
        city="Berlin",
        country="DE",
    )


@pytest.fixture
def product(db, tenant):
    return Product.objects.create(
        tenant=tenant,
        sku="ART-001",
        name="Test Produkt",
        unit_price=Decimal("100.00"),
        vat_rate=Decimal("19.00"),
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


@pytest.fixture
def invoice_with_items(invoice, product):
    InvoiceItem.objects.create(
        invoice=invoice,
        product=product,
        description="Position 1",
        quantity=Decimal("2"),
        unit_price=Decimal("100.00"),
        vat_rate=Decimal("19.00"),
    )
    invoice.calculate_totals()
    invoice.save()
    return invoice


@pytest.fixture
def finalized_invoice(invoice_with_items):
    invoice_with_items.status = "final"
    invoice_with_items.save()
    return invoice_with_items