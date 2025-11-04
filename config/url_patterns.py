from django.contrib import admin
from django.urls import path, include

# URLs principales del sistema
urlpatterns_public = [
    # Admin de Django
    path('admin/', admin.site.urls),
    
    # APIs REST
    # Autenticación
    path('api/v1/auth/', include('apps.autenticacion.urls')),
    
    # Usuarios y Pacientes
    path('api/v1/usuarios/', include('apps.usuarios.urls')),
    
    # Citas y Consultas
    path('api/v1/citas/', include('apps.citas.urls')),
    
    # Servicios y Combos
    path('api/v1/servicios/', include('apps.administracion_clinica.urls')),
    
    # Pagos y Facturas
    path('api/v1/pagos/', include('apps.sistema_pagos.urls')),
    
    # Historial Clínico y Documentos
    path('api/v1/historial-clinico/', include('apps.historial_clinico.urls')),  # Corregido: historial-clinico
    path('api/v1/historia-clinica/', include('apps.historial_clinico.urls')),  # Backwards compatibility
    
    # Planes de Tratamiento y Presupuestos
    path('api/v1/tratamientos/', include('apps.tratamientos.urls')),
    
    # Presupuestos Digitales (alias directo - compatibilidad frontend)
    path('api/v1/presupuestos-digitales/', include('apps.tratamientos.urls_presupuestos')),
    
    # Profesionales (Odontólogos, Especialidades)
    path('api/v1/profesionales/', include('apps.profesionales.urls')),
    
    # Pacientes (alias de usuarios filtrado)
    path('api/v1/pacientes/', include('apps.usuarios.urls')),  # Usa mismo ViewSet
    
    # Auditoría (Bitácora)
    path('api/v1/auditoria/', include('apps.auditoria.urls')),
    
    # Respaldos automáticos en la nube
    path('api/v1/', include('respaldos.urls')),
    
    # Chatbot de citas
    path('api/v1/', include('apps.chatbot.urls')),
    
    # Dashboard Administrativo (CU26)
    path('api/v1/dashboard/', include('apps.admin_dashboard.urls')),  # Corregido: /dashboard/ directo
    path('api/v1/admin/dashboard/', include('apps.admin_dashboard.urls')),  # Backwards compatibility
    
    # Reportes
    path('api/v1/reportes/', include('apps.admin_dashboard.urls')),  # Usa mismo módulo
    
    # Administración (Servicios, Configuración)
    path('api/v1/administracion/', include('apps.administracion_clinica.urls')),
    
    # Gestión de Inventario (CU27)
    path('api/v1/inventario/', include('apps.inventario.urls')),
]

# TODO (Multi-clínica): Eliminar urlpatterns_tenant después de migración completa
urlpatterns_tenant = urlpatterns_public