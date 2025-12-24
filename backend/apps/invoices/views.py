from django.http import HttpResponse
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Invoice, InvoiceItem, Reminder
from .serializers import InvoiceSerializer, InvoiceItemSerializer, InvoiceItemCreateSerializer, ReminderSerializer
from .xrechnung import generate_xrechnung
from .validator import validate_xrechnung, check_validator_health
from .zugferd import generate_zugferd_pdf
from .email import send_invoice_email
from datetime import date
from .datev import generate_datev_simple
from .archive import archive_invoice, verify_archive, download_archive


class InvoiceViewSet(viewsets.ModelViewSet):
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'format', 'customer']
    search_fields = ['invoice_number', 'customer__company_name']
    ordering_fields = ['invoice_number', 'invoice_date', 'created_at']
    ordering = ['-invoice_date']

    def get_queryset(self):
        return Invoice.objects.filter(tenant=self.request.user.tenant).prefetch_related('items')

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.user.tenant,
                        created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def finalize(self, request, pk=None):
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

        invoice.calculate_totals()
        invoice.status = 'final'
        invoice.save()
        try:
            archive_result = archive_invoice(invoice)
        except Exception as e:
            pass
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
    def send_email(self, request, pk=None):
        """Rechnung per E-Mail versenden"""
        invoice = self.get_object()

        if invoice.status == 'draft':
            return Response(
                {'error': 'Entwürfe können nicht versendet werden.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Optional: andere E-Mail-Adresse
        recipient = request.data.get('email', invoice.customer.email)

        if not recipient:
            return Response(
                {'error': 'Keine E-Mail-Adresse vorhanden.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            send_invoice_email(invoice, recipient)

            # Status auf "versendet" setzen
            if invoice.status == 'final':
                invoice.status = 'sent'
                invoice.save()

            return Response({
                'success': True,
                'message': f'Rechnung an {recipient} versendet.',
                'invoice': InvoiceSerializer(invoice).data
            })
        except Exception as e:
            return Response(
                {'error': f'Fehler beim Versenden: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get', 'post'])
    def reminders(self, request, pk=None):
        """Mahnungen abrufen oder neue Mahnung senden"""
        from .email import send_reminder_email

        invoice = self.get_object()

        if request.method == 'GET':
            reminders = invoice.reminders.all()
            return Response(ReminderSerializer(reminders, many=True).data)

        # POST: Neue Mahnung senden
        if invoice.status not in ['sent', 'final']:
            return Response(
                {'error': 'Nur versendete/finalisierte Rechnungen können gemahnt werden.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if invoice.status == 'paid':
            return Response(
                {'error': 'Rechnung ist bereits bezahlt.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Nächste Mahnstufe ermitteln
        last_reminder = invoice.reminders.order_by('-level').first()
        next_level = (last_reminder.level + 1) if last_reminder else 1

        if next_level > 3:
            return Response(
                {'error': 'Maximale Mahnstufe (3) erreicht.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        recipient = request.data.get('email', invoice.customer.email)
        fee = request.data.get('fee', 0)

        if not recipient:
            return Response(
                {'error': 'Keine E-Mail-Adresse vorhanden.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            send_reminder_email(invoice, next_level, recipient, fee)

            reminder = Reminder.objects.create(
                invoice=invoice,
                level=next_level,
                sent_to=recipient,
                fee=fee,
            )

            return Response({
                'success': True,
                'message': f'Mahnung Stufe {next_level} an {recipient} versendet.',
                'reminder': ReminderSerializer(reminder).data
            })
        except Exception as e:
            return Response(
                {'error': f'Fehler beim Versenden: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

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
        from django.utils import timezone

        original = self.get_object()
        today = timezone.now().date()

        # Neue Rechnung erstellen
        new_invoice = Invoice.objects.create(
            tenant=original.tenant,
            customer=original.customer,
            invoice_date=today,
            due_date=today +
            timezone.timedelta(days=original.customer.payment_terms_days),
            status='draft',
            format=original.format,
            leitweg_id=original.leitweg_id,
            payment_terms=original.payment_terms,
            notes=original.notes,
            created_by=request.user,
        )

        # Positionen kopieren
        for item in original.items.all():
            InvoiceItem.objects.create(
                invoice=new_invoice,
                product=item.product,
                position=item.position,
                sku=item.sku,
                description=item.description,
                quantity=item.quantity,
                unit=item.unit,
                unit_price=item.unit_price,
                vat_rate=item.vat_rate,
            )

        # Summen berechnen
        new_invoice.calculate_totals()
        new_invoice.save()

        return Response(
            InvoiceSerializer(new_invoice).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['get'])
    def download_xml(self, request, pk=None):
        """XRechnung XML herunterladen"""
        from django.core.files.base import ContentFile

        invoice = self.get_object()

        if invoice.status == 'draft':
            return Response(
                {'error': 'Entwürfe können nicht exportiert werden. Bitte zuerst finalisieren.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if invoice.total == 0:
            invoice.calculate_totals()
            invoice.save()

        xml_content = generate_xrechnung(invoice)

        # XML in Datenbank speichern
        if not invoice.xml_file:
            invoice.xml_file.save(
                f"{invoice.invoice_number}.xml",
                ContentFile(xml_content.encode('utf-8')),
                save=True
            )

        response = HttpResponse(
            xml_content, content_type='application/xml; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="{invoice.invoice_number}.xml"'
        return response

    @action(detail=True, methods=['get'])
    def download_pdf(self, request, pk=None):
        """ZUGFeRD PDF herunterladen"""
        from django.core.files.base import ContentFile

        invoice = self.get_object()

        if invoice.status == 'draft':
            return Response(
                {'error': 'Bitte Rechnung erst finalisieren.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        invoice.calculate_totals()
        pdf_content = generate_zugferd_pdf(invoice)

        # PDF in Datenbank speichern
        if not invoice.pdf_file:
            invoice.pdf_file.save(
                f"{invoice.invoice_number}.pdf",
                ContentFile(pdf_content),
                save=True
            )

        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{invoice.invoice_number}.pdf"'
        return response

    @action(detail=True, methods=['get'])
    def validate(self, request, pk=None):
        """XRechnung validieren"""
        invoice = self.get_object()

        if invoice.status == 'draft':
            return Response(
                {'error': 'Entwürfe können nicht validiert werden.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        xml_content = generate_xrechnung(invoice)
        result = validate_xrechnung(xml_content)

        return Response({
            'is_valid': result.is_valid,
            'errors': result.errors,
            'warnings': result.warnings,
        })

    @action(detail=False, methods=['get'])
    def validator_status(self, request):
        """Prüft ob der Validator erreichbar ist"""
        return Response({'validator_available': check_validator_health()})

    @action(detail=False, methods=['get'])
    def export_datev(self, request):
        """DATEV CSV Export aller finalisierten Rechnungen"""
        invoices = self.get_queryset().exclude(status='draft')

        # Optional: Datumsfilter
        date_from = request.query_params.get('from')
        date_to = request.query_params.get('to')

        if date_from:
            invoices = invoices.filter(invoice_date__gte=date_from)
        if date_to:
            invoices = invoices.filter(invoice_date__lte=date_to)

        csv_content = generate_datev_simple(list(invoices))

        response = HttpResponse(
            csv_content, content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="datev_export_{date.today()}.csv"'
        return response

    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        """Dashboard Statistiken"""
        from django.db.models import Sum, Count
        from django.db.models.functions import TruncMonth
        from decimal import Decimal

        invoices = self.get_queryset()

        # Basis-Statistiken
        total_invoices = invoices.count()
        draft_count = invoices.filter(status='draft').count()
        open_count = invoices.filter(status__in=['final', 'sent']).count()
        paid_count = invoices.filter(status='paid').count()
        cancelled_count = invoices.filter(status='cancelled').count()

        # Beträge
        total_revenue = invoices.filter(status='paid').aggregate(
            total=Sum('total'))['total'] or Decimal('0.00')
        open_amount = invoices.filter(status__in=['final', 'sent']).aggregate(
            total=Sum('total'))['total'] or Decimal('0.00')

        # Überfällige Rechnungen
        from django.utils import timezone
        today = timezone.now().date()
        overdue = invoices.filter(
            status__in=['final', 'sent'],
            due_date__lt=today
        )
        overdue_count = overdue.count()
        overdue_amount = overdue.aggregate(total=Sum('total'))[
            'total'] or Decimal('0.00')

        # Umsatz pro Monat (letzte 12 Monate)
        monthly_revenue = invoices.filter(
            status='paid'
        ).annotate(
            month=TruncMonth('invoice_date')
        ).values('month').annotate(
            total=Sum('total'),
            count=Count('id')
        ).order_by('month')

        return Response({
            'total_invoices': total_invoices,
            'by_status': {
                'draft': draft_count,
                'open': open_count,
                'paid': paid_count,
                'cancelled': cancelled_count,
            },
            'total_revenue': str(total_revenue),
            'open_amount': str(open_amount),
            'overdue': {
                'count': overdue_count,
                'amount': str(overdue_amount),
            },
            'monthly_revenue': [
                {
                    'month': item['month'].strftime('%Y-%m') if item['month'] else None,
                    'total': str(item['total']),
                    'count': item['count']
                }
                for item in monthly_revenue
            ],
        })

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):

        invoice = self.get_object()

        try:
            result = archive_invoice(invoice)
            return Response({
                'success': True,
                'message': f'Rechnung {invoice.invoice_number} wurde archiviert.',
                'archive': result,
            })
        except ValueError as e:
            return Response({
                'success': False,
                'error': str(e),
            }, status=400)
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Archivierung fehlgeschlagen: {str(e)}',
            }, status=500)

    @action(detail=True, methods=['get'])
    def verify(self, request, pk=None):
        invoice = self.get_object()
        result = verify_archive(invoice)

        if result['valid']:
            return Response({
                'success': True,
                'message': 'Archiv ist intakt.',
                'details': result,
            })
        else:
            return Response({
                'success': False,
                'message': 'Archiv-Prüfung fehlgeschlagen!',
                'details': result,
            }, status=400)

    @action(detail=True, methods=['get'])
    def download_archive(self, request, pk=None):
        invoice = self.get_object()

        if not invoice.archived_at:
            return Response({
                'success': False,
                'error': 'Rechnung ist nicht archiviert.',
            }, status=400)

        zip_data = download_archive(invoice)

        if zip_data is None:
            return Response({
                'success': False,
                'error': 'Archiv konnte nicht geladen werden.',
            }, status=500)

        response = HttpResponse(zip_data, content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="archiv_{invoice.invoice_number}.zip"'
        return response

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """Rechnung manuell archivieren"""
        invoice = self.get_object()

        try:
            result = archive_invoice(invoice)
            return Response({
                'success': True,
                'message': 'Rechnung erfolgreich archiviert.',
                'archive': result
            })
        except ValueError as e:
            return Response({'error': str(e)}, status=400)

    @action(detail=True, methods=['get'])
    def verify_archive_endpoint(self, request, pk=None):
        """Archiv-Integrität prüfen"""
        invoice = self.get_object()
        result = verify_archive(invoice)

        if not result['valid']:
            return Response({
                'success': False,
                'error': result.get('error'),
                'details': result,
            }, status=400)

        return Response({
            'success': True,
            'message': 'Archiv ist gültig.',
            'details': result
        })


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

    def perform_create(self, serializer):
        item = serializer.save()
        item.invoice.calculate_totals()
        item.invoice.save()

    def perform_update(self, serializer):
        item = serializer.save()
        item.invoice.calculate_totals()
        item.invoice.save()

    def perform_destroy(self, instance):
        invoice = instance.invoice
        instance.delete()
        invoice.calculate_totals()
        invoice.save()
