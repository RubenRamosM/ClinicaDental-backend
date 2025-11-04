from django.db import models

# Importar modelos de inventario (CU27)
from .models_inventario import (
    CategoriaInsumo,
    Proveedor,
    Insumo,
    MovimientoInventario,
    AlertaInventario
)

# Importar modelos de tratamientos desde apps.tratamientos (CU19-21, CU24)
from apps.tratamientos.models import (
    PlanTratamiento,
    Presupuesto,
    ItemPresupuesto,
    Procedimiento,
    HistorialPago
)


class Historialclinico(models.Model):
    """
    Historia Clínica Electrónica (HCE) - Versión Completa
    Soporta todos los campos requeridos por el frontend
    """
    # ==================== CAMPOS BÁSICOS ====================
    pacientecodigo = models.ForeignKey(
        'usuarios.Paciente',
        on_delete=models.CASCADE,
        db_column='pacientecodigo',
        related_name='historiales',
        verbose_name='Paciente'
    )
    
    episodio = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Número de Episodio',
        help_text='Número secuencial de consulta para este paciente (auto-generado)'
    )
    
    fecha = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Actualización'
    )
    
    # ==================== MOTIVO Y DIAGNÓSTICO ====================
    motivoconsulta = models.TextField(
        verbose_name='Motivo de Consulta',
        help_text='Razón por la que el paciente consulta',
        blank=True,
        null=True
    )
    
    diagnostico = models.TextField(
        verbose_name='Diagnóstico',
        help_text='Diagnóstico médico/odontológico',
        blank=True,
        null=True
    )
    
    tratamiento = models.TextField(
        verbose_name='Tratamiento',
        help_text='Tratamiento prescrito o realizado',
        blank=True,
        null=True
    )
    
    # ==================== ANTECEDENTES ====================
    alergias = models.TextField(
        verbose_name='Alergias',
        help_text='Alergias conocidas del paciente',
        blank=True,
        null=True
    )
    
    enfermedades = models.TextField(
        verbose_name='Enfermedades',
        help_text='Enfermedades previas o crónicas',
        blank=True,
        null=True
    )
    
    antecedentesfamiliares = models.TextField(
        verbose_name='Antecedentes Familiares',
        help_text='Historial médico familiar relevante',
        blank=True,
        null=True
    )
    
    antecedentespersonales = models.TextField(
        verbose_name='Antecedentes Personales',
        help_text='Historial médico personal',
        blank=True,
        null=True
    )
    
    # ==================== EXÁMENES ====================
    examengeneral = models.TextField(
        verbose_name='Examen General',
        help_text='Resultados del examen físico general',
        blank=True,
        null=True
    )
    
    examenregional = models.TextField(
        verbose_name='Examen Regional',
        help_text='Examen regional o segmentario',
        blank=True,
        null=True
    )
    
    examenbucal = models.TextField(
        verbose_name='Examen Bucal',
        help_text='Examen odontológico específico',
        blank=True,
        null=True
    )
    
    # ==================== RECETA ====================
    receta = models.TextField(
        verbose_name='Receta Médica',
        help_text='Prescripción de medicamentos',
        blank=True,
        null=True
    )
    
    # ==================== CAMPO LEGACY (mantener compatibilidad) ====================
    descripcion = models.TextField(
        verbose_name='Descripción General',
        help_text='Campo general (legacy)',
        blank=True,
        null=True
    )
    
    class Meta:
        db_table = 'historialclinico'
        verbose_name = 'Historia Clínica'
        verbose_name_plural = 'Historias Clínicas'
        ordering = ['-fecha', '-episodio']
        unique_together = [['pacientecodigo', 'episodio']]
        indexes = [
            models.Index(fields=['pacientecodigo', '-fecha']),
            models.Index(fields=['pacientecodigo', 'episodio']),
        ]
    
    def __str__(self):
        if self.pacientecodigo and self.pacientecodigo.codusuario:
            paciente_nombre = f"{self.pacientecodigo.codusuario.nombre} {self.pacientecodigo.codusuario.apellido}"
        else:
            paciente_nombre = "Paciente desconocido"
        return f"HC #{self.id} - {paciente_nombre} - Episodio {self.episodio}"
    
    def save(self, *args, **kwargs):
        """
        Auto-incrementar episodio si no está definido.
        Usa transaction.atomic() + select_for_update() para evitar race conditions.
        """
        from django.db import transaction
        
        if not self.pk and not self.episodio:  # Solo en creación
            with transaction.atomic():
                # Bloquear registros del paciente para evitar race conditions
                ultimo = Historialclinico.objects.filter(
                    pacientecodigo=self.pacientecodigo
                ).select_for_update().order_by('-episodio').first()
                
                self.episodio = (ultimo.episodio + 1) if ultimo else 1
                
                # IMPORTANTE: super().save() debe estar DENTRO del atomic()
                # para mantener el lock hasta que el INSERT se complete
                super().save(*args, **kwargs)
        else:
            # Si ya tiene PK o episodio, guardar normalmente
            super().save(*args, **kwargs)


class DocumentoClinico(models.Model):
    historial = models.ForeignKey(Historialclinico, on_delete=models.CASCADE, related_name='documentos')
    titulo = models.CharField(max_length=255)
    descripcion = models.TextField(null=True, blank=True)
    archivo_url = models.CharField(max_length=512)
    tipo_documento = models.CharField(max_length=50, null=True, blank=True)
    fecha_subida = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'documento_clinico'
        verbose_name = 'Documento Clinico'
        verbose_name_plural = 'Documentos Clinicos'
        ordering = ['-fecha_subida']

    def __str__(self):
        return f'{self.titulo} - {self.tipo_documento}'


class Odontograma(models.Model):
    """Odontograma digital del paciente con 32 dientes."""
    
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
        'usuarios.Paciente',
        on_delete=models.CASCADE,
        related_name='odontogramas',
        db_column='pacientecodigo'
    )
    odontologo = models.ForeignKey(
        'profesionales.Odontologo',
        on_delete=models.PROTECT,
        related_name='odontogramas_realizados',
        null=True
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
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
                    'caras_afectadas': [],
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
    """Registro de tratamientos odontológicos realizados."""
    
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


class ConsentimientoInformado(models.Model):
    """
    Consentimiento informado digital firmado por el paciente.
    CU13: Gestionar consentimiento informado
    """
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente de Firma'),
        ('firmado', 'Firmado'),
        ('rechazado', 'Rechazado'),
        ('vencido', 'Vencido'),
    ]
    
    paciente = models.ForeignKey(
        'usuarios.Paciente',
        on_delete=models.CASCADE,
        db_column='pacientecodigo',
        related_name='consentimientos'
    )
    # ✅ NUEVO: Relación con la cita/consulta
    consulta = models.ForeignKey(
        'citas.Consulta',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='consentimientos',
        help_text="Cita/consulta asociada al consentimiento"
    )
    odontologo = models.ForeignKey(
        'profesionales.Odontologo',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='odontologocodigo',
        related_name='consentimientos_creados'
    )
    tipo_tratamiento = models.CharField(max_length=200)
    contenido_documento = models.TextField(
        help_text="Texto completo del consentimiento informado"
    )
    riesgos = models.TextField(
        blank=True,
        null=True,
        help_text="Riesgos asociados al tratamiento"
    )
    beneficios = models.TextField(
        blank=True,
        null=True,
        help_text="Beneficios esperados del tratamiento"
    )
    alternativas = models.TextField(
        blank=True,
        null=True,
        help_text="Tratamientos alternativos disponibles"
    )
    
    # Firma digital
    # ✅ CORREGIDO: TextField para soportar base64 largo (firmas pueden ser 10K-50K caracteres)
    firma_paciente_url = models.TextField(
        blank=True,
        null=True,
        help_text="URL o base64 data URI de la imagen de la firma del paciente"
    )
    firma_tutor_url = models.TextField(
        blank=True,
        null=True,
        help_text="URL o base64 data URI de la firma del tutor legal (para menores)"
    )
    nombre_tutor = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Nombre completo del tutor legal"
    )
    documento_tutor = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Documento de identidad del tutor"
    )
    
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='pendiente',
        db_index=True
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_firma = models.DateTimeField(blank=True, null=True)
    fecha_vencimiento = models.DateField(
        blank=True,
        null=True,
        help_text="Fecha hasta la cual es válido el consentimiento"
    )
    ip_firma = models.GenericIPAddressField(
        blank=True,
        null=True,
        help_text="Dirección IP desde donde se firmó"
    )
    notas = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'consentimiento_informado'
        verbose_name = 'Consentimiento Informado'
        verbose_name_plural = 'Consentimientos Informados'
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"{self.tipo_tratamiento} - {self.paciente} ({self.estado})"
    
    def esta_vigente(self):
        """Verifica si el consentimiento está vigente"""
        from django.utils import timezone
        if self.estado != 'firmado':
            return False
        if self.fecha_vencimiento and self.fecha_vencimiento < timezone.now().date():
            return False
        return True
