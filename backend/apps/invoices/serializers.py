from rest_framework import serializers
from decimal import Decimal, ROUND_HALF_UP
from .models import Invoice, InvoiceItem, Reminder


class InvoiceItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True, allow_null=True)

    class Meta:
        model = InvoiceItem
        fields = [
            'id',
            'product',
            'product_name',
            'position',
            'sku',
            'description',
            'quantity',
            'unit',
            'unit_price',
            'vat_rate',
            'line_total',
            'tax_amount',
        ]
        read_only_fields = ['id', 'line_total', 'tax_amount']


class InvoiceSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source='customer.display_name', read_only=True)
    created_by_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    format_display = serializers.CharField(source='get_format_display', read_only=True)

    class Meta:
        model = Invoice
        fields = [
            'id',
            'invoice_number',
            'customer',
            'customer_name',
            'status',
            'status_display',
            'format',
            'format_display',
            'invoice_date',
            'due_date',
            'leitweg_id',
            'buyer_reference',
            'subtotal',
            'tax_amount',
            'total',
            'notes',
            'payment_terms',
            'items',
            'created_by',
            'created_by_name',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id', 'invoice_number', 'subtotal', 'tax_amount', 'total',
            'created_by', 'created_at', 'updated_at'
        ]

    def get_created_by_name(self, obj) -> str:
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return ''

    def create(self, validated_data):
        tenant = self.context['request'].user.tenant
        user = self.context['request'].user

        # Auto-generate invoice number: RE-YYYY-NNNN
        from django.utils import timezone
        year = timezone.now().year
        last_invoice = Invoice.objects.filter(
            tenant=tenant,
            invoice_number__startswith=f'RE-{year}'
        ).order_by('-invoice_number').first()

        if last_invoice:
            try:
                last_num = int(last_invoice.invoice_number.split('-')[-1])
                new_num = f"RE-{year}-{last_num + 1:04d}"
            except ValueError:
                new_num = f"RE-{year}-0001"
        else:
            new_num = f"RE-{year}-0001"

        validated_data['invoice_number'] = new_num
        validated_data['tenant'] = tenant
        validated_data['created_by'] = user
        return super().create(validated_data)


class InvoiceItemCreateSerializer(serializers.ModelSerializer):
    """Separater Serializer zum Anlegen von Positionen"""

    class Meta:
        model = InvoiceItem
        fields = [
            'id',
            'invoice',
            'product',
            'position',
            'sku',
            'description',
            'quantity',
            'unit',
            'unit_price',
            'vat_rate',
        ]
        read_only_fields = ['id']

        def create(self, validated_data):
            tenant = self.context['request'].user.tenant
            user = self.context['request'].user

            # Auto-generate invoice number: RE-YYYY-NNNN
            from django.utils import timezone
            year = timezone.now().year
            last_invoice = Invoice.objects.filter(
                tenant=tenant,
                invoice_number__startswith=f'RE-{year}'
            ).order_by('-invoice_number').first()

            if last_invoice:
                try:
                    last_num = int(last_invoice.invoice_number.split('-')[-1])
                    new_num = f"RE-{year}-{last_num + 1:04d}"
                except ValueError:
                    new_num = f"RE-{year}-0001"
            else:
                new_num = f"RE-{year}-0001"

            validated_data['invoice_number'] = new_num
            validated_data['tenant'] = tenant
            validated_data['created_by'] = user
            
            invoice = super().create(validated_data)
            return invoice
        
class ReminderSerializer(serializers.ModelSerializer):
    invoice_number = serializers.CharField(source='invoice.invoice_number', read_only=True)
    level_display = serializers.CharField(source='get_level_display', read_only=True)

    class Meta:
        model = Reminder
        fields = [
            'id',
            'invoice',
            'invoice_number',
            'level',
            'level_display',
            'sent_at',
            'sent_to',
            'fee',
            'notes',
        ]
        read_only_fields = ['id', 'sent_at']