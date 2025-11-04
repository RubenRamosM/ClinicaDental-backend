"""
Middleware personalizado para detectar tenant desde header HTTP
Compatible con django-tenants para deployment en Render con frontend en Vercel
"""
from django_tenants.middleware.main import TenantMainMiddleware
from django.http import Http404
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
    
    def get_tenant(self, model, hostname, request):
        """
        Sobrescribe el método de TenantMainMiddleware para buscar por header
        en lugar de por hostname.
        """
        # Obtener el subdomain desde el header HTTP
        subdomain = request.headers.get('X-Tenant-Subdomain', '').strip().lower()
        
        # Si no hay header, usar tenant público
        if not subdomain:
            subdomain = 'public'
        
        # Buscar el tenant por schema_name
        try:
            tenant = model.objects.get(schema_name=subdomain)
            return tenant
        except model.DoesNotExist:
            # Si el tenant no existe, retornar error 404
            raise Http404(f"Tenant '{subdomain}' no encontrado")
    
    def process_request(self, request):
        """
        Procesa la petición y establece el tenant basado en el header
        """
        # Obtener el modelo de tenant (Clinica)
        connection = self.get_connection(request)
        hostname = self.hostname_from_request(request)
        
        # Usar nuestro método personalizado get_tenant
        tenant = self.get_tenant(Clinica, hostname, request)
        
        # Establecer el tenant en la conexión
        request.tenant = tenant
        connection.set_tenant(tenant)
        
        # Establecer el schema en la conexión
        self.setup_url_routing(request)
