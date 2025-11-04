"""
Tareas asíncronas para el módulo de autenticación.
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta


@shared_task(name='apps.autenticacion.tasks.limpiar_tokens_expirados')
def limpiar_tokens_expirados():
    """
    Elimina tokens de autenticación expirados de la base de datos.
    
    Se ejecuta diariamente a las 3:00 AM para mantener la BD limpia.
    """
    from rest_framework.authtoken.models import Token
    from django.contrib.auth import get_user_model
    
    ahora = timezone.now()
    hace_30_dias = ahora - timedelta(days=30)
    
    # Estrategia: Eliminar tokens de usuarios inactivos hace más de 30 días
    # Los tokens de DRF no tienen fecha de expiración por defecto,
    # así que usamos last_login del usuario
    
    User = get_user_model()
    
    tokens_eliminados = 0
    
    try:
        # Obtener usuarios inactivos hace más de 30 días
        usuarios_inactivos = User.objects.filter(
            last_login__lt=hace_30_dias
        ).values_list('id', flat=True)
        
        # Eliminar sus tokens
        tokens_a_eliminar = Token.objects.filter(
            user_id__in=usuarios_inactivos
        )
        
        tokens_eliminados = tokens_a_eliminar.count()
        tokens_a_eliminar.delete()
        
        print(f"✅ Tokens expirados eliminados: {tokens_eliminados}")
        
    except Exception as e:
        print(f"❌ Error al limpiar tokens: {str(e)}")
    
    return {
        'fecha_ejecucion': ahora.isoformat(),
        'tokens_eliminados': tokens_eliminados
    }


@shared_task(name='apps.autenticacion.tasks.limpiar_sesiones_expiradas')
def limpiar_sesiones_expiradas():
    """
    Elimina sesiones expiradas de Django.
    
    Opcional: Se puede ejecutar semanalmente.
    """
    from django.core.management import call_command
    
    try:
        call_command('clearsessions')
        print("✅ Sesiones expiradas limpiadas")
        return {'status': 'success', 'fecha': timezone.now().isoformat()}
    except Exception as e:
        print(f"❌ Error al limpiar sesiones: {str(e)}")
        return {'status': 'error', 'mensaje': str(e)}
