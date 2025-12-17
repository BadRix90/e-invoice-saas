from rest_framework import serializers
from .models import Customer


class CustomerSerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(read_only=True)

    class Meta:
        model = Customer
        fields = [
            'id',
            'customer_number',
            'is_business',
            'company_name',
            'first_name',
            'last_name',
            'display_name',
            'street',
            'zip_code',
            'city',
            'country',
            'email',
            'phone',
            'vat_id',
            'leitweg_id',
            'payment_terms_days',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'customer_number', 'display_name', 'created_at', 'updated_at']

    def create(self, validated_data):
        tenant = self.context['request'].user.tenant
        last_customer = Customer.objects.filter(tenant=tenant).order_by('-id').first()
        if last_customer and last_customer.customer_number:
            try:
                last_num = int(last_customer.customer_number.split('-')[-1])
                new_num = f"K-{last_num + 1:04d}"
            except ValueError:
                new_num = "K-0001"
        else:
            new_num = "K-0001"
        validated_data['customer_number'] = new_num
        validated_data['tenant'] = tenant
        return super().create(validated_data)