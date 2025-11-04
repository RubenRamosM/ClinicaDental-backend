"""
URLs para TENANT PÚBLICO (localhost)
Solo gestión de clínicas y administración del sistema
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin de Django (solo para super administradores del sistema)
    path('admin/', admin.site.urls),
    
    # API de gestión de clínicas (SOLO EN PÚBLICO)
    path('api/v1/clinicas/', include('apps.comun.urls')),
    
    # Autenticación (necesaria en ambos)
    path('api/v1/auth/', include('apps.autenticacion.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
