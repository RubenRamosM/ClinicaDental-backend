"""
Modelos base para reutilización en toda la aplicación.
Prepara el código para multi-tenancy futuro sin implementarlo ahora.
"""
from django.db import models


# =================================================================
# MULTITENANCY - MODELOS DE CLÍNICAS
# =================================================================
from .models_tenant import Clinica, Dominio  # noqa


# =================================================================
# MODELOS ABSTRACTOS BASE
# =================================================================


class ModeloConFechas(models.Model):
    """
    Modelo abstracto que agrega timestamps automáticos.
    Útil para auditoría y tracking de cambios.
    """
    fecha_creacion = models.DateTimeField(
        auto_now_add=True, 
        db_index=True,
        verbose_name="Fecha de creación"
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Última actualización"
    )

    class Meta:
        abstract = True
        ordering = ['-fecha_creacion']


class ModeloEliminacionLogica(models.Model):
    """
    Modelo abstracto para eliminación lógica (soft delete).
    Los registros no se eliminan físicamente, solo se marcan como inactivos.
    """
    activo = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name="Activo",
        help_text="Indica si el registro está activo o fue eliminado"
    )
    fecha_eliminacion = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha de eliminación"
    )

    class Meta:
        abstract = True


class ModeloPreparadoMultiClinica(ModeloConFechas):
    """
    Modelo abstracto preparado para multi-clínica FUTURO.
    
    Por ahora NO incluye el campo 'clinica', pero está diseñado
    para agregarlo fácilmente cuando se implemente multi-tenancy.
    
    ⚠️ CUANDO SE ACTIVE MULTI-CLÍNICA, solo agregar:
    clinica = models.ForeignKey('tenancy.Clinica', on_delete=models.CASCADE, null=True)
    
    Este modelo ya tiene los índices y estructura lista para ese campo.
    """
    
    class Meta:
        abstract = True
    
    # TODO (Multi-clínica): Descomentar cuando se cree la app 'tenancy'
    # clinica = models.ForeignKey(
    #     'tenancy.Clinica',
    #     on_delete=models.CASCADE,
    #     null=True,
    #     blank=True,
    #     db_index=True,
    #     related_name='%(class)s_set',
    #     verbose_name='Clínica',
    #     help_text='Clínica a la que pertenece este registro'
    # )


class ModeloAuditable(ModeloConFechas):
    """
    Modelo con campos de auditoría completos (quién creó/modificó).
    """
    creado_por = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_creado',
        verbose_name="Creado por"
    )
    modificado_por = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_modificado',
        verbose_name="Modificado por"
    )

    class Meta:
        abstract = True
