"""
URLs para historial clínico.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import reportes

router = DefaultRouter()
# IMPORTANTE: Registrar ViewSets con prefijos específicos para evitar conflictos
# El orden importa - los más específicos primero
router.register(r'documentos', views.DocumentoClinicoViewSet, basename='documento')
router.register(r'odontogramas', views.OdontogramaViewSet, basename='odontograma')
router.register(r'tratamientos-odonto', views.TratamientoOdontologicoViewSet, basename='tratamiento-odonto')
router.register(r'consentimientos', views.ConsentimientoInformadoViewSet, basename='consentimiento')
# El ViewSet principal de historial va al final con prefijo vacío (captura el resto)
router.register(r'', views.HistorialclinicoViewSet, basename='historial')

urlpatterns = [
    path('', include(router.urls)),
    
    # CU25: Reportes Clínicos
    path('reportes/estadisticas/', reportes.estadisticas_generales, name='reportes-estadisticas'),
    path('reportes/odontologos/productividad/', reportes.reporte_productividad_odontologos, name='reportes-productividad'),
    path('reportes/ingresos/mensuales/', reportes.reporte_ingresos_mensuales, name='reportes-ingresos'),
    path('reportes/pacientes/frecuentes/', reportes.reporte_pacientes_frecuentes, name='reportes-pacientes'),
]
