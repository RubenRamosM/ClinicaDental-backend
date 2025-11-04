from django.db import models


class Bitacora(models.Model):
    """Registro de auditoría de acciones en el sistema."""
    usuario = models.ForeignKey('usuarios.Usuario', on_delete=models.SET_NULL, null=True, blank=True)
    accion = models.CharField(max_length=255, help_text="Acción realizada")
    tabla_afectada = models.CharField(max_length=100, null=True, blank=True)
    registro_id = models.IntegerField(null=True, blank=True)
    detalles = models.TextField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'bitacora'
        verbose_name = 'Bitácora'
        verbose_name_plural = 'Bitácoras'
        ordering = ['-fecha']

    def __str__(self):
        usuario_str = self.usuario.nombre if self.usuario else "Sistema"
        return f"{usuario_str} - {self.accion} - {self.fecha}"
