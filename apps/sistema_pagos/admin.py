from django.contrib import admin
from .models import Tipopago, Estadodefactura, Factura, Itemdefactura, Pago, PagoEnLinea


@admin.register(Tipopago)
class TipopagoAdmin(admin.ModelAdmin):
    list_display = ('nombrepago',)


@admin.register(Estadodefactura)
class EstadodefacturaAdmin(admin.ModelAdmin):
    list_display = ('estado',)


@admin.register(Factura)
class FacturaAdmin(admin.ModelAdmin):
    list_display = ('id', 'fechaemision', 'montototal', 'idestadofactura')
    list_filter = ('idestadofactura', 'fechaemision')


@admin.register(Itemdefactura)
class ItemdefacturaAdmin(admin.ModelAdmin):
    list_display = ('idfactura', 'descripcion', 'monto')


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ('id', 'idfactura', 'idtipopago', 'montopagado', 'fechapago')
    list_filter = ('idtipopago', 'fechapago')


@admin.register(PagoEnLinea)
class PagoEnLineaAdmin(admin.ModelAdmin):
    list_display = ('codigo_pago', 'estado', 'monto', 'metodo_pago', 'fecha_creacion')
    list_filter = ('estado', 'metodo_pago', 'origen_tipo')
    search_fields = ('codigo_pago', 'stripe_payment_intent_id')
