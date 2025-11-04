from django.contrib import admin
from .models import Respaldo


@admin.register(Respaldo)
class RespaldoAdmin(admin.ModelAdmin):
    list_display = ('nombre_archivo', 'tipo_respaldo', 'estado', 'tamaño_mb', 'fecha_creacion', 'creado_por')
    list_filter = ('tipo_respaldo', 'estado', 'fecha_creacion')
    search_fields = ('nombre_archivo', 'notas')
    readonly_fields = ('fecha_creacion',)

    def tamaño_mb(self, obj):
        if obj.tamaño_bytes:
            return f'{obj.tamaño_bytes / (1024 * 1024):.2f} MB'
        return '-'
    tamaño_mb.short_description = 'Tamaño'
