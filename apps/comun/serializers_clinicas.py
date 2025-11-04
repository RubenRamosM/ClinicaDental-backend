"""
Serializers para gestión de clínicas (SOLO TENANT PÚBLICO)
"""
from rest_framework import serializers
from .models import Clinica, Dominio


class DominioSerializer(serializers.ModelSerializer):
    """Serializer para dominios"""
    clinica_nombre = serializers.CharField(source='tenant.nombre', read_only=True)
    
    class Meta:
        model = Dominio
        fields = ['id', 'domain', 'tenant', 'clinica_nombre', 'is_primary']
        read_only_fields = ['id']


class ClinicaSerializer(serializers.ModelSerializer):
    """Serializer para listar/ver clínicas"""
    dominios = DominioSerializer(many=True, read_only=True, source='domains')
    dominio_principal = serializers.SerializerMethodField()
    
    class Meta:
        model = Clinica
        fields = [
            'id', 'schema_name', 'nombre', 'ruc', 'direccion', 'telefono', 
            'email', 'admin_nombre', 'admin_email', 'admin_telefono',
            'plan', 'max_usuarios', 'max_pacientes', 'activa',
            'fecha_creacion', 'fecha_actualizacion', 'logo_url',
            'dominios', 'dominio_principal'
        ]
        read_only_fields = ['id', 'schema_name', 'fecha_creacion', 'fecha_actualizacion']
    
    def get_dominio_principal(self, obj):
        """Obtener el dominio principal de la clínica"""
        dominio = obj.domains.filter(is_primary=True).first()
        return dominio.domain if dominio else None


class CrearClinicaSerializer(serializers.Serializer):
    """
    Serializer para crear nueva clínica con su dominio
    """
    # Datos de la clínica
    schema_name = serializers.CharField(
        max_length=63,
        help_text="Nombre del schema (ej: clinica2, clinica3)"
    )
    nombre = serializers.CharField(max_length=200)
    ruc = serializers.CharField(max_length=20)
    direccion = serializers.CharField()
    telefono = serializers.CharField(max_length=20)
    email = serializers.EmailField()
    
    # Datos del administrador
    admin_nombre = serializers.CharField(max_length=200)
    admin_email = serializers.EmailField()
    admin_telefono = serializers.CharField(max_length=20, required=False)
    
    # Configuración del plan
    plan = serializers.ChoiceField(
        choices=['basico', 'profesional', 'empresarial'],
        default='profesional'
    )
    max_usuarios = serializers.IntegerField(default=5)
    max_pacientes = serializers.IntegerField(default=100)
    
    # Dominio
    dominio = serializers.CharField(
        max_length=253,
        help_text="Dominio de la clínica (ej: clinica2.localhost)"
    )
    logo_url = serializers.URLField(required=False, allow_blank=True)
    
    def validate_schema_name(self, value):
        """Validar que el schema_name no exista"""
        if Clinica.objects.filter(schema_name=value).exists():
            raise serializers.ValidationError(
                f"Ya existe una clínica con el schema '{value}'"
            )
        
        # Validar formato (solo letras minúsculas, números y guiones bajos)
        if not value.replace('_', '').replace('-', '').isalnum():
            raise serializers.ValidationError(
                "El schema_name solo puede contener letras, números, guiones y guiones bajos"
            )
        
        if value == 'public':
            raise serializers.ValidationError(
                "No se puede usar 'public' como schema_name"
            )
        
        return value.lower()
    
    def validate_ruc(self, value):
        """Validar que el RUC no exista"""
        if Clinica.objects.filter(ruc=value).exists():
            raise serializers.ValidationError(
                f"Ya existe una clínica con el RUC '{value}'"
            )
        return value
    
    def validate_dominio(self, value):
        """Validar que el dominio no exista"""
        if Dominio.objects.filter(domain=value).exists():
            raise serializers.ValidationError(
                f"El dominio '{value}' ya está en uso"
            )
        return value
    
    def create(self, validated_data):
        """Crear clínica con su dominio"""
        from django.core.management import call_command
        
        # Extraer dominio
        dominio = validated_data.pop('dominio')
        
        # Crear clínica
        clinica = Clinica.objects.create(**validated_data)
        
        # Crear dominio
        Dominio.objects.create(
            domain=dominio,
            tenant=clinica,
            is_primary=True
        )
        
        # Ejecutar migraciones en el nuevo schema
        try:
            call_command('migrate_schemas', schema=clinica.schema_name, verbosity=0)
        except Exception as e:
            # Si falla, eliminar la clínica creada
            clinica.delete()
            raise serializers.ValidationError(
                f"Error al crear el schema de la clínica: {str(e)}"
            )
        
        return clinica
