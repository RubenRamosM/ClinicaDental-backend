"""
Modelos para Odontograma Digital.
"""
from django.db import models
from apps.usuarios.models import Paciente
from apps.profesionales.models import Odontologo


class Odontograma(models.Model):
    """
    Modelo para el odontograma digital del paciente.
    Estructura de 32 dientes con estados y tratamientos.
    """
    
    ESTADO_DIENTE_CHOICES = [
        ('sano', 'Sano'),
        ('caries', 'Caries'),
        ('obturacion', 'Obturación'),
        ('corona', 'Corona'),
        ('endodoncia', 'Endodoncia'),
        ('extraccion', 'Extracción'),
        ('ausente', 'Ausente'),
        ('implante', 'Implante'),
        ('protesis', 'Prótesis'),
        ('fractura', 'Fractura'),
    ]
    
    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,
        related_name='odontogramas'
    )
    odontologo = models.ForeignKey(
        Odontologo,
        on_delete=models.PROTECT,
        related_name='odontogramas_realizados'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    # Estructura JSON para los 32 dientes
    # Cada diente tiene: numero, estado, caras_afectadas[], observaciones
    dientes = models.JSONField(
        default=dict,
        help_text="Estructura JSON con información de los 32 dientes"
    )
    
    observaciones_generales = models.TextField(blank=True)
    
    class Meta:
        db_table = 'odontograma'
        verbose_name = 'Odontograma'
        verbose_name_plural = 'Odontogramas'
        ordering = ['-fecha_actualizacion']
    
    def __str__(self):
        return f"Odontograma de {self.paciente} - {self.fecha_actualizacion.date()}"
    
    def inicializar_dientes(self):
        """Inicializar estructura de 32 dientes sanos."""
        if not self.dientes:
            self.dientes = {}
            for num in range(1, 33):
                self.dientes[str(num)] = {
                    'numero': num,
                    'estado': 'sano',
                    'caras_afectadas': [],  # vestibular, lingual, mesial, distal, oclusal
                    'observaciones': '',
                    'tratamientos': []
                }
    
    def actualizar_diente(self, numero_diente, estado, caras=None, observaciones=''):
        """Actualizar el estado de un diente específico."""
        if not self.dientes:
            self.inicializar_dientes()
        
        diente_str = str(numero_diente)
        if diente_str in self.dientes:
            self.dientes[diente_str]['estado'] = estado
            if caras:
                self.dientes[diente_str]['caras_afectadas'] = caras
            if observaciones:
                self.dientes[diente_str]['observaciones'] = observaciones
            self.save()
    
    def obtener_estadisticas(self):
        """Obtener estadísticas del estado dental."""
        if not self.dientes:
            return {}
        
        stats = {}
        for diente in self.dientes.values():
            estado = diente.get('estado', 'sano')
            stats[estado] = stats.get(estado, 0) + 1
        
        return stats


class TratamientoOdontologico(models.Model):
    """
    Registro de tratamientos odontológicos realizados.
    """
    odontograma = models.ForeignKey(
        Odontograma,
        on_delete=models.CASCADE,
        related_name='tratamientos'
    )
    numero_diente = models.IntegerField(
        help_text="Número del diente tratado (1-32)"
    )
    tipo_tratamiento = models.CharField(max_length=100)
    descripcion = models.TextField()
    fecha_tratamiento = models.DateField()
    costo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    class Meta:
        db_table = 'tratamiento_odontologico'
        verbose_name = 'Tratamiento Odontológico'
        verbose_name_plural = 'Tratamientos Odontológicos'
        ordering = ['-fecha_tratamiento']
    
    def __str__(self):
        return f"{self.tipo_tratamiento} - Diente #{self.numero_diente}"
