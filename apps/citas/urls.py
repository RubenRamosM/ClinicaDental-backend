"""
URLs para la app de citas.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'horarios', views.HorarioViewSet, basename='horario')
router.register(r'estados-consulta', views.EstadodeconsultaViewSet, basename='estadodeconsulta')
router.register(r'tipos-consulta', views.TipodeconsultaViewSet, basename='tipodeconsulta')
router.register(r'consultas', views.ConsultaViewSet, basename='consulta')
# Registrar también en raíz para compatibilidad con frontend
router.register(r'', views.ConsultaViewSet, basename='cita')

urlpatterns = [
    path('', include(router.urls)),
    # Alias para compatibilidad con frontend (horarios-disponibles en vez de horarios/disponibles/)
    path('horarios-disponibles/', views.HorarioViewSet.as_view({'get': 'disponibles'}), name='horarios-disponibles'),
]
