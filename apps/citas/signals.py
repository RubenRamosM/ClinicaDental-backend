"""
Signals para el módulo de citas.
CU18: No-Show Automation
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Consulta


@receiver(post_save, sender=Consulta)
def bloquear_paciente_por_noshows(sender, instance, created, **kwargs):
    """
    Signal que bloquea automáticamente a un paciente cuando acumula
    3 o más faltas (no-show).
    
    CU18: Automatización de No-Show
    """
    # Solo ejecutar si la consulta fue marcada como no_show
    if instance.estado == 'no_show':
        paciente = instance.codpaciente
        usuario = paciente.codusuario
        
        # Contar total de no-shows del paciente
        total_noshows = Consulta.objects.filter(
            codpaciente=paciente,
            estado='no_show'
        ).count()
        
        # Si tiene 3 o más faltas, bloquear
        if total_noshows >= 3:
            from apps.autenticacion.models import BloqueoUsuario
            
            # Verificar si ya está bloqueado
            bloqueo_existente = BloqueoUsuario.objects.filter(
                usuario=usuario,
                activo=True
            ).first()
            
            if not bloqueo_existente:
                # Crear bloqueo automático
                BloqueoUsuario.objects.create(
                    usuario=usuario,
                    motivo=f'Bloqueo automático por {total_noshows} faltas consecutivas (no-show)',
                    fecha_bloqueo=timezone.now(),
                    bloqueado_por=None,  # Bloqueado automáticamente por el sistema
                    activo=True
                )
                
                # TODO: Opcional - Enviar notificación al paciente
                # Ejemplo: enviar_email_bloqueo(usuario.email, total_noshows)
