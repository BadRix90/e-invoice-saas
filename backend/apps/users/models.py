"""
Custom User Model with Multi-Tenancy Support
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class Tenant(models.Model):
    """
    Tenant model for multi-tenancy (Cloud version).
    Each company/organization is a tenant.
    """

    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)

    # Company details
    company_name = models.CharField(max_length=255)
    street = models.CharField(max_length=255, blank=True)
    zip_code = models.CharField(max_length=10, blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=2, default="DE")  # ISO 3166-1 alpha-2

    # Tax information
    tax_id = models.CharField(max_length=50, blank=True)  # Steuernummer
    vat_id = models.CharField(max_length=50, blank=True)  # USt-IdNr.

    # Contact
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)

    # Bank details
    bank_name = models.CharField(max_length=255, blank=True)
    iban = models.CharField(max_length=34, blank=True)
    bic = models.CharField(max_length=11, blank=True)

    # Subscription
    is_active = models.BooleanField(default=True)
    subscription_plan = models.CharField(
        max_length=20,
        choices=[
            ("cloud", "Cloud"),
            ("onpremise", "On-Premise"),
        ],
        default="cloud",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tenants"
        verbose_name = "Tenant"
        verbose_name_plural = "Tenants"

    def __str__(self) -> str:
        return self.company_name


class User(AbstractUser):
    """
    Custom User Model extending Django's AbstractUser.
    """

    # Link to tenant
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="users",
        null=True,
        blank=True,
    )

    # Additional fields
    phone = models.CharField(max_length=50, blank=True)

    # Role within tenant
    role = models.CharField(
        max_length=20,
        choices=[
            ("owner", "Owner"),
            ("admin", "Admin"),
            ("user", "User"),
        ],
        default="user",
    )

    class Meta:
        db_table = "users"
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self) -> str:
        return self.email or self.username
