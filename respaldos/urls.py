"""
Configuración de URLs para la app de respaldos.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RespaldoViewSet

router = DefaultRouter()
router.register(r'respaldos', RespaldoViewSet, basename='respaldo')

urlpatterns = [
    path('', include(router.urls)),
]
