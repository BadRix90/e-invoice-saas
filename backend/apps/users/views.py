from rest_framework import viewsets, permissions, generics, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from .models import Tenant
from .serializers import TenantSerializer, RegisterSerializer


class RegisterView(generics.CreateAPIView):
    """Registrierung neuer User mit Firmen-Code"""
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        return Response({
            'user': {
                'username': user.username,
                'email': user.email,
                'tenant': user.tenant.name,
                'is_admin': user.is_staff
            },
            'message': 'Registrierung erfolgreich! Bitte melden Sie sich an.'
        }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def check_company_code(request):
    """Prüft ob Firmen-Code bereits existiert"""
    code = request.query_params.get('code')
    if not code:
        return Response({'error': 'Code parameter erforderlich'}, status=400)
    
    exists = Tenant.objects.filter(slug=code).exists()
    return Response({'exists': exists})


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
            serializer = TenantSerializer(tenant, context={'request': request})
            return Response(serializer.data)

        serializer = TenantSerializer(
            tenant, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=False, methods=['post', 'delete'], url_path='logo')
    def logo(self, request):
        """Logo hochladen oder löschen"""
        tenant = request.user.tenant

        if request.method == 'DELETE':
            if tenant.logo:
                tenant.logo.delete()
                tenant.save()
            return Response({'status': 'Logo gelöscht'})

        if 'logo' not in request.FILES:
            return Response({'error': 'Keine Datei'}, status=400)

        # Altes Logo löschen
        if tenant.logo:
            tenant.logo.delete()

        tenant.logo = request.FILES['logo']
        tenant.save()

        serializer = TenantSerializer(tenant, context={'request': request})
        return Response(serializer.data)