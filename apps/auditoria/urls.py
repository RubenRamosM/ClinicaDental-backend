"""
URLs para auditoría.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
# Registrar sin prefijo para que las acciones estén directamente en /api/v1/auditoria/
router.register(r'', views.BitacoraViewSet, basename='auditoria')

urlpatterns = [
    path('', include(router.urls)),
]
