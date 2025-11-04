from django.db import models
from decimal import Decimal


class Servicio(models.Model):
    nombre = models.CharField(max_length=255, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    costobase = models.DecimalField(max_digits=10, decimal_places=2)
    duracion = models.IntegerField(default=30, help_text="Duracion estimada en minutos")
    activo = models.BooleanField(default=True, help_text="Servicio disponible")
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)
    fecha_modificacion = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        db_table = "servicio"
        ordering = ["nombre"]
        verbose_name = "Servicio"
        verbose_name_plural = "Servicios"

    def __str__(self):
        return f"{self.nombre} - ${self.costobase}"


class ComboServicio(models.Model):
    TIPO_PRECIO_CHOICES = [
        ("PORCENTAJE", "Descuento Porcentual"),
        ("MONTO_FIJO", "Monto Fijo"),
        ("PROMOCION", "Precio Promocional"),
    ]

    nombre = models.CharField(max_length=255, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    tipo_precio = models.CharField(max_length=20, choices=TIPO_PRECIO_CHOICES, default="PORCENTAJE")
    valor_precio = models.DecimalField(max_digits=10, decimal_places=2)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "combo_servicio"
        ordering = ["-fecha_creacion"]
        verbose_name = "Combo de Servicios"
        verbose_name_plural = "Combos de Servicios"
        constraints = [
            models.CheckConstraint(
                check=models.Q(valor_precio__gte=0), name="combo_valor_precio_no_negativo"
            )
        ]

    def __str__(self):
        return self.nombre

    def calcular_precio_total_servicios(self):
        total = Decimal("0.00")
        for detalle in self.detalles.all():
            total += detalle.servicio.costobase * detalle.cantidad
        return total

    def calcular_precio_final(self):
        precio_servicios = self.calcular_precio_total_servicios()
        if self.tipo_precio == "PORCENTAJE":
            descuento = precio_servicios * (self.valor_precio / Decimal("100"))
            precio_final = precio_servicios - descuento
        elif self.tipo_precio == "MONTO_FIJO":
            precio_final = self.valor_precio
        elif self.tipo_precio == "PROMOCION":
            precio_final = self.valor_precio
        else:
            precio_final = precio_servicios
        if precio_final < 0:
            raise ValueError("El precio final no puede ser negativo")
        return precio_final

    def calcular_duracion_total(self):
        duracion_total = 0
        for detalle in self.detalles.all():
            duracion_total += detalle.servicio.duracion * detalle.cantidad
        return duracion_total


class ComboServicioDetalle(models.Model):
    combo = models.ForeignKey(ComboServicio, on_delete=models.CASCADE, related_name="detalles")
    servicio = models.ForeignKey(Servicio, on_delete=models.PROTECT, related_name="combos_detalle")
    cantidad = models.PositiveIntegerField(default=1)
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "combo_servicio_detalle"
        ordering = ["orden", "id"]
        verbose_name = "Detalle de Combo"
        verbose_name_plural = "Detalles de Combos"
        constraints = [
            models.UniqueConstraint(fields=["combo", "servicio"], name="unique_combo_servicio"),
            models.CheckConstraint(check=models.Q(cantidad__gt=0), name="combo_detalle_cantidad_positiva"),
        ]

    def __str__(self):
        return f"{self.servicio.nombre} x{self.cantidad} en {self.combo.nombre}"

    def calcular_subtotal(self):
        return self.servicio.costobase * self.cantidad
