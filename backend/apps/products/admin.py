from django.contrib import admin

from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("sku", "name", "unit_price", "vat_rate", "is_active")
    list_filter = ("is_active", "vat_rate", "unit")
    search_fields = ("sku", "name")
