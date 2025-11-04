"""
URLs para TENANTS DE CLÍNICAS (clinica1.localhost, clinica2.localhost, etc.)
Todas las operaciones de la clínica
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin de Django (para administradores de la clínica)
    path('admin/', admin.site.urls),
    
    # APIs REST de la clínica
    # Autenticación
    path('api/v1/auth/', include('apps.autenticacion.urls')),
    
    # Usuarios y Pacientes
    path('api/v1/usuarios/', include('apps.usuarios.urls')),
    path('api/v1/pacientes/', include('apps.usuarios.urls')),  # Alias
    
    # Citas y Consultas
    path('api/v1/citas/', include('apps.citas.urls')),
    
    # Servicios y Combos
    path('api/v1/servicios/', include('apps.administracion_clinica.urls')),
    
    # Pagos y Facturas
    path('api/v1/pagos/', include('apps.sistema_pagos.urls')),
    
    # Historial Clínico y Documentos
    path('api/v1/historial-clinico/', include('apps.historial_clinico.urls')),
    path('api/v1/historia-clinica/', include('apps.historial_clinico.urls')),  # Backwards compatibility
    
    # Planes de Tratamiento y Presupuestos
    path('api/v1/tratamientos/', include('apps.tratamientos.urls')),
    path('api/v1/presupuestos-digitales/', include('apps.tratamientos.urls_presupuestos')),
    
    # Profesionales (Odontólogos, Especialidades)
    path('api/v1/profesionales/', include('apps.profesionales.urls')),
    
    # Auditoría (Bitácora de la clínica)
    path('api/v1/auditoria/', include('apps.auditoria.urls')),
    
    # Respaldos automáticos en la nube (de la clínica)
    path('api/v1/', include('respaldos.urls')),
    
    # Chatbot de citas
    path('api/v1/', include('apps.chatbot.urls')),
    
    # Dashboard Administrativo de la clínica
    path('api/v1/dashboard/', include('apps.admin_dashboard.urls')),
    path('api/v1/admin/dashboard/', include('apps.admin_dashboard.urls')),  # Backwards compatibility
    
    # Reportes de la clínica
    path('api/v1/reportes/', include('apps.admin_dashboard.urls')),
    
    # Administración (Servicios, Configuración de la clínica)
    path('api/v1/administracion/', include('apps.administracion_clinica.urls')),
    
    # Gestión de Inventario de la clínica
    path('api/v1/inventario/', include('apps.inventario.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
