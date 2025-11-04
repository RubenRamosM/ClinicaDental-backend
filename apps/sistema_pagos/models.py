from django.db import models


class Tipopago(models.Model):
    nombrepago = models.CharField(unique=True, max_length=100)

    class Meta:
        db_table = "tipopago"
        verbose_name = "Tipo de Pago"
        verbose_name_plural = "Tipos de Pago"
        ordering = ["nombrepago"]

    def __str__(self):
        return self.nombrepago


class Estadodefactura(models.Model):
    estado = models.CharField(unique=True, max_length=100)

    class Meta:
        db_table = "estadodefactura"
        verbose_name = "Estado de Factura"
        verbose_name_plural = "Estados de Factura"
        ordering = ["estado"]

    def __str__(self):
        return self.estado


class Factura(models.Model):
    fechaemision = models.DateField()
    montototal = models.DecimalField(max_digits=10, decimal_places=2)
    idestadofactura = models.ForeignKey(Estadodefactura, on_delete=models.DO_NOTHING, db_column="idestadofactura")

    class Meta:
        db_table = "factura"
        verbose_name = "Factura"
        verbose_name_plural = "Facturas"
        ordering = ["-fechaemision"]

    def __str__(self):
        return f"Factura {self.id} - {self.fechaemision}"


class Itemdefactura(models.Model):
    idfactura = models.ForeignKey(Factura, on_delete=models.DO_NOTHING, db_column="idfactura")
    descripcion = models.TextField()
    monto = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = "itemdefactura"
        verbose_name = "Item de Factura"
        verbose_name_plural = "Items de Factura"

    def __str__(self):
        return f"{self.descripcion} - ${self.monto}"


class Pago(models.Model):
    idfactura = models.ForeignKey(Factura, on_delete=models.DO_NOTHING, db_column="idfactura")
    idtipopago = models.ForeignKey(Tipopago, on_delete=models.DO_NOTHING, db_column="idtipopago")
    montopagado = models.DecimalField(max_digits=10, decimal_places=2)
    fechapago = models.DateField()

    class Meta:
        db_table = "pago"
        verbose_name = "Pago"
        verbose_name_plural = "Pagos"
        ordering = ["-fechapago"]

    def __str__(self):
        return f"Pago {self.id} - ${self.montopagado}"


class PagoEnLinea(models.Model):
    ORIGEN_CHOICES = [
        ("plan_completo", "Plan de Tratamiento Completo"),
        ("items_individuales", "Items Individuales del Plan"),
        ("consulta", "Consulta/Cita"),
    ]

    ESTADO_CHOICES = [
        ("pendiente", "Pendiente"),
        ("procesando", "Procesando"),
        ("aprobado", "Aprobado"),
        ("rechazado", "Rechazado"),
        ("cancelado", "Cancelado"),
        ("reembolsado", "Reembolsado"),
        ("anulado", "Anulado"),
    ]

    METODO_CHOICES = [
        ("tarjeta", "Tarjeta de Credito/Debito"),
        ("transferencia", "Transferencia Bancaria"),
        ("qr", "Codigo QR"),
    ]

    codigo_pago = models.CharField(max_length=50, unique=True)
    origen_tipo = models.CharField(max_length=30, choices=ORIGEN_CHOICES)
    consulta = models.ForeignKey("citas.Consulta", on_delete=models.PROTECT, related_name="pagos", null=True, blank=True)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    moneda = models.CharField(max_length=3, default="BOB")
    monto_original = models.DecimalField(max_digits=10, decimal_places=2)
    saldo_anterior = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    saldo_nuevo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default="pendiente")
    metodo_pago = models.CharField(max_length=20, choices=METODO_CHOICES, default="tarjeta")
    stripe_payment_intent_id = models.CharField(max_length=255, null=True, blank=True, unique=True)
    stripe_charge_id = models.CharField(max_length=255, null=True, blank=True)
    stripe_customer_id = models.CharField(max_length=255, null=True, blank=True)
    stripe_metadata = models.JSONField(default=dict, blank=True)
    descripcion = models.TextField()
    motivo_rechazo = models.TextField(null=True, blank=True)
    numero_intentos = models.IntegerField(default=0)
    ultimo_intento = models.DateTimeField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "pago_en_linea"
        verbose_name = "Pago en Linea"
        verbose_name_plural = "Pagos en Linea"
        ordering = ["-fecha_creacion"]

    def __str__(self):
        return f"{self.codigo_pago} - {self.estado} - ${self.monto}"
