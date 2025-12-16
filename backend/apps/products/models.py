"""
Product Models - Artikelverwaltung
"""

from decimal import Decimal

from django.db import models

from apps.users.models import Tenant


class Product(models.Model):
    """
    Product/Service model for invoice line items.
    """

    VAT_RATE_CHOICES = [
        (Decimal("19.00"), "19% (Standard)"),
        (Decimal("7.00"), "7% (Ermäßigt)"),
        (Decimal("0.00"), "0% (Steuerfrei)"),
    ]

    UNIT_CHOICES = [
        ("H87", "Stück"),  # Piece
        ("HUR", "Stunde"),  # Hour
        ("DAY", "Tag"),  # Day
        ("MON", "Monat"),  # Month
        ("KGM", "Kilogramm"),  # Kilogram
        ("MTR", "Meter"),  # Meter
        ("LTR", "Liter"),  # Liter
        ("C62", "Einheit"),  # Unit (generic)
    ]

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="products",
    )

    # Product identification
    sku = models.CharField(max_length=50)  # Article number
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    # Pricing
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=3, choices=UNIT_CHOICES, default="H87")
    vat_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        choices=VAT_RATE_CHOICES,
        default=Decimal("19.00"),
    )

    # Status
    is_active = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "products"
        verbose_name = "Product"
        verbose_name_plural = "Products"
        unique_together = ("tenant", "sku")
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.sku} - {self.name}"
