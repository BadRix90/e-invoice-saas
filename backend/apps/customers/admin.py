from django.contrib import admin

from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("customer_number", "display_name", "city", "email", "leitweg_id")
    list_filter = ("is_business", "country")
    search_fields = ("customer_number", "company_name", "last_name", "email")
