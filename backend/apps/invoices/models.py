"""
Invoice Models - Rechnungsverwaltung
"""

from decimal import Decimal

from django.db import models

from apps.customers.models import Customer
from apps.products.models import Product
from apps.users.models import Tenant, User


class Invoice(models.Model):
    """
    Invoice model - core entity for e-invoicing.
    """

    STATUS_CHOICES = [
        ("draft", "Entwurf"),
        ("final", "Finalisiert"),
        ("sent", "Versendet"),
        ("paid", "Bezahlt"),
        ("cancelled", "Storniert"),
    ]

    FORMAT_CHOICES = [
        ("xrechnung", "XRechnung (XML)"),
        ("zugferd", "ZUGFeRD (PDF)"),
    ]

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="invoices",
    )

    # Invoice identification
    invoice_number = models.CharField(max_length=50)
    invoice_date = models.DateField()
    due_date = models.DateField()

    # Customer reference
    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name="invoices",
    )

    # Format & Status
    format = models.CharField(max_length=20, choices=FORMAT_CHOICES, default="zugferd")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")

    # XRechnung specific
    leitweg_id = models.CharField(max_length=50, blank=True)
    buyer_reference = models.CharField(max_length=100, blank=True)  # Bestellnummer

    # Amounts (calculated from line items)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    # Notes
    notes = models.TextField(blank=True)
    payment_terms = models.TextField(blank=True)

    # Generated files
    xml_file = models.FileField(upload_to="invoices/xml/", blank=True)
    pdf_file = models.FileField(upload_to="invoices/pdf/", blank=True)

    # Archive (GoBD)
    archived_at = models.DateTimeField(null=True, blank=True)
    archive_hash = models.CharField(max_length=64, blank=True)  # SHA-256

    # Audit trail
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_invoices",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "invoices"
        verbose_name = "Invoice"
        verbose_name_plural = "Invoices"
        unique_together = ("tenant", "invoice_number")
        ordering = ["-invoice_date", "-invoice_number"]

    def __str__(self) -> str:
        return f"{self.invoice_number} - {self.customer}"

    def calculate_totals(self) -> None:
        """Calculate invoice totals from line items."""
        self.subtotal = sum(item.line_total for item in self.items.all())
        self.tax_amount = sum(item.tax_amount for item in self.items.all())
        self.total = self.subtotal + self.tax_amount


class InvoiceItem(models.Model):
    """
    Invoice line item.
    """

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="items",
    )

    # Optional product reference
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    # Line item details (copied from product or entered manually)
    position = models.PositiveIntegerField(default=1)
    sku = models.CharField(max_length=50, blank=True)
    description = models.CharField(max_length=500)
    quantity = models.DecimalField(max_digits=10, decimal_places=3, default=Decimal("1.000"))
    unit = models.CharField(max_length=3, default="H87")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("19.00"))

    # Calculated fields
    line_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    class Meta:
        db_table = "invoice_items"
        verbose_name = "Invoice Item"
        verbose_name_plural = "Invoice Items"
        ordering = ["position"]

    def __str__(self) -> str:
        return f"{self.position}. {self.description}"

    def save(self, *args, **kwargs) -> None:
        """Calculate line total and tax before saving."""
        self.line_total = self.quantity * self.unit_price
        self.tax_amount = self.line_total * (self.vat_rate / Decimal("100"))
        super().save(*args, **kwargs)
