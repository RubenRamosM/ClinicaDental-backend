"""
Modelos para gestión de inventario.
CU27: Gestión de Inventario
"""
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class CategoriaInsumo(models.Model):
    """
    Categorías de insumos (Materiales, Medicamentos, Instrumental, etc.)
    """
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        app_label = 'admin_dashboard'
        db_table = 'categoria_insumo'
        verbose_name = 'Categoría de Insumo'
        verbose_name_plural = 'Categorías de Insumos'
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre


class Proveedor(models.Model):
    """
    Proveedores de insumos y materiales.
    """
    nombre = models.CharField(max_length=200)
    ruc = models.CharField(max_length=20, unique=True)
    direccion = models.TextField(blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    contacto_nombre = models.CharField(max_length=100, blank=True, null=True)
    contacto_telefono = models.CharField(max_length=20, blank=True, null=True)
    activo = models.BooleanField(default=True)
    notas = models.TextField(blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        app_label = 'admin_dashboard'
        db_table = 'proveedor'
        verbose_name = 'Proveedor'
        verbose_name_plural = 'Proveedores'
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.nombre} ({self.ruc})"


class Insumo(models.Model):
    """
    Insumos y materiales del inventario.
    """
    UNIDADES_MEDIDA = [
        ('unidad', 'Unidad'),
        ('caja', 'Caja'),
        ('paquete', 'Paquete'),
        ('litro', 'Litro'),
        ('mililitro', 'Mililitro'),
        ('gramo', 'Gramo'),
        ('kilogramo', 'Kilogramo'),
        ('metro', 'Metro'),
        ('otro', 'Otro'),
    ]
    
    codigo = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    categoria = models.ForeignKey(
        CategoriaInsumo, 
        on_delete=models.PROTECT,
        related_name='insumos'
    )
    proveedor_principal = models.ForeignKey(
        Proveedor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='insumos'
    )
    
    # Stock
    stock_actual = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0'))]
    )
    stock_minimo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=5,
        validators=[MinValueValidator(Decimal('0'))]
    )
    stock_maximo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=100,
        validators=[MinValueValidator(Decimal('0'))]
    )
    unidad_medida = models.CharField(
        max_length=20,
        choices=UNIDADES_MEDIDA,
        default='unidad'
    )
    
    # Precios
    precio_compra = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0'))]
    )
    precio_venta = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0'))],
        blank=True,
        null=True
    )
    
    # Control
    requiere_vencimiento = models.BooleanField(default=False)
    fecha_vencimiento = models.DateField(blank=True, null=True)
    lote = models.CharField(max_length=50, blank=True, null=True)
    ubicacion = models.CharField(max_length=100, blank=True, null=True)
    activo = models.BooleanField(default=True)
    
    # Auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'admin_dashboard'
        db_table = 'insumo'
        verbose_name = 'Insumo'
        verbose_name_plural = 'Insumos'
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"
    
    @property
    def requiere_reposicion(self):
        """Verifica si el stock está por debajo del mínimo."""
        return self.stock_actual <= self.stock_minimo
    
    @property
    def estado_stock(self):
        """Retorna el estado del stock: bajo, normal, alto."""
        if self.stock_actual <= self.stock_minimo:
            return 'bajo'
        elif self.stock_actual >= self.stock_maximo:
            return 'alto'
        else:
            return 'normal'
    
    @property
    def valor_inventario(self):
        """Calcula el valor total del inventario (stock * precio_compra)."""
        return self.stock_actual * self.precio_compra


class MovimientoInventario(models.Model):
    """
    Registro de movimientos de inventario (entradas y salidas).
    """
    TIPOS_MOVIMIENTO = [
        ('entrada', 'Entrada'),
        ('salida', 'Salida'),
        ('ajuste', 'Ajuste'),
        ('devolucion', 'Devolución'),
        ('merma', 'Merma'),
    ]
    
    insumo = models.ForeignKey(
        Insumo,
        on_delete=models.PROTECT,
        related_name='movimientos'
    )
    tipo_movimiento = models.CharField(max_length=20, choices=TIPOS_MOVIMIENTO)
    cantidad = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    stock_anterior = models.DecimalField(max_digits=10, decimal_places=2)
    stock_nuevo = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Información adicional
    motivo = models.TextField()
    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimientos'
    )
    numero_factura = models.CharField(max_length=50, blank=True, null=True)
    costo_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0'))]
    )
    costo_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0'))]
    )
    
    # Auditoría
    fecha_movimiento = models.DateTimeField(auto_now_add=True)
    realizado_por = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        related_name='movimientos_inventario'
    )
    notas = models.TextField(blank=True, null=True)
    
    class Meta:
        app_label = 'admin_dashboard'
        db_table = 'movimiento_inventario'
        verbose_name = 'Movimiento de Inventario'
        verbose_name_plural = 'Movimientos de Inventario'
        ordering = ['-fecha_movimiento']
    
    def __str__(self):
        return f"{self.tipo_movimiento.upper()} - {self.insumo.nombre} ({self.cantidad} {self.insumo.unidad_medida})"
    
    def save(self, *args, **kwargs):
        """
        Override save para actualizar el stock del insumo automáticamente.
        """
        if not self.pk:  # Solo en creación
            # Guardar stock anterior
            self.stock_anterior = self.insumo.stock_actual
            
            # Calcular nuevo stock según tipo de movimiento
            if self.tipo_movimiento in ['entrada', 'devolucion']:
                self.stock_nuevo = self.stock_anterior + self.cantidad
            elif self.tipo_movimiento in ['salida', 'merma']:
                self.stock_nuevo = self.stock_anterior - self.cantidad
            elif self.tipo_movimiento == 'ajuste':
                # Para ajustes, la cantidad es el nuevo stock total
                self.stock_nuevo = self.cantidad
            
            # Actualizar stock del insumo
            self.insumo.stock_actual = self.stock_nuevo
            self.insumo.save()
            
            # Calcular costo total
            if self.costo_unitario > 0:
                self.costo_total = self.cantidad * self.costo_unitario
        
        super().save(*args, **kwargs)


class AlertaInventario(models.Model):
    """
    Alertas automáticas de inventario.
    """
    TIPOS_ALERTA = [
        ('stock_bajo', 'Stock Bajo'),
        ('stock_agotado', 'Stock Agotado'),
        ('proximo_vencer', 'Próximo a Vencer'),
        ('vencido', 'Vencido'),
    ]
    
    insumo = models.ForeignKey(
        Insumo,
        on_delete=models.CASCADE,
        related_name='alertas'
    )
    tipo_alerta = models.CharField(max_length=20, choices=TIPOS_ALERTA)
    mensaje = models.TextField()
    prioridad = models.CharField(
        max_length=10,
        choices=[
            ('baja', 'Baja'),
            ('media', 'Media'),
            ('alta', 'Alta'),
            ('critica', 'Crítica'),
        ],
        default='media'
    )
    resuelta = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_resolucion = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        app_label = 'admin_dashboard'
        db_table = 'alerta_inventario'
        verbose_name = 'Alerta de Inventario'
        verbose_name_plural = 'Alertas de Inventario'
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"{self.tipo_alerta} - {self.insumo.nombre}"
