from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PresupuestoViewSet

# Router dedicado para presupuestos digitales (alias sin prefijo adicional)
router = DefaultRouter()
router.register(r'', PresupuestoViewSet, basename='presupuesto-digital')

urlpatterns = [
    path('', include(router.urls)),
]
