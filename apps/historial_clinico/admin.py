from django.contrib import admin
from .models import Historialclinico, DocumentoClinico


@admin.register(Historialclinico)
class HistorialclinicoAdmin(admin.ModelAdmin):
    list_display = ('id', 'pacientecodigo', 'fecha')
    list_filter = ('fecha',)
    search_fields = ('pacientecodigo__codusuario__nombre', 'descripcion')


@admin.register(DocumentoClinico)
class DocumentoClinicoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'tipo_documento', 'historial', 'fecha_subida')
    list_filter = ('tipo_documento', 'fecha_subida')
    search_fields = ('titulo', 'descripcion')
