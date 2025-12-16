from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Tenant, User


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ("company_name", "slug", "email", "is_active", "subscription_plan")
    list_filter = ("is_active", "subscription_plan")
    search_fields = ("company_name", "email", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "email", "tenant", "role", "is_active")
    list_filter = ("is_active", "role", "tenant")
    search_fields = ("username", "email")

    fieldsets = BaseUserAdmin.fieldsets + (
        ("Tenant Info", {"fields": ("tenant", "role", "phone")}),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Tenant Info", {"fields": ("tenant", "role")}),
    )
