"""
Admin para modelos de inventario en Django Admin.
"""
from django.contrib import admin
from .models_inventario import CategoriaInsumo, Proveedor, Insumo, MovimientoInventario, AlertaInventario


@admin.register(CategoriaInsumo)
class CategoriaInsumoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'activo', 'fecha_creacion']
    search_fields = ['nombre']
    list_filter = ['activo']


@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'ruc', 'telefono', 'email', 'activo']
    search_fields = ['nombre', 'ruc', 'email']
    list_filter = ['activo']


@admin.register(Insumo)
class InsumoAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'categoria', 'stock_actual', 'stock_minimo', 'precio_compra', 'requiere_reposicion']
    search_fields = ['codigo', 'nombre']
    list_filter = ['categoria', 'activo', 'requiere_vencimiento']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']


@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(admin.ModelAdmin):
    list_display = ['insumo', 'tipo_movimiento', 'cantidad', 'stock_anterior', 'stock_nuevo', 'fecha_movimiento']
    search_fields = ['insumo__nombre', 'motivo']
    list_filter = ['tipo_movimiento', 'fecha_movimiento']
    readonly_fields = ['fecha_movimiento', 'stock_anterior', 'stock_nuevo']


@admin.register(AlertaInventario)
class AlertaInventarioAdmin(admin.ModelAdmin):
    list_display = ['insumo', 'tipo_alerta', 'prioridad', 'resuelta', 'fecha_creacion']
    search_fields = ['insumo__nombre', 'mensaje']
    list_filter = ['tipo_alerta', 'prioridad', 'resuelta']
    readonly_fields = ['fecha_creacion']
