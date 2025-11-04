# Signals para el módulo de tratamientos
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Procedimiento, PlanTratamiento


@receiver(post_save, sender=Procedimiento)
def actualizar_estado_plan(sender, instance, created, **kwargs):
    """
    Actualiza automáticamente el estado del plan cuando todos
    los procedimientos están completados
    """
    if instance.estado == 'completado':
        plan = instance.plan_tratamiento
        
        # Si no hay procedimientos pendientes o en proceso, marcar plan como completado
        if not plan.procedimientos.exclude(estado='completado').exists():
            from django.utils import timezone
            plan.estado = 'completado'
            plan.fecha_finalizacion = timezone.now().date()
            plan.save()
