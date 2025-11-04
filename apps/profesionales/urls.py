"""
URLs para la app de profesionales.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from . import views
from .models import Odontologo

router = DefaultRouter()
# ViewSet específico para /api/v1/profesionales/odontologos/
router.register(r'odontologos', views.OdontologoViewSet, basename='odontologo')

# Vista personalizada para especialidades
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def especialidades_list(request):
    """Listar especialidades únicas de odontólogos."""
    especialidades = Odontologo.objects.values_list('especialidad', flat=True).distinct()
    especialidades_list = [{'nombre': esp} for esp in especialidades if esp]
    return Response(especialidades_list)

urlpatterns = [
    path('especialidades/', especialidades_list, name='especialidades'),
    path('', include(router.urls)),
]
