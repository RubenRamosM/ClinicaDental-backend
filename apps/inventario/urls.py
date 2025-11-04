"""
URLs para gestión de inventario.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'categorias', views.CategoriaInsumoViewSet, basename='categoria')
router.register(r'proveedores', views.ProveedorViewSet, basename='proveedor')
router.register(r'insumos', views.InsumoViewSet, basename='insumo')
router.register(r'movimientos', views.MovimientoInventarioViewSet, basename='movimiento')
router.register(r'alertas', views.AlertaInventarioViewSet, basename='alerta')

urlpatterns = [
    path('', include(router.urls)),
    path('reporte/', views.reporte_general, name='reporte-inventario'),
]
