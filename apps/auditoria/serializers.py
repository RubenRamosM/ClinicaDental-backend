"""
Serializers para auditoría.
"""
from rest_framework import serializers
from .models import Bitacora


class BitacoraSerializer(serializers.ModelSerializer):
    """Serializer para bitácora (solo lectura)."""
    usuario_nombre = serializers.SerializerMethodField()
    
    class Meta:
        model = Bitacora
        fields = [
            'id', 'usuario', 'usuario_nombre', 'accion',
            'tabla_afectada', 'registro_id', 'detalles',
            'ip_address', 'user_agent', 'fecha'
        ]
        read_only_fields = [
            'id', 'usuario', 'accion', 'tabla_afectada', 
            'registro_id', 'detalles', 'ip_address', 'user_agent', 'fecha'
        ]
    
    def get_usuario_nombre(self, obj):
        if obj.usuario:
            return f"{obj.usuario.nombre} {obj.usuario.apellido}"
        return "Sistema"
