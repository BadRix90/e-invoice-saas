"""
Customer Models - Kundenverwaltung
"""

from django.db import models

from apps.users.models import Tenant


class Customer(models.Model):
    """
    Customer model for storing customer/recipient data.
    """

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="customers",
    )

    # Customer identification
    customer_number = models.CharField(max_length=50)

    # Company or person
    is_business = models.BooleanField(default=True)
    company_name = models.CharField(max_length=255, blank=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)

    # Address
    street = models.CharField(max_length=255)
    zip_code = models.CharField(max_length=10)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=2, default="DE")

    # Contact
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)

    # Tax information
    vat_id = models.CharField(max_length=50, blank=True)  # USt-IdNr.

    # XRechnung specific
    leitweg_id = models.CharField(max_length=50, blank=True)  # Leitweg-ID for B2G

    # Payment
    payment_terms_days = models.PositiveIntegerField(default=30)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "customers"
        verbose_name = "Customer"
        verbose_name_plural = "Customers"
        unique_together = ("tenant", "customer_number")
        ordering = ["company_name", "last_name"]

    def __str__(self) -> str:
        if self.company_name:
            return self.company_name
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def display_name(self) -> str:
        """Returns the display name for the customer."""
        return str(self)
