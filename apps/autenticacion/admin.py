from django.contrib import admin
from .models import BloqueoUsuario


@admin.register(BloqueoUsuario)
class BloqueoUsuarioAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'fecha_inicio', 'fecha_fin', 'activo', 'motivo_corto')
    list_filter = ('activo', 'fecha_inicio')
    search_fields = ('usuario__nombre', 'usuario__apellido', 'motivo')
    
    def motivo_corto(self, obj):
        return obj.motivo[:50] + '...' if len(obj.motivo) > 50 else obj.motivo
    motivo_corto.short_description = 'Motivo'
