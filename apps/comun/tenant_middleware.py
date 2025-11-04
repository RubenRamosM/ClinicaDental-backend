"""
Middleware personalizado para detectar tenant desde header HTTP
Compatible con django-tenants para deployment en Render con frontend en Vercel
"""
from django_tenants.middleware.main import TenantMainMiddleware
from django.http import Http404
from django.db import connection
from apps.comun.models import Clinica


class TenantHeaderMiddleware(TenantMainMiddleware):
    """
    Middleware que detecta el tenant desde el header X-Tenant-Subdomain
    en lugar de usar el hostname.
    
    Flujo:
    1. Lee el header X-Tenant-Subdomain de la petición
    2. Busca la clínica con ese schema_name
    3. Establece connection.tenant para esa clínica
    4. Django usa automáticamente el schema correcto
    
    Caso especial: Si no hay header, usa 'public' (tenant por defecto)
    """
    
    def process_request(self, request):
        """
        Procesa la petición y establece el tenant basado en el header X-Tenant-Subdomain
        """
        # Establecer schema público primero (donde están los metadatos de tenants)
        connection.set_schema_to_public()
        
        # Obtener el subdomain desde el header HTTP
        subdomain = request.headers.get('X-Tenant-Subdomain', '').strip().lower()
        
        # Si no hay header, usar tenant público
        if not subdomain:
            subdomain = 'public'
        
        # Buscar el tenant por schema_name
        try:
            tenant = Clinica.objects.get(schema_name=subdomain)
        except Clinica.DoesNotExist:
            raise Http404(f"Tenant '{subdomain}' no encontrado")
        
        # Establecer el tenant en la conexión
        tenant.domain_url = request.get_host()
        request.tenant = tenant
        connection.set_tenant(tenant)
        
        # Configurar el URL routing si es necesario
        self.setup_url_routing(request)
