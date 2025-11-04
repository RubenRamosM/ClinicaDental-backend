"""
URLs para gestión de clínicas (SOLO TENANT PÚBLICO)
Este módulo solo está disponible en localhost (tenant público)
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views_clinicas import ClinicaViewSet, DominioViewSet

router = DefaultRouter()
router.register(r'', ClinicaViewSet, basename='clinica')
router.register(r'dominios', DominioViewSet, basename='dominio')

urlpatterns = [
    path('', include(router.urls)),
]
