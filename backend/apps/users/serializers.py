from rest_framework import serializers
from .models import Tenant


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = [
            'id', 'name', 'slug',
            'company_name', 'street', 'zip_code', 'city', 'country',
            'tax_id', 'vat_id',
            'email', 'phone',
            'bank_name', 'iban', 'bic',
            'logo',
        ]
        read_only_fields = ['id', 'slug']