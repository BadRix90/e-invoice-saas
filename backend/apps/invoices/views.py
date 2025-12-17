from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Invoice, InvoiceItem
from .serializers import InvoiceSerializer, InvoiceItemSerializer, InvoiceItemCreateSerializer


class InvoiceViewSet(viewsets.ModelViewSet):
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'invoice_format', 'customer']
    search_fields = ['invoice_number', 'customer__company_name']
    ordering_fields = ['invoice_number', 'invoice_date', 'created_at']
    ordering = ['-invoice_date']

    def get_queryset(self):
        return Invoice.objects.filter(tenant=self.request.user.tenant).prefetch_related('items')

    @action(detail=True, methods=['post'])
    def finalize(self, request, pk=None):
        """Rechnung finalisieren (Entwurf → Final)"""
        invoice = self.get_object()
        if invoice.status != 'draft':
            return Response(
                {'error': 'Nur Entwürfe können finalisiert werden.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not invoice.items.exists():
            return Response(
                {'error': 'Rechnung muss mindestens eine Position haben.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        invoice.status = 'final'
        invoice.save()
        return Response(InvoiceSerializer(invoice).data)

    @action(detail=True, methods=['post'])
    def mark_sent(self, request, pk=None):
        """Rechnung als versendet markieren"""
        invoice = self.get_object()
        if invoice.status not in ['final', 'sent']:
            return Response(
                {'error': 'Rechnung muss finalisiert sein.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        invoice.status = 'sent'
        invoice.save()
        return Response(InvoiceSerializer(invoice).data)

    @action(detail=True, methods=['post'])
    def mark_paid(self, request, pk=None):
        """Rechnung als bezahlt markieren"""
        invoice = self.get_object()
        if invoice.status not in ['sent', 'final']:
            return Response(
                {'error': 'Rechnung muss versendet oder finalisiert sein.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        invoice.status = 'paid'
        invoice.save()
        return Response(InvoiceSerializer(invoice).data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Rechnung stornieren"""
        invoice = self.get_object()
        if invoice.status == 'cancelled':
            return Response(
                {'error': 'Rechnung ist bereits storniert.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        invoice.status = 'cancelled'
        invoice.save()
        return Response(InvoiceSerializer(invoice).data)

    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """Rechnung duplizieren (als neuen Entwurf)"""
        original = self.get_object()
        
        # Neue Rechnung erstellen
        new_invoice = Invoice.objects.create(
            tenant=original.tenant,
            customer=original.customer,
            status='draft',
            invoice_format=original.invoice_format,
            payment_terms=original.payment_terms,
            notes=original.notes,
            created_by=request.user,
        )
        
        # Positionen kopieren
        for item in original.items.all():
            InvoiceItem.objects.create(
                invoice=new_invoice,
                product=item.product,
                description=item.description,
                quantity=item.quantity,
                unit=item.unit,
                unit_price=item.unit_price,
                vat_rate=item.vat_rate,
            )
        
        return Response(
            InvoiceSerializer(new_invoice).data,
            status=status.HTTP_201_CREATED
        )


class InvoiceItemViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['invoice']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return InvoiceItemCreateSerializer
        return InvoiceItemSerializer

    def get_queryset(self):
        return InvoiceItem.objects.filter(
            invoice__tenant=self.request.user.tenant
        )