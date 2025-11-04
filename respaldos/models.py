"""
Modelos para sistema de respaldos automáticos.
"""
from django.db import models
from django.utils import timezone
from datetime import timedelta


class Respaldo(models.Model):
    """
    Registro de respaldos realizados.
    Multitenancy: Cada clínica tiene sus propios respaldos.
    """
    TIPO_CHOICES = [
        ('completo', 'Respaldo Completo'),
        ('incremental', 'Respaldo Incremental'),
        ('manual', 'Respaldo Manual'),
    ]
    
    ESTADO_CHOICES = [
        ('en_proceso', 'En Proceso'),
        ('completado', 'Completado'),
        ('fallido', 'Fallido'),
    ]
    
    # Tipo y estado
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='completo')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='en_proceso')
    
    # Información del archivo
    nombre_archivo = models.CharField(max_length=255)
    ruta_nube = models.CharField(max_length=500, help_text='Ruta en S3')
    tamano_bytes = models.BigIntegerField(default=0)
    hash_md5 = models.CharField(max_length=32, help_text='Hash MD5 para verificar integridad')
    
    # Estadísticas
    tablas_respaldadas = models.JSONField(default=list, help_text='Lista de tablas incluidas')
    registros_totales = models.IntegerField(default=0)
    tiempo_ejecucion = models.DurationField(null=True, blank=True)
    
    # Metadata
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_expiracion = models.DateTimeField(
        help_text='Fecha en que se eliminará automáticamente',
        null=True,
        blank=True
    )
    notas = models.TextField(blank=True)
    error_mensaje = models.TextField(blank=True)
    
    # Usuario que solicitó el respaldo (si es manual)
    creado_por = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='respaldos_creados'
    )
    
    class Meta:
        db_table = 'respaldo'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['-fecha_creacion']),
            models.Index(fields=['estado', 'fecha_creacion']),
        ]
    
    def __str__(self):
        return f"Respaldo {self.id} - {self.fecha_creacion.strftime('%Y-%m-%d %H:%M')}"
    
    def get_tamano_legible(self):
        """Retorna el tamaño en formato legible"""
        tamano = self.tamano_bytes
        for unidad in ['bytes', 'KB', 'MB', 'GB']:
            if tamano < 1024.0:
                return f"{tamano:.2f} {unidad}"
            tamano /= 1024.0
        return f"{tamano:.2f} TB"
    
    def marcar_para_expiracion(self, dias=30):
        """Marca el respaldo para eliminación después de X días"""
        self.fecha_expiracion = timezone.now() + timedelta(days=dias)
        self.save()
