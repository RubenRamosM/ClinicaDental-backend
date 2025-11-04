"""
Serializers para autenticación.
"""
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from apps.usuarios.models import Usuario


class LoginSerializer(serializers.Serializer):
    """Serializer para login de usuarios."""
    correo = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)
    
    def validate(self, data):
        correo = data.get('correo')
        password = data.get('password')
        
        if not correo or not password:
            raise serializers.ValidationError(
                "Debe proporcionar correo y contraseña."
            )
        
        # Buscar usuario por correo en nuestro modelo Usuario
        try:
            usuario = Usuario.objects.get(correoelectronico=correo)
        except Usuario.DoesNotExist:
            raise serializers.ValidationError(
                "Credenciales inválidas. Verifique su correo y contraseña."
            )

        # Intentar autenticar contra el modelo User de Django
        # Requiere que exista un User con username == correo
        from django.contrib.auth import authenticate
        django_user = authenticate(username=correo, password=password)
        if django_user is None:
            # Autenticación fallida (usuario no existe en auth.User o contraseña incorrecta)
            raise serializers.ValidationError(
                "Credenciales inválidas. Verifique su correo y contraseña."
            )

        data['usuario'] = usuario
        data['django_user'] = django_user
        return data


class RecuperarPasswordSerializer(serializers.Serializer):
    """Serializer para solicitar recuperación de contraseña."""
    correo = serializers.EmailField(required=True)
    
    def validate_correo(self, value):
        try:
            Usuario.objects.get(correoelectronico=value)
        except Usuario.DoesNotExist:
            raise serializers.ValidationError(
                "No existe un usuario con ese correo electrónico."
            )
        return value


class CambiarPasswordSerializer(serializers.Serializer):
    """Serializer para cambiar contraseña."""
    password_actual = serializers.CharField(write_only=True, required=True)
    password_nuevo = serializers.CharField(write_only=True, required=True)
    password_confirmacion = serializers.CharField(write_only=True, required=True)
    
    def validate(self, data):
        if data['password_nuevo'] != data['password_confirmacion']:
            raise serializers.ValidationError({
                'password_confirmacion': 'Las contraseñas no coinciden.'
            })
        
        if len(data['password_nuevo']) < 8:
            raise serializers.ValidationError({
                'password_nuevo': 'La contraseña debe tener al menos 8 caracteres.'
            })
        
        return data


class TokenSerializer(serializers.Serializer):
    """Serializer para respuesta de token."""
    token = serializers.CharField()
    usuario = serializers.SerializerMethodField()
    
    def get_usuario(self, obj):
        from apps.usuarios.serializers import UsuarioDetalleSerializer
        return UsuarioDetalleSerializer(obj['usuario']).data


class ActualizarPerfilSerializer(serializers.Serializer):
    """Serializer para actualizar perfil de usuario."""
    nombre = serializers.CharField(max_length=100, required=False)
    apellido = serializers.CharField(max_length=100, required=False)
    telefono = serializers.CharField(max_length=20, required=False)
    notificaciones_email = serializers.BooleanField(required=False)
    notificaciones_push = serializers.BooleanField(required=False)
    
    # Campos específicos para pacientes
    direccion = serializers.CharField(max_length=255, required=False, allow_blank=True)
    
    def validate_telefono(self, value):
        """Validar formato de teléfono."""
        if value and len(value) < 7:
            raise serializers.ValidationError("El teléfono debe tener al menos 7 dígitos.")
        return value


class RegistroSerializer(serializers.Serializer):
    """Serializer para registro de nuevos usuarios."""
    # Campos básicos (obligatorios para todos)
    nombre = serializers.CharField(max_length=255, required=True)
    apellido = serializers.CharField(max_length=255, required=True)
    correo = serializers.EmailField(required=True)
    telefono = serializers.CharField(max_length=20, required=True)
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    password_confirmacion = serializers.CharField(write_only=True, required=True)
    tipo_usuario = serializers.CharField(required=True)
    
    # Campos opcionales generales
    sexo = serializers.CharField(max_length=50, required=False, allow_blank=True)
    
    # Campos específicos para pacientes (opcionales, pero recomendados)
    carnet = serializers.CharField(max_length=50, required=False, allow_blank=True)
    fecha_nacimiento = serializers.DateField(required=False, allow_null=True)
    direccion = serializers.CharField(max_length=255, required=False, allow_blank=True)
    
    def validate_correo(self, value):
        """Validar que el correo no exista."""
        if Usuario.objects.filter(correoelectronico=value).exists():
            raise serializers.ValidationError(
                "Ya existe un usuario registrado con este correo electrónico."
            )
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                "Ya existe un usuario registrado con este correo electrónico."
            )
        return value
    
    def validate_carnet(self, value):
        """Validar que el carnet no exista (si se proporciona)."""
        if value and value.strip():
            from apps.usuarios.models import Paciente
            if Paciente.objects.filter(carnetidentidad=value).exists():
                raise serializers.ValidationError(
                    "Ya existe un paciente registrado con este número de carnet."
                )
        return value
    
    def validate_tipo_usuario(self, value):
        """Validar que el tipo de usuario exista."""
        from apps.usuarios.models import Tipodeusuario
        try:
            # Buscar por rol (nombre del tipo)
            tipo = Tipodeusuario.objects.get(rol__iexact=value)
            return tipo.rol
        except Tipodeusuario.DoesNotExist:
            raise serializers.ValidationError(
                f"El tipo de usuario '{value}' no existe. Tipos válidos: Paciente, Odontólogo, Administrador."
            )
    
    def validate_telefono(self, value):
        """Validar formato de teléfono."""
        if len(value) < 7:
            raise serializers.ValidationError(
                "El teléfono debe tener al menos 7 dígitos."
            )
        return value
    
    def validate(self, data):
        """Validaciones generales."""
        # Validar que las contraseñas coincidan
        if data['password'] != data['password_confirmacion']:
            raise serializers.ValidationError({
                'password_confirmacion': 'Las contraseñas no coinciden.'
            })
        
        # Si es paciente, validar que se proporcionen datos adicionales
        if data['tipo_usuario'].lower() == 'paciente':
            # Advertencia: estos campos son opcionales pero recomendados
            # No los hacemos obligatorios para permitir registro rápido
            pass
        
        return data
