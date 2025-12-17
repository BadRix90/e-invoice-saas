from rest_framework import serializers
from decimal import Decimal, ROUND_HALF_UP
from .models import Invoice, InvoiceItem
from apps.customers.serializers import CustomerSerializer
from apps.products.serializers import ProductSerializer


class InvoiceItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    line_total_net = serializers.SerializerMethodField()
    line_total_gross = serializers.SerializerMethodField()
    line_vat_amount = serializers.SerializerMethodField()

    class Meta:
        model = InvoiceItem
        fields = [
            'id',
            'product',
            'product_name',
            'description',
            'quantity',
            'unit',
            'unit_price',
            'vat_rate',
            'line_total_net',
            'line_vat_amount',
            'line_total_gross',
        ]
        read_only_fields = ['id']

    def get_line_total_net(self, obj) -> Decimal:
        """Netto-Zeilensumme = Menge × Einzelpreis"""
        total = obj.quantity * obj.unit_price
        return total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def get_line_vat_amount(self, obj) -> Decimal:
        """MwSt-Betrag der Zeile"""
        net = obj.quantity * obj.unit_price
        vat = net * (obj.vat_rate / Decimal('100'))
        return vat.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def get_line_total_gross(self, obj) -> Decimal:
        """Brutto-Zeilensumme = Netto + MwSt"""
        net = obj.quantity * obj.unit_price
        vat = net * (obj.vat_rate / Decimal('100'))
        gross = net + vat
        return gross.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


class InvoiceSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source='customer.company_name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    # Berechnete Felder
    total_net = serializers.SerializerMethodField()
    total_vat = serializers.SerializerMethodField()
    total_gross = serializers.SerializerMethodField()
    vat_summary = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = [
            'id',
            'invoice_number',
            'customer',
            'customer_name',
            'status',
            'invoice_format',
            'invoice_date',
            'delivery_date',
            'due_date',
            'payment_terms',
            'notes',
            'items',
            'total_net',
            'total_vat',
            'total_gross',
            'vat_summary',
            'created_by',
            'created_by_name',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id', 'invoice_number', 'created_by', 'created_at', 'updated_at'
        ]

    def get_total_net(self, obj) -> Decimal:
        """Summe aller Netto-Positionen"""
        total = Decimal('0.00')
        for item in obj.items.all():
            line_net = item.quantity * item.unit_price
            total += line_net.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return total

    def get_total_vat(self, obj) -> Decimal:
        """Summe aller MwSt-Beträge"""
        total = Decimal('0.00')
        for item in obj.items.all():
            line_net = item.quantity * item.unit_price
            line_vat = line_net * (item.vat_rate / Decimal('100'))
            total += line_vat.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return total

    def get_total_gross(self, obj) -> Decimal:
        """Bruttosumme = Netto + MwSt"""
        return self.get_total_net(obj) + self.get_total_vat(obj)

    def get_vat_summary(self, obj) -> list:
        """MwSt-Aufschlüsselung nach Steuersatz (für Rechnung)"""
        vat_dict = {}
        for item in obj.items.all():
            rate = item.vat_rate
            line_net = (item.quantity * item.unit_price).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
            line_vat = (line_net * rate / Decimal('100')).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
            
            if rate not in vat_dict:
                vat_dict[rate] = {'net': Decimal('0.00'), 'vat': Decimal('0.00')}
            vat_dict[rate]['net'] += line_net
            vat_dict[rate]['vat'] += line_vat

        return [
            {'rate': rate, 'net': data['net'], 'vat': data['vat']}
            for rate, data in sorted(vat_dict.items(), reverse=True)
        ]

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
            'description',
            'quantity',
            'unit',
            'unit_price',
            'vat_rate',
        ]
        read_only_fields = ['id']

    def create(self, validated_data):
        # Wenn Produkt angegeben, Standardwerte übernehmen
        product = validated_data.get('product')
        if product:
            if not validated_data.get('description'):
                validated_data['description'] = product.name
            if not validated_data.get('unit'):
                validated_data['unit'] = product.unit
            if not validated_data.get('unit_price'):
                validated_data['unit_price'] = product.unit_price
            if not validated_data.get('vat_rate'):
                validated_data['vat_rate'] = product.vat_rate
        return super().create(validated_data)