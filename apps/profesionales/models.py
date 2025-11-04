from django.db import models


class Odontologo(models.Model):
    codusuario = models.OneToOneField('usuarios.Usuario', on_delete=models.DO_NOTHING, db_column='codusuario', primary_key=True)
    especialidad = models.CharField(max_length=255, blank=True, null=True)
    experienciaprofesional = models.TextField(blank=True, null=True)
    nromatricula = models.CharField(unique=True, max_length=100, blank=True, null=True)

    class Meta:
        db_table = 'odontologo'
        verbose_name = 'Odontólogo'
        verbose_name_plural = 'Odontólogos'

    def __str__(self):
        return f'Dr(a). {self.codusuario.nombre} {self.codusuario.apellido}'


class Recepcionista(models.Model):
    codusuario = models.OneToOneField('usuarios.Usuario', on_delete=models.DO_NOTHING, db_column='codusuario', primary_key=True)
    habilidadessoftware = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'recepcionista'
        verbose_name = 'Recepcionista'
        verbose_name_plural = 'Recepcionistas'

    def __str__(self):
        return f'{self.codusuario.nombre} {self.codusuario.apellido}'
