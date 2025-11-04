"""
URLs para administración clínica.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'servicios', views.ServicioViewSet, basename='servicio')
router.register(r'combos', views.ComboServicioViewSet, basename='combo')

urlpatterns = [
    path('', include(router.urls)),
    # Endpoints adicionales
    path('consultorios/', views.consultorios_list, name='consultorios-list'),
    path('configuracion/', views.configuracion_general, name='configuracion-general'),
    path('piezas-dentales/', views.piezas_dentales_list, name='piezas-dentales-list'),
]
