"""
Serializers para la app de usuarios.
"""
from rest_framework import serializers
from .models import Tipodeusuario, Usuario, Paciente


class TipodeusuarioSerializer(serializers.ModelSerializer):
    """Serializer para tipos de usuario."""
    
    class Meta:
        model = Tipodeusuario
        fields = ['id', 'rol', 'descripcion']
        read_only_fields = ['id']


class UsuarioSerializer(serializers.ModelSerializer):
    """Serializer básico para Usuario."""
    tipo_usuario_nombre = serializers.CharField(source='idtipousuario.rol', read_only=True)
    nombre_completo = serializers.SerializerMethodField()
    
    class Meta:
        model = Usuario
        fields = [
            'codigo', 'nombre', 'apellido', 'correoelectronico', 'sexo',
            'telefono', 'idtipousuario', 'tipo_usuario_nombre', 'nombre_completo',
            'recibir_notificaciones', 'notificaciones_email', 'notificaciones_push'
        ]
        read_only_fields = ['codigo']
        extra_kwargs = {
            'correoelectronico': {'required': True},
            'idtipousuario': {'required': True}
        }
    
    def get_nombre_completo(self, obj):
        return f"{obj.nombre} {obj.apellido}"


class UsuarioDetalleSerializer(UsuarioSerializer):
    """Serializer detallado para Usuario (incluye relaciones)."""
    paciente = serializers.SerializerMethodField()
    
    class Meta(UsuarioSerializer.Meta):
        fields = UsuarioSerializer.Meta.fields + ['paciente']
    
    def get_paciente(self, obj):
        try:
            paciente = obj.paciente
            return {
                'carnet': paciente.carnetidentidad,
                'fecha_nacimiento': paciente.fechanacimiento,
                'direccion': paciente.direccion
            }
        except:
            return None


class PacienteSerializer(serializers.ModelSerializer):
    """Serializer para Paciente."""
    usuario = UsuarioSerializer(source='codusuario', read_only=True)
    nombre = serializers.CharField(source='codusuario.nombre', read_only=True)
    apellido = serializers.CharField(source='codusuario.apellido', read_only=True)
    correo = serializers.EmailField(source='codusuario.correoelectronico', read_only=True)
    telefono = serializers.CharField(source='codusuario.telefono', read_only=True)
    edad = serializers.SerializerMethodField()
    
    class Meta:
        model = Paciente
        fields = [
            'codusuario', 'usuario', 'nombre', 'apellido', 'correo', 'telefono',
            'carnetidentidad', 'fechanacimiento', 'edad', 'direccion'
        ]
        read_only_fields = ['codusuario']
    
    def get_edad(self, obj):
        if obj.fechanacimiento:
            from apps.comun.utilidades import calcular_edad
            return calcular_edad(obj.fechanacimiento)
        return None


class PacienteCrearSerializer(serializers.Serializer):
    """Serializer para crear un paciente con su usuario."""
    # Datos del usuario
    nombre = serializers.CharField(max_length=255)
    apellido = serializers.CharField(max_length=255)
    correoelectronico = serializers.EmailField()
    sexo = serializers.CharField(max_length=50, required=False, allow_blank=True)
    telefono = serializers.CharField(max_length=20, required=False, allow_blank=True)
    
    # Datos del paciente
    carnetidentidad = serializers.CharField(max_length=50, required=False, allow_blank=True)
    fechanacimiento = serializers.DateField(required=False, allow_null=True)
    direccion = serializers.CharField(required=False, allow_blank=True)
    
    def create(self, validated_data):
        # Separar datos de usuario y paciente
        datos_paciente = {
            'carnetidentidad': validated_data.pop('carnetidentidad', None),
            'fechanacimiento': validated_data.pop('fechanacimiento', None),
            'direccion': validated_data.pop('direccion', None),
        }
        
        # Obtener tipo de usuario "Paciente"
        tipo_paciente = Tipodeusuario.objects.get(rol='Paciente')
        validated_data['idtipousuario'] = tipo_paciente
        
        # Crear usuario
        usuario = Usuario.objects.create(**validated_data)
        
        # Crear paciente
        paciente = Paciente.objects.create(codusuario=usuario, **datos_paciente)
        
        return paciente
    
    def to_representation(self, instance):
        """Usar PacienteSerializer para la respuesta."""
        return PacienteSerializer(instance).data


class UsuarioActualizarNotificacionesSerializer(serializers.ModelSerializer):
    """Serializer para actualizar preferencias de notificaciones."""
    
    class Meta:
        model = Usuario
        fields = ['recibir_notificaciones', 'notificaciones_email', 'notificaciones_push']
