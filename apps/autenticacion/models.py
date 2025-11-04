from django.db import models


class BloqueoUsuario(models.Model):
    """Bloqueo temporal de usuarios por políticas de asistencia."""
    usuario = models.ForeignKey('usuarios.Usuario', on_delete=models.CASCADE, related_name='bloqueos')
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_fin = models.DateTimeField(null=True, blank=True, help_text="Fecha de fin del bloqueo")
    motivo = models.TextField(help_text="Motivo del bloqueo")
    activo = models.BooleanField(default=True)
    creado_por = models.ForeignKey('usuarios.Usuario', on_delete=models.SET_NULL, null=True, blank=True, related_name='bloqueos_creados')

    class Meta:
        db_table = 'bloqueo_usuario'
        verbose_name = 'Bloqueo de Usuario'
        verbose_name_plural = 'Bloqueos de Usuarios'
        ordering = ['-fecha_inicio']

    def __str__(self):
        return f"Bloqueo: {self.usuario} - {self.fecha_inicio} a {self.fecha_fin or 'indefinido'}"
