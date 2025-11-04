from django.db import models


class Horario(models.Model):
    hora = models.TimeField(unique=True)

    class Meta:
        db_table = "horario"
        verbose_name = "Horario"
        verbose_name_plural = "Horarios"
        ordering = ["hora"]

    def __str__(self):
        return str(self.hora)


class Estadodeconsulta(models.Model):
    estado = models.CharField(unique=True, max_length=100)

    class Meta:
        db_table = "estadodeconsulta"
        verbose_name = "Estado de Consulta"
        verbose_name_plural = "Estados de Consulta"
        ordering = ["estado"]

    def __str__(self):
        return self.estado


class Tipodeconsulta(models.Model):
    nombreconsulta = models.CharField(max_length=255, unique=True)
    permite_agendamiento_web = models.BooleanField(
        default=False, help_text="Pacientes pueden agendar desde la web"
    )
    requiere_aprobacion = models.BooleanField(
        default=False, help_text="Requiere aprobacion de staff antes de confirmar"
    )
    es_urgencia = models.BooleanField(
        default=False, help_text="Es consulta urgente (prioridad alta)"
    )
    duracion_estimada = models.IntegerField(
        default=30, help_text="Duracion estimada en minutos"
    )

    class Meta:
        db_table = "tipodeconsulta"
        verbose_name = "Tipo de Consulta"
        verbose_name_plural = "Tipos de Consulta"
        ordering = ["nombreconsulta"]

    def __str__(self):
        return self.nombreconsulta


class Consulta(models.Model):
    ESTADOS_CONSULTA = [
        ("pendiente", "Pendiente"),
        ("confirmada", "Confirmada"),
        ("en_consulta", "En Consulta"),
        ("diagnosticada", "Diagnosticada"),
        ("con_plan", "Con Plan"),
        ("completada", "Completada"),
        ("cancelada", "Cancelada"),
        ("no_asistio", "No Asistio"),
    ]

    TIPOS_CONSULTA = [
        ("primera_vez", "Primera Vez"),
        ("control", "Control"),
        ("tratamiento", "Tratamiento"),
        ("urgencia", "Urgencia"),
    ]

    HORARIOS_PREFERIDOS = [
        ("manana", "Manana (8am-12pm)"),
        ("tarde", "Tarde (2pm-6pm)"),
        ("noche", "Noche (6pm-8pm)"),
        ("cualquiera", "Cualquier horario"),
    ]

    fecha = models.DateField()
    codpaciente = models.ForeignKey("usuarios.Paciente", on_delete=models.DO_NOTHING, db_column="codpaciente")
    cododontologo = models.ForeignKey("profesionales.Odontologo", on_delete=models.DO_NOTHING, db_column="cododontologo", blank=True, null=True)
    codrecepcionista = models.ForeignKey("profesionales.Recepcionista", on_delete=models.DO_NOTHING, db_column="codrecepcionista", blank=True, null=True)
    idhorario = models.ForeignKey("Horario", on_delete=models.DO_NOTHING, db_column="idhorario")
    idtipoconsulta = models.ForeignKey("Tipodeconsulta", on_delete=models.DO_NOTHING, db_column="idtipoconsulta")
    idestadoconsulta = models.ForeignKey("Estadodeconsulta", on_delete=models.DO_NOTHING, db_column="idestadoconsulta")
    
    estado = models.CharField(max_length=20, choices=ESTADOS_CONSULTA, default="pendiente")
    fecha_preferida = models.DateField(null=True, blank=True)
    horario_preferido = models.CharField(max_length=20, choices=HORARIOS_PREFERIDOS, default="cualquiera")
    fecha_consulta = models.DateField(null=True, blank=True)
    hora_consulta = models.TimeField(null=True, blank=True)
    hora_llegada = models.DateTimeField(null=True, blank=True)
    hora_inicio_consulta = models.DateTimeField(null=True, blank=True)
    hora_fin_consulta = models.DateTimeField(null=True, blank=True)
    tipo_consulta = models.CharField(max_length=20, choices=TIPOS_CONSULTA, null=True, blank=True)
    motivo_consulta = models.TextField(null=True, blank=True)
    notas_recepcion = models.TextField(null=True, blank=True)
    motivo_cancelacion = models.TextField(null=True, blank=True)
    duracion_estimada = models.IntegerField(null=True, blank=True)
    observaciones = models.TextField(null=True, blank=True)
    diagnostico = models.TextField(null=True, blank=True)
    tratamiento = models.TextField(null=True, blank=True)
    costo_consulta = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    requiere_pago = models.BooleanField(default=False)

    class Meta:
        db_table = "consulta"
        verbose_name = "Consulta"
        verbose_name_plural = "Consultas"
        ordering = ["-fecha"]

    def __str__(self):
        return f"Consulta {self.id} - {self.codpaciente} - {self.fecha}"
