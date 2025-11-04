"""
Middleware para auditoría automática.
"""
import json
from .utils import registrar_accion


class AuditoriaMiddleware:
    """
    Middleware que registra automáticamente todas las peticiones POST, PUT, PATCH, DELETE
    en la bitácora de auditoría.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Procesar request
        response = self.get_response(request)
        
        # Solo auditar métodos que modifican datos
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            # Solo auditar rutas de API
            if request.path.startswith('/api/v1/'):
                self._registrar_peticion(request, response)
        
        return response
    
    def _registrar_peticion(self, request, response):
        """Registra la petición en auditoría."""
        try:
            # Solo registrar si fue exitoso (2xx o 3xx)
            if 200 <= response.status_code < 400:
                # Determinar acción basada en método y ruta
                accion = self._generar_descripcion_accion(request, response)
                
                # Extraer tabla afectada de la ruta
                tabla_afectada = self._extraer_tabla_de_ruta(request.path)
                
                # Intentar extraer ID del registro de la respuesta
                registro_id = self._extraer_registro_id(response)
                
                # Registrar en auditoría
                registrar_accion(
                    request,
                    accion=accion,
                    tabla_afectada=tabla_afectada,
                    registro_id=registro_id,
                    detalles=f"{request.method} {request.path}"
                )
        except Exception as e:
            # No queremos que falle la petición si falla la auditoría
            print(f"Error en middleware de auditoría: {str(e)}")
    
    def _generar_descripcion_accion(self, request, response):
        """Genera descripción de la acción basada en método HTTP."""
        metodo_map = {
            'POST': 'Creó',
            'PUT': 'Actualizó',
            'PATCH': 'Modificó',
            'DELETE': 'Eliminó'
        }
        
        verbo = metodo_map.get(request.method, 'Ejecutó')
        recurso = self._extraer_recurso_de_ruta(request.path)
        
        return f"{verbo} {recurso}"
    
    def _extraer_tabla_de_ruta(self, path):
        """Extrae el nombre de la tabla de la ruta."""
        partes = path.strip('/').split('/')
        if len(partes) >= 3:
            # /api/v1/usuarios/ -> usuarios
            return partes[2]
        return 'desconocido'
    
    def _extraer_recurso_de_ruta(self, path):
        """Extrae el nombre del recurso de la ruta."""
        partes = path.strip('/').split('/')
        if len(partes) >= 3:
            recurso = partes[2].replace('-', ' ').title()
            return recurso
        return 'recurso'
    
    def _extraer_registro_id(self, response):
        """Intenta extraer el ID del registro de la respuesta."""
        try:
            if hasattr(response, 'data') and isinstance(response.data, dict):
                return response.data.get('id')
        except:
            pass
        return None
