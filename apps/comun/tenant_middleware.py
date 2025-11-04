"""
Middleware personalizado para detectar tenant desde header HTTP
Compatible con django-tenants para deployment en Render con frontend en Vercel
"""
from django_tenants.middleware.main import BaseTenantMiddleware
from django.http import Http404
from apps.comun.models import Clinica


class TenantHeaderMiddleware(BaseTenantMiddleware):
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
    
    def get_tenant(self, request):
        """
        Sobrescribe el método de BaseTenantMiddleware para buscar por header.
        """
        # Obtener el subdomain desde el header HTTP
        subdomain = request.headers.get('X-Tenant-Subdomain', '').strip().lower()
        
        # Si no hay header, usar tenant público
        if not subdomain:
            subdomain = 'public'
        
        # Buscar el tenant por schema_name usando el modelo Clinica
        try:
            tenant = Clinica.objects.get(schema_name=subdomain)
            return tenant
        except Clinica.DoesNotExist:
            # Si el tenant no existe, retornar error 404
            raise Http404(f"Tenant '{subdomain}' no encontrado")
