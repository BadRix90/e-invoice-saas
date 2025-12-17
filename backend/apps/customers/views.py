from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Customer
from .serializers import CustomerSerializer


class CustomerViewSet(viewsets.ModelViewSet):
    serializer_class = CustomerSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['company_name', 'contact_person', 'email', 'customer_number']
    ordering_fields = ['company_name', 'customer_number', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        return Customer.objects.filter(tenant=self.request.user.tenant)