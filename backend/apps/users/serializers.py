from rest_framework import serializers
from .models import Tenant


class TenantSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()

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

    def get_logo(self, obj):
        if obj.logo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.logo.url)
            return obj.logo.url
        return None