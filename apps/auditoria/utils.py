"""
Utilidades para registro de auditoría.
"""


def registrar_accion(request, accion, tabla_afectada=None, registro_id=None, detalles=None):
    """
    Registra una acción en la bitácora de auditoría.
    
    Args:
        request: HttpRequest object
        accion: Descripción de la acción realizada
        tabla_afectada: Nombre de la tabla afectada (opcional)
        registro_id: ID del registro afectado (opcional)
        detalles: Detalles adicionales (opcional)
    """
    try:
        from .models import Bitacora
        from apps.usuarios.models import Usuario
        
        # Obtener usuario desde el request
        usuario = None
        if request.user.is_authenticated:
            try:
                usuario = Usuario.objects.get(correoelectronico=request.user.email)
            except Usuario.DoesNotExist:
                pass
        
        # Obtener IP del cliente
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')
        
        # Obtener User Agent
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]  # Limitar a 500 caracteres
        
        # Crear registro en bitácora
        Bitacora.objects.create(
            usuario=usuario,
            accion=accion,
            tabla_afectada=tabla_afectada,
            registro_id=registro_id,
            detalles=detalles,
            ip_address=ip_address,
            user_agent=user_agent
        )
    except Exception as e:
        # No queremos que falle la operación principal si falla el registro de auditoría
        print(f"Error al registrar auditoría: {str(e)}")


def registrar_login(request, usuario_email, exitoso=True):
    """Registra un intento de login."""
    accion = f"Login exitoso: {usuario_email}" if exitoso else f"Login fallido: {usuario_email}"
    registrar_accion(request, accion, tabla_afectada='auth', detalles=accion)


def registrar_logout(request, usuario_email):
    """Registra un logout."""
    registrar_accion(request, f"Logout: {usuario_email}", tabla_afectada='auth')


def registrar_creacion(request, modelo, instancia):
    """Registra la creación de un registro."""
    tabla = modelo._meta.db_table
    registro_id = instancia.pk
    accion = f"Creó {modelo._meta.verbose_name}: {str(instancia)}"
    registrar_accion(request, accion, tabla_afectada=tabla, registro_id=registro_id)


def registrar_actualizacion(request, modelo, instancia):
    """Registra la actualización de un registro."""
    tabla = modelo._meta.db_table
    registro_id = instancia.pk
    accion = f"Actualizó {modelo._meta.verbose_name}: {str(instancia)}"
    registrar_accion(request, accion, tabla_afectada=tabla, registro_id=registro_id)


def registrar_eliminacion(request, modelo, instancia):
    """Registra la eliminación de un registro."""
    tabla = modelo._meta.db_table
    registro_id = instancia.pk
    accion = f"Eliminó {modelo._meta.verbose_name}: {str(instancia)}"
    detalles = f"ID: {registro_id}, Datos: {str(instancia)}"
    registrar_accion(request, accion, tabla_afectada=tabla, registro_id=registro_id, detalles=detalles)
