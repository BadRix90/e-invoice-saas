from django.contrib import admin

from .models import Invoice, InvoiceItem


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1
    fields = ("position", "description", "quantity", "unit", "unit_price", "vat_rate", "line_total")
    readonly_fields = ("line_total",)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("invoice_number", "customer", "invoice_date", "total", "status", "format")
    list_filter = ("status", "format", "invoice_date")
    search_fields = ("invoice_number", "customer__company_name")
    date_hierarchy = "invoice_date"
    inlines = [InvoiceItemInline]
    readonly_fields = ("subtotal", "tax_amount", "total", "created_at", "updated_at")
