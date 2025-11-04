from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PlanTratamientoViewSet, 
    PresupuestoViewSet, 
    ProcedimientoViewSet,
    HistorialPagoViewSet,
    SesionTratamientoViewSet
)

router = DefaultRouter()
router.register(r'planes-tratamiento', PlanTratamientoViewSet, basename='plan-tratamiento')
router.register(r'presupuestos', PresupuestoViewSet, basename='presupuesto')
router.register(r'procedimientos', ProcedimientoViewSet, basename='procedimiento')
router.register(r'pagos', HistorialPagoViewSet, basename='pago')
router.register(r'sesiones-tratamiento', SesionTratamientoViewSet, basename='sesion-tratamiento')

urlpatterns = [
    path('', include(router.urls)),
]
