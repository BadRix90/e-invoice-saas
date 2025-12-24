from rest_framework import viewsets, permissions, generics, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from .models import Tenant
from .serializers import TenantSerializer, RegisterSerializer


class RegisterView(generics.CreateAPIView):

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
                'role': user.role,
                'is_admin': user.role in ['owner', 'admin']
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
    
    @action(detail=False, methods=['get'])
    def team(self, request):
        """Alle Team-Mitglieder des Tenants abrufen"""
        from .serializers import UserSerializer
        
        users = request.user.tenant.users.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], url_path='team/add')
    def add_team_member(self, request):
        """Neuen Mitarbeiter hinzufügen (nur Owner)"""
        from django.contrib.auth import get_user_model
        
        # Nur Owner darf Mitarbeiter hinzufügen
        if request.user.role != 'owner':
            return Response(
                {'error': 'Nur der Owner darf Mitarbeiter hinzufügen.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        User = get_user_model()
        email = request.data.get('email')
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not all([email, username, password]):
            return Response(
                {'error': 'E-Mail, Username und Passwort erforderlich.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # User erstellen
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            tenant=request.user.tenant,
            role='user'
        )
        
        from .serializers import UserSerializer
        return Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED
        )
