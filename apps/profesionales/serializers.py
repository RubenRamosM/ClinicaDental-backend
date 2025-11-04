"""
Serializers para el módulo de profesionales.
"""
from rest_framework import serializers
from .models import Odontologo, Recepcionista
from apps.usuarios.serializers import UsuarioSerializer


class OdontologoSerializer(serializers.ModelSerializer):
    """Serializer para Odontólogos."""
    usuario = UsuarioSerializer(source='codusuario', read_only=True)
    nombre = serializers.CharField(source='codusuario.nombre', read_only=True)
    apellido = serializers.CharField(source='codusuario.apellido', read_only=True)
    email = serializers.EmailField(source='codusuario.correoelectronico', read_only=True)
    telefono = serializers.CharField(source='codusuario.telefono', read_only=True)
    activo = serializers.BooleanField(source='codusuario.activo', read_only=True, required=False)
    
    class Meta:
        model = Odontologo
        fields = [
            'codusuario', 'usuario', 'nombre', 'apellido', 'email', 'telefono',
            'especialidad', 'experienciaprofesional', 'nromatricula', 'activo'
        ]
        # Permitir escribir codusuario al crear
        read_only_fields = ['usuario', 'nombre', 'apellido', 'email', 'telefono', 'activo']


class RecepcionistaSerializer(serializers.ModelSerializer):
    """Serializer para Recepcionistas."""
    usuario = UsuarioSerializer(source='codusuario', read_only=True)
    nombre = serializers.CharField(source='codusuario.nombre', read_only=True)
    apellido = serializers.CharField(source='codusuario.apellido', read_only=True)
    email = serializers.EmailField(source='codusuario.correo', read_only=True)
    telefono = serializers.CharField(source='codusuario.telefono', read_only=True)
    activo = serializers.BooleanField(source='codusuario.activo', read_only=True)
    
    class Meta:
        model = Recepcionista
        fields = [
            'codusuario', 'usuario', 'nombre', 'apellido', 'email', 'telefono',
            'habilidadessoftware', 'activo'
        ]
        read_only_fields = ['codusuario', 'usuario']
