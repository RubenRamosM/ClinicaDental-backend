from django.contrib import admin
from .models import Tipodeusuario, Usuario, Paciente


@admin.register(Tipodeusuario)
class TipodeusuarioAdmin(admin.ModelAdmin):
    list_display = ('rol', 'descripcion')
    search_fields = ('rol',)


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'apellido', 'correoelectronico', 'idtipousuario', 'telefono')
    list_filter = ('idtipousuario', 'sexo')
    search_fields = ('nombre', 'apellido', 'correoelectronico')


@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = ('codusuario', 'carnetidentidad', 'fechanacimiento')
    search_fields = ('carnetidentidad', 'codusuario__nombre', 'codusuario__apellido')
