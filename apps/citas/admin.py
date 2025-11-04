from django.contrib import admin
from .models import Horario, Estadodeconsulta, Tipodeconsulta, Consulta


@admin.register(Horario)
class HorarioAdmin(admin.ModelAdmin):
    list_display = ('hora',)


@admin.register(Estadodeconsulta)
class EstadodeconsultaAdmin(admin.ModelAdmin):
    list_display = ('estado',)


@admin.register(Tipodeconsulta)
class TipodeconsultaAdmin(admin.ModelAdmin):
    list_display = ('nombreconsulta', 'permite_agendamiento_web', 'duracion_estimada', 'es_urgencia')
    list_filter = ('permite_agendamiento_web', 'es_urgencia', 'requiere_aprobacion')


@admin.register(Consulta)
class ConsultaAdmin(admin.ModelAdmin):
    list_display = ('id', 'fecha', 'codpaciente', 'cododontologo', 'estado', 'idtipoconsulta')
    list_filter = ('estado', 'fecha', 'idtipoconsulta')
    search_fields = ('codpaciente__codusuario__nombre', 'codpaciente__codusuario__apellido')
