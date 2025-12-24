"""
Custom User Model with Multi-Tenancy Support
"""

from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager
from django.db import models


class Tenant(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)

    company_name = models.CharField(max_length=255)
    street = models.CharField(max_length=255, blank=True)
    zip_code = models.CharField(max_length=10, blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=2, default="DE")

    tax_id = models.CharField(max_length=50, blank=True)
    vat_id = models.CharField(max_length=50, blank=True)

    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)

    bank_name = models.CharField(max_length=255, blank=True)
    iban = models.CharField(max_length=34, blank=True)
    bic = models.CharField(max_length=11, blank=True)

    logo = models.ImageField(upload_to="logos/", blank=True, null=True)

    is_active = models.BooleanField(default=True)
    subscription_plan = models.CharField(
        max_length=20,
        choices=[
            ("cloud", "Cloud"),
            ("onpremise", "On-Premise"),
        ],
        default="cloud",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tenants"

    def __str__(self):
        return self.company_name


class CustomUserManager(BaseUserManager):
    def create_user(self, username, email=None, password=None, **extra_fields):
        if not username:
            raise ValueError("Username must be set")

        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "owner")
        return self.create_user(username, email, password, **extra_fields)


class User(AbstractUser):
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="users",
        null=True,
        blank=True,
    )

    phone = models.CharField(max_length=50, blank=True)

    role = models.CharField(
        max_length=20,
        choices=[
            ("owner", "Owner"),
            ("admin", "Admin"),
            ("user", "User"),
        ],
        default="user",
    )

    objects = CustomUserManager()

    class Meta:
        db_table = "users"

    def __str__(self):
        return self.email or self.username
