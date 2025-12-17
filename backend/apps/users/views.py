from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Tenant
from .serializers import TenantSerializer


class TenantViewSet(viewsets.ModelViewSet):
    serializer_class = TenantSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Tenant.objects.filter(id=self.request.user.tenant_id)
    
    @action(detail=False, methods=['get', 'put', 'patch'])
    def current(self, request):
        """Aktuellen Tenant abrufen/bearbeiten"""
        tenant = request.user.tenant
        
        if request.method == 'GET':
            serializer = TenantSerializer(tenant)
            return Response(serializer.data)
        
        serializer = TenantSerializer(tenant, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)