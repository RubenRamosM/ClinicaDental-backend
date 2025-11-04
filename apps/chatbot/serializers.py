from rest_framework import serializers
from .models import ConversacionChatbot, MensajeChatbot


class MensajeChatbotSerializer(serializers.ModelSerializer):
    class Meta:
        model = MensajeChatbot
        fields = ['id', 'tipo', 'mensaje', 'metadata', 'fecha_creacion']
        read_only_fields = ['id', 'fecha_creacion']


class ConversacionChatbotSerializer(serializers.ModelSerializer):
    mensajes = MensajeChatbotSerializer(many=True, read_only=True)
    
    class Meta:
        model = ConversacionChatbot
        fields = [
            'id', 'session_id', 'paciente', 'correo_electronico',
            'nombre', 'telefono', 'ultima_interaccion', 'contexto',
            'mensajes', 'fecha_creacion'
        ]
        read_only_fields = ['id', 'ultima_interaccion', 'fecha_creacion']


class ChatbotMensajeRequest(serializers.Serializer):
    """Serializer para mensajes entrantes del usuario."""
    session_id = serializers.CharField(max_length=100)
    mensaje = serializers.CharField()
    correo_electronico = serializers.EmailField(required=False, allow_blank=True)
    nombre = serializers.CharField(max_length=255, required=False, allow_blank=True)
    telefono = serializers.CharField(max_length=20, required=False, allow_blank=True)


class ChatbotRespuesta(serializers.Serializer):
    """Serializer para respuestas del chatbot."""
    mensaje = serializers.CharField()
    opciones = serializers.ListField(child=serializers.CharField(), required=False)
    intent = serializers.CharField(required=False)
    metadata = serializers.DictField(required=False)
