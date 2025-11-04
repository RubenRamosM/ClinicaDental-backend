from django.contrib import admin
from .models import Bitacora


@admin.register(Bitacora)
class BitacoraAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'usuario', 'accion', 'tabla_afectada', 'ip_address')
    list_filter = ('fecha', 'accion', 'tabla_afectada')
    search_fields = ('usuario__nombre', 'accion', 'detalles')
    readonly_fields = ('fecha', 'usuario', 'accion', 'tabla_afectada', 'registro_id', 'detalles', 'ip_address', 'user_agent')
    
    def has_add_permission(self, request):
        return False  # No se puede agregar manualmente
    
    def has_change_permission(self, request, obj=None):
        return False  # Solo lectura
