"""
URLs para la app de usuarios.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'tipos-usuario', views.TipodeusuarioViewSet, basename='tipodeusuario')
router.register(r'usuarios', views.UsuarioViewSet, basename='usuario')
router.register(r'pacientes', views.PacienteViewSet, basename='paciente')

urlpatterns = [
    path('', include(router.urls)),
]
