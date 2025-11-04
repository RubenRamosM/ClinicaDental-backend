from django.contrib import admin
from .models import Odontologo, Recepcionista


@admin.register(Odontologo)
class OdontologoAdmin(admin.ModelAdmin):
    list_display = ('codusuario', 'especialidad', 'nromatricula')
    search_fields = ('codusuario__nombre', 'codusuario__apellido', 'especialidad', 'nromatricula')


@admin.register(Recepcionista)
class RecepcionistaAdmin(admin.ModelAdmin):
    list_display = ('codusuario', 'habilidadessoftware')
    search_fields = ('codusuario__nombre', 'codusuario__apellido')
