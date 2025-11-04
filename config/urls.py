"""
URL configuration for dental_clinic_backend project.

Sistema de enrutamiento dinámico para Multi-Tenancy:
"""
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.http import JsonResponse
from .url_patterns import urlpatterns_public, urlpatterns_tenant


def test_headers(request):
    """Endpoint de prueba para verificar headers recibidos"""
    headers = {k: v for k, v in request.headers.items()}
    tenant_header = request.headers.get('X-Tenant-Subdomain', 'NO ENCONTRADO')
    
    return JsonResponse({
        'status': 'ok',
        'tenant_header': tenant_header,
        'all_headers': headers,
        'hostname': request.get_host(),
        'path': request.path,
        'method': request.method,
    }, json_dumps_params={'indent': 2})

# Django no soporta lambda en path, así que usamos el middleware para cambiar ROOT_URLCONF
# Por defecto, cargamos las URLs públicas
urlpatterns = [
    path('api/v1/test-headers/', test_headers, name='test-headers'),  # Endpoint de prueba
] + urlpatterns_public

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
