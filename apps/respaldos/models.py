from django.db import models


class Respaldo(models.Model):
    nombre_archivo = models.CharField(max_length=255)
    ruta_archivo = models.CharField(max_length=512)
    tipo_respaldo = models.CharField(max_length=50, choices=[
        ('COMPLETO', 'Completo'),
        ('INCREMENTAL', 'Incremental'),
        ('MANUAL', 'Manual')
    ])
    tamaño_bytes = models.BigIntegerField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    creado_por = models.ForeignKey('usuarios.Usuario', on_delete=models.SET_NULL, null=True, blank=True, related_name='respaldos_creados')
    estado = models.CharField(max_length=20, choices=[
        ('EXITOSO', 'Exitoso'),
        ('FALLIDO', 'Fallido'),
        ('EN_PROCESO', 'En Proceso')
    ], default='EXITOSO')
    notas = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'respaldo'
        verbose_name = 'Respaldo'
        verbose_name_plural = 'Respaldos'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f'{self.nombre_archivo} - {self.fecha_creacion.strftime("%Y-%m-%d %H:%M")}'
