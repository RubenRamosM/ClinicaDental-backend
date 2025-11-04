"""
Middleware para cambiar dinámicamente las URLs según el tenant
"""
from django.utils.deprecation import MiddlewareMixin
from django.db import connection


class TenantURLRoutingMiddleware(MiddlewareMixin):
    """
    Middleware que cambia ROOT_URLCONF según el tenant detectado
    
    - Si es tenant público (public) → usa url_patterns.urlpatterns_public
    - Si es un tenant de clínica → usa url_patterns.urlpatterns_tenant
    
    IMPORTANTE: Debe ejecutarse DESPUÉS de TenantMainMiddleware
    """
    
    def process_request(self, request):
        # TenantMainMiddleware ya estableció connection.tenant
        # Ahora solo cambiamos las URLs según el schema
        
        if connection.schema_name == 'public':
            # Tenant público: solo admin de sistema y gestión de clínicas
            request.urlconf = 'config.url_patterns_public'
        else:
            # Tenant de clínica: APIs normales
            request.urlconf = 'config.url_patterns_tenant'
        
        return None
