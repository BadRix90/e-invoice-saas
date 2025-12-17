from rest_framework.routers import DefaultRouter
from .views import InvoiceViewSet, InvoiceItemViewSet

router = DefaultRouter()
router.register('items', InvoiceItemViewSet, basename='invoice-item')
router.register('', InvoiceViewSet, basename='invoice')

urlpatterns = router.urls