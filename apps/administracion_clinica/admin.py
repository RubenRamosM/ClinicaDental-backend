from django.contrib import admin
from .models import Servicio, ComboServicio, ComboServicioDetalle


@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'costobase', 'duracion', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombre',)


@admin.register(ComboServicio)
class ComboServicioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo_precio', 'valor_precio', 'activo')
    list_filter = ('activo', 'tipo_precio')


@admin.register(ComboServicioDetalle)
class ComboServicioDetalleAdmin(admin.ModelAdmin):
    list_display = ('combo', 'servicio', 'cantidad', 'orden')
    list_filter = ('combo',)
