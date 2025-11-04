"""
Serializadores para la API de respaldos.
"""
from rest_framework import serializers
from .models import Respaldo


class RespaldoSerializer(serializers.ModelSerializer):
    """Serializador básico para listar respaldos."""
    
    tamaño_mb = serializers.SerializerMethodField()
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    tipo_respaldo_display = serializers.CharField(source='get_tipo_respaldo_display', read_only=True)
    puede_restaurar = serializers.SerializerMethodField()
    
    class Meta:
        model = Respaldo
        fields = [
            'id',
            'clinica_id',
            'fecha_respaldo',
            'tamaño_bytes',
            'tamaño_mb',
            'numero_registros',
            'estado',
            'estado_display',
            'tipo_respaldo',
            'tipo_respaldo_display',
            'descripcion',
            'usuario',
            'fecha_creacion',
            'puede_restaurar',
        ]
        read_only_fields = fields
    
    def get_tamaño_mb(self, obj):
        """Convertir tamaño a MB."""
        return round(obj.tamaño_bytes / (1024 * 1024), 2) if obj.tamaño_bytes else 0
    
    def get_puede_restaurar(self, obj):
        """Verificar si el respaldo puede ser restaurado."""
        return obj.puede_restaurarse()


class RespaldoDetailSerializer(serializers.ModelSerializer):
    """Serializador detallado para ver un respaldo específico."""
    
    tamaño_mb = serializers.SerializerMethodField()
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    tipo_respaldo_display = serializers.CharField(source='get_tipo_respaldo_display', read_only=True)
    puede_restaurar = serializers.SerializerMethodField()
    tiempo_ejecucion_segundos = serializers.SerializerMethodField()
    usuario_nombre = serializers.SerializerMethodField()
    
    class Meta:
        model = Respaldo
        fields = [
            'id',
            'clinica_id',
            'archivo_s3',
            'fecha_respaldo',
            'tamaño_bytes',
            'tamaño_mb',
            'hash_md5',
            'numero_registros',
            'tiempo_ejecucion',
            'tiempo_ejecucion_segundos',
            'estado',
            'estado_display',
            'tipo_respaldo',
            'tipo_respaldo_display',
            'descripcion',
            'metadata',
            'usuario',
            'usuario_nombre',
            'fecha_creacion',
            'fecha_actualizacion',
            'puede_restaurar',
        ]
        read_only_fields = fields
    
    def get_tamaño_mb(self, obj):
        """Convertir tamaño a MB."""
        return round(obj.tamaño_bytes / (1024 * 1024), 2) if obj.tamaño_bytes else 0
    
    def get_puede_restaurar(self, obj):
        """Verificar si el respaldo puede ser restaurado."""
        return obj.puede_restaurarse()
    
    def get_tiempo_ejecucion_segundos(self, obj):
        """Convertir duración a segundos."""
        return obj.tiempo_ejecucion.total_seconds() if obj.tiempo_ejecucion else 0
    
    def get_usuario_nombre(self, obj):
        """Obtener nombre del usuario que creó el respaldo."""
        if obj.usuario:
            return f"{obj.usuario.nombre} {obj.usuario.apellido}"
        return None


class CrearRespaldoSerializer(serializers.Serializer):
    """Serializador para crear respaldos manuales desde la API."""
    
    descripcion = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Descripción opcional del respaldo"
    )
    
    def create(self, validated_data):
        """Crear respaldo usando el servicio."""
        from .services import BackupService
        
        # Obtener clinica_id del contexto (usuario autenticado)
        usuario = self.context['request'].user
        clinica_id = usuario.clinica_id
        
        backup_service = BackupService()
        respaldo = backup_service.crear_respaldo(
            clinica_id=clinica_id,
            tipo='por_demanda',
            usuario=usuario,
            descripcion=validated_data.get('descripcion', '')
        )
        
        return respaldo
