from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TenantViewSet, RegisterView, check_company_code

router = DefaultRouter()
router.register(r'tenants', TenantViewSet, basename='tenant')

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('check-code/', check_company_code, name='check-code'),
    path('', include(router.urls)),
]