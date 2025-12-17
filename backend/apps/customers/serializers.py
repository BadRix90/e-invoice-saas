from rest_framework import serializers
from .models import Customer


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = [
            'id',
            'customer_number',
            'customer_type',
            'company_name',
            'contact_person',
            'email',
            'phone',
            'street',
            'zip_code',
            'city',
            'country',
            'leitweg_id',
            'tax_id',
            'vat_id',
            'payment_terms',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'customer_number', 'created_at', 'updated_at']

    def create(self, validated_data):
        # Auto-generate customer number
        tenant = self.context['request'].user.tenant
        last_customer = Customer.objects.filter(tenant=tenant).order_by('-id').first()
        if last_customer and last_customer.customer_number:
            last_num = int(last_customer.customer_number.split('-')[-1])
            new_num = f"K-{last_num + 1:04d}"
        else:
            new_num = "K-0001"
        validated_data['customer_number'] = new_num
        validated_data['tenant'] = tenant
        return super().create(validated_data)