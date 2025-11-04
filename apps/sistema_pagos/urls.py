"""
URLs para sistema de pagos.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'tipos-pago', views.TipopagoViewSet, basename='tipo-pago')
router.register(r'estados-factura', views.EstadodefacturaViewSet, basename='estado-factura')
router.register(r'facturas', views.FacturaViewSet, basename='factura')
router.register(r'pagos-online', views.PagoEnLineaViewSet, basename='pago-online')
# Registrar sin prefijo para que las acciones estén en /api/v1/pagos/pendientes/ etc
# IMPORTANTE: Debe ir al final para que no capture las rutas anteriores
router.register(r'', views.PagoViewSet, basename='pago')

urlpatterns = [
    # Router URLs
    path('', include(router.urls)),
    
    # Stripe Payment URLs - Consultas
    path('stripe/crear-intencion-consulta/', views.crear_intencion_pago_consulta, name='stripe-crear-intencion-consulta'),
    path('stripe/confirmar-pago/', views.confirmar_pago_consulta, name='stripe-confirmar-pago'),
    path('stripe/clave-publica/', views.obtener_clave_publica_stripe, name='stripe-clave-publica'),
    
    # Stripe Payment URLs - Presupuestos/Tratamientos
    path('stripe/crear-intencion-presupuesto/', views.crear_intencion_pago_presupuesto, name='stripe-crear-intencion-presupuesto'),
    path('stripe/confirmar-pago-presupuesto/', views.confirmar_pago_presupuesto, name='stripe-confirmar-pago-presupuesto'),
]
