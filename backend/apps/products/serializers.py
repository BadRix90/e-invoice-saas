from rest_framework import serializers
from decimal import Decimal, ROUND_HALF_UP
from .models import Product


class ProductSerializer(serializers.ModelSerializer):
    gross_price = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id',
            'sku',
            'name',
            'description',
            'unit',
            'unit_price',
            'gross_price',
            'vat_rate',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'sku', 'gross_price', 'created_at', 'updated_at']

    def get_gross_price(self, obj) -> Decimal:
        """Bruttopreis = Netto + MwSt (kaufmännisch gerundet)"""
        vat_multiplier = Decimal('1') + (obj.vat_rate / Decimal('100'))
        gross = obj.unit_price * vat_multiplier
        return gross.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def create(self, validated_data):
        tenant = self.context['request'].user.tenant
        # Auto-generate SKU
        last_product = Product.objects.filter(tenant=tenant).order_by('-id').first()
        if last_product and last_product.sku:
            try:
                last_num = int(last_product.sku.split('-')[-1])
                new_sku = f"ART-{last_num + 1:04d}"
            except ValueError:
                new_sku = "ART-0001"
        else:
            new_sku = "ART-0001"
        validated_data['sku'] = new_sku
        validated_data['tenant'] = tenant
        return super().create(validated_data)