from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from apps.usuarios.models import Paciente
from apps.profesionales.models import Odontologo
from apps.administracion_clinica.models import Servicio


class PlanTratamiento(models.Model):
    """
    Plan de tratamiento propuesto por el odontólogo.
    CU19: Crear plan de tratamiento
    """
    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('aprobado', 'Aprobado'),
        ('en_proceso', 'En Proceso'),
        ('completado', 'Completado'),
        ('cancelado', 'Cancelado'),
    ]

    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,
        related_name='planes_tratamiento',
        db_column='pacientecodigo'
    )
    odontologo = models.ForeignKey(
        Odontologo,
        on_delete=models.SET_NULL,
        null=True,
        related_name='planes_creados',
        db_column='odontologocodigo'
    )
    codigo = models.CharField(max_length=50, unique=True, db_index=True)
    descripcion = models.TextField()
    diagnostico = models.TextField(blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='borrador', db_index=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_aprobacion = models.DateTimeField(blank=True, null=True)
    fecha_inicio = models.DateField(blank=True, null=True)
    fecha_finalizacion = models.DateField(blank=True, null=True)
    duracion_estimada_dias = models.IntegerField(blank=True, null=True, help_text="Duración estimada en días")

    class Meta:
        app_label = 'tratamientos'
        db_table = 'plan_tratamiento'
        verbose_name = 'Plan de Tratamiento'
        verbose_name_plural = 'Planes de Tratamiento'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"Plan {self.codigo} - {self.paciente}"

    def generar_codigo(self):
        """Genera código único para el plan"""
        import datetime
        fecha = datetime.datetime.now()
        ultimo = PlanTratamiento.objects.filter(
            codigo__startswith=f'PT-{fecha.year}'
        ).count()
        return f'PT-{fecha.year}{fecha.month:02d}-{ultimo + 1:04d}'

    def save(self, *args, **kwargs):
        if not self.codigo:
            self.codigo = self.generar_codigo()
        super().save(*args, **kwargs)

    def calcular_costo_total(self):
        """Calcula el costo total sumando todos los procedimientos"""
        procedimientos = self.procedimientos.all()
        total = sum(p.costo_estimado or Decimal('0') for p in procedimientos)
        return total

    def obtener_progreso(self):
        """Calcula el progreso del plan (% de procedimientos completados)"""
        total_procedimientos = self.procedimientos.count()
        if total_procedimientos == 0:
            return 0
        completados = self.procedimientos.filter(estado='completado').count()
        return round((completados / total_procedimientos) * 100, 2)


class Presupuesto(models.Model):
    """
    Presupuesto detallado para un plan de tratamiento.
    CU20: Generar presupuesto
    CU21: Aprobar/rechazar presupuesto
    """
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
        ('vencido', 'Vencido'),
    ]

    plan_tratamiento = models.ForeignKey(
        PlanTratamiento,
        on_delete=models.CASCADE,
        related_name='presupuestos',
        db_column='idplantratamiento'
    )
    codigo = models.CharField(max_length=50, unique=True, db_index=True)
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))]
    )
    descuento = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0'))]
    )
    impuesto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0'))]
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))]
    )
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente', db_index=True)
    notas = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_vencimiento = models.DateField(blank=True, null=True)
    fecha_aprobacion = models.DateTimeField(blank=True, null=True)
    aprobado_por = models.CharField(max_length=200, blank=True, null=True)
    motivo_rechazo = models.TextField(blank=True, null=True)

    class Meta:
        app_label = 'tratamientos'
        db_table = 'presupuesto'
        verbose_name = 'Presupuesto'
        verbose_name_plural = 'Presupuestos'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"Presupuesto {self.codigo} - {self.plan_tratamiento.paciente}"

    def generar_codigo(self):
        """Genera código único para el presupuesto"""
        import datetime
        fecha = datetime.datetime.now()
        ultimo = Presupuesto.objects.filter(
            codigo__startswith=f'PRES-{fecha.year}'
        ).count()
        return f'PRES-{fecha.year}{fecha.month:02d}-{ultimo + 1:04d}'

    def save(self, *args, **kwargs):
        if not self.codigo:
            self.codigo = self.generar_codigo()
        # Calcular total automáticamente
        self.total = self.subtotal - self.descuento + self.impuesto
        super().save(*args, **kwargs)

    def calcular_totales(self):
        """Calcula subtotal sumando items"""
        items = self.items.all()
        self.subtotal = sum(item.total for item in items)
        self.total = self.subtotal - self.descuento + self.impuesto
        return self.total


class ItemPresupuesto(models.Model):
    """
    Ítems individuales del presupuesto (servicios/tratamientos).
    """
    presupuesto = models.ForeignKey(
        Presupuesto,
        on_delete=models.CASCADE,
        related_name='items',
        db_column='idpresupuesto'
    )
    servicio = models.ForeignKey(
        Servicio,
        on_delete=models.CASCADE,
        db_column='idservicio'
    )
    descripcion = models.TextField(blank=True, null=True, help_text="Descripción adicional del servicio")
    cantidad = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))]
    )
    descuento_item = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0'))]
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))]
    )
    numero_diente = models.IntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1)],
        help_text="Número de diente si aplica (1-32)"
    )

    class Meta:
        app_label = 'tratamientos'
        db_table = 'item_presupuesto'
        verbose_name = 'Item de Presupuesto'
        verbose_name_plural = 'Items de Presupuesto'
        ordering = ['id']

    def __str__(self):
        return f"{self.servicio.nombreservicio} - {self.cantidad}x"

    def save(self, *args, **kwargs):
        # Calcular total del item
        subtotal_item = self.precio_unitario * self.cantidad
        self.total = subtotal_item - self.descuento_item
        super().save(*args, **kwargs)


class Procedimiento(models.Model):
    """
    Procedimientos/tratamientos realizados en el plan.
    CU24: Registrar procedimiento realizado
    """
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('en_proceso', 'En Proceso'),
        ('completado', 'Completado'),
        ('cancelado', 'Cancelado'),
    ]

    plan_tratamiento = models.ForeignKey(
        PlanTratamiento,
        on_delete=models.CASCADE,
        related_name='procedimientos',
        db_column='idplantratamiento'
    )
    servicio = models.ForeignKey(
        Servicio,
        on_delete=models.CASCADE,
        db_column='idservicio'
    )
    odontologo = models.ForeignKey(
        Odontologo,
        on_delete=models.SET_NULL,
        null=True,
        db_column='odontologocodigo'
    )
    numero_diente = models.IntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1)],
        help_text="Número de diente tratado (1-32)"
    )
    descripcion = models.TextField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente', db_index=True)
    fecha_planificada = models.DateField(blank=True, null=True)
    fecha_realizado = models.DateTimeField(blank=True, null=True)
    duracion_minutos = models.IntegerField(blank=True, null=True)
    costo_estimado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal('0'))]
    )
    costo_real = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal('0'))]
    )
    notas = models.TextField(blank=True, null=True)
    complicaciones = models.TextField(blank=True, null=True)

    class Meta:
        app_label = 'tratamientos'
        db_table = 'procedimiento'
        verbose_name = 'Procedimiento'
        verbose_name_plural = 'Procedimientos'
        ordering = ['fecha_planificada', 'id']

    def __str__(self):
        return f"{self.servicio.nombreservicio} - {self.estado}"

    def marcar_completado(self):
        """Marca el procedimiento como completado"""
        from django.utils import timezone
        self.estado = 'completado'
        self.fecha_realizado = timezone.now()
        self.save()


class SesionTratamiento(models.Model):
    """
    Sesión de tratamiento - registro de una consulta/cita donde se realizan procedimientos.
    Permite agrupar múltiples procedimientos en una misma sesión.
    """
    ESTADO_CHOICES = [
        ('programada', 'Programada'),
        ('en_curso', 'En Curso'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada'),
    ]

    plan_tratamiento = models.ForeignKey(
        PlanTratamiento,
        on_delete=models.CASCADE,
        related_name='sesiones',
        db_column='idplantratamiento'
    )
    odontologo = models.ForeignKey(
        Odontologo,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sesiones_realizadas',
        db_column='odontologocodigo'
    )
    codigo = models.CharField(max_length=50, unique=True, db_index=True)
    numero_sesion = models.IntegerField(help_text='Número de sesión dentro del plan')
    titulo = models.CharField(max_length=200, help_text='Título descriptivo de la sesión')
    descripcion = models.TextField(blank=True, null=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='programada', db_index=True)
    fecha_programada = models.DateTimeField()
    fecha_inicio = models.DateTimeField(blank=True, null=True)
    fecha_fin = models.DateTimeField(blank=True, null=True)
    duracion_minutos = models.IntegerField(blank=True, null=True, help_text='Duración real de la sesión')
    observaciones = models.TextField(blank=True, null=True)
    recomendaciones = models.TextField(blank=True, null=True, help_text='Recomendaciones post-sesión')
    proxima_sesion_programada = models.DateField(blank=True, null=True)
    
    class Meta:
        app_label = 'tratamientos'
        db_table = 'sesion_tratamiento'
        verbose_name = 'Sesión de Tratamiento'
        verbose_name_plural = 'Sesiones de Tratamiento'
        ordering = ['-fecha_programada']
        unique_together = [['plan_tratamiento', 'numero_sesion']]

    def __str__(self):
        return f"Sesión {self.numero_sesion} - {self.plan_tratamiento.codigo}"

    def generar_codigo(self):
        """Genera código único para la sesión"""
        import datetime
        fecha = datetime.datetime.now()
        ultimo = SesionTratamiento.objects.filter(
            codigo__startswith=f'SES-{fecha.year}'
        ).count()
        return f'SES-{fecha.year}{fecha.month:02d}-{ultimo + 1:04d}'

    def save(self, *args, **kwargs):
        if not self.codigo:
            self.codigo = self.generar_codigo()
        if not self.numero_sesion:
            # Auto-incrementar número de sesión
            ultima_sesion = SesionTratamiento.objects.filter(
                plan_tratamiento=self.plan_tratamiento
            ).order_by('-numero_sesion').first()
            self.numero_sesion = (ultima_sesion.numero_sesion + 1) if ultima_sesion else 1
        super().save(*args, **kwargs)

    def marcar_completada(self):
        """Marca la sesión como completada"""
        from django.utils import timezone
        self.estado = 'completada'
        if not self.fecha_inicio:
            self.fecha_inicio = timezone.now()
        self.fecha_fin = timezone.now()
        if self.fecha_inicio and self.fecha_fin:
            duracion = (self.fecha_fin - self.fecha_inicio).total_seconds() / 60
            self.duracion_minutos = int(duracion)
        self.save()


class HistorialPago(models.Model):
    """
    Historial de pagos realizados para un plan de tratamiento.
    Registra todos los pagos parciales o totales que hace el paciente.
    """
    METODO_PAGO_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('tarjeta', 'Tarjeta de Crédito/Débito'),
        ('transferencia', 'Transferencia Bancaria'),
        ('cheque', 'Cheque'),
        ('qr', 'Código QR'),
    ]

    ESTADO_PAGO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('completado', 'Completado'),
        ('cancelado', 'Cancelado'),
        ('reembolsado', 'Reembolsado'),
    ]

    plan_tratamiento = models.ForeignKey(
        PlanTratamiento,
        on_delete=models.CASCADE,
        related_name='pagos',
        db_column='idplantratamiento'
    )
    presupuesto = models.ForeignKey(
        Presupuesto,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pagos',
        db_column='idpresupuesto',
        help_text='Presupuesto asociado si existe'
    )
    codigo = models.CharField(max_length=50, unique=True, db_index=True)
    monto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO_CHOICES)
    estado = models.CharField(max_length=20, choices=ESTADO_PAGO_CHOICES, default='completado', db_index=True)
    fecha_pago = models.DateTimeField(auto_now_add=True)
    numero_comprobante = models.CharField(max_length=100, blank=True, null=True, help_text='Número de recibo o comprobante')
    numero_transaccion = models.CharField(max_length=100, blank=True, null=True, help_text='ID de transacción bancaria')
    notas = models.TextField(blank=True, null=True)
    registrado_por = models.CharField(max_length=200, help_text='Usuario que registró el pago')

    class Meta:
        app_label = 'tratamientos'
        db_table = 'historial_pago'
        verbose_name = 'Historial de Pago'
        verbose_name_plural = 'Historial de Pagos'
        ordering = ['-fecha_pago']

    def __str__(self):
        return f"Pago {self.codigo} - Bs. {self.monto}"

    def generar_codigo(self):
        """Genera código único para el pago"""
        import datetime
        fecha = datetime.datetime.now()
        ultimo = HistorialPago.objects.filter(
            codigo__startswith=f'PAG-{fecha.year}'
        ).count()
        return f'PAG-{fecha.year}{fecha.month:02d}-{ultimo + 1:04d}'

    def save(self, *args, **kwargs):
        if not self.codigo:
            self.codigo = self.generar_codigo()
        super().save(*args, **kwargs)
