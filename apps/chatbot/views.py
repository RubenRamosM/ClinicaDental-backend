"""
Views del chatbot.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.utils import timezone

from .models import ConversacionChatbot, MensajeChatbot
from .serializers import (
    ConversacionChatbotSerializer,
    MensajeChatbotSerializer,
    ChatbotMensajeRequest,
    ChatbotRespuesta
)
from .bot_engine import ChatbotEngine
from apps.usuarios.models import Paciente, Usuario


class ChatbotViewSet(viewsets.ViewSet):
    """
    ViewSet para interacciones con el chatbot.
    """
    permission_classes = [AllowAny]  # Permitir acceso sin autenticación
    
    @action(detail=False, methods=['post'])
    def mensaje(self, request):
        """
        Procesar mensaje del usuario y generar respuesta del bot.
        
        Body:
        {
            "session_id": "unique-session-id",
            "mensaje": "Hola, quiero ver mis citas",
            "correo_electronico": "paciente@example.com",  // opcional
            "nombre": "Juan Pérez",  // opcional
            "telefono": "77777777"  // opcional
        }
        """
        serializer = ChatbotMensajeRequest(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        session_id = serializer.validated_data['session_id']
        mensaje_usuario = serializer.validated_data['mensaje']
        correo = serializer.validated_data.get('correo_electronico')
        nombre = serializer.validated_data.get('nombre')
        telefono = serializer.validated_data.get('telefono')
        
        # Obtener o crear conversación
        conversacion, created = ConversacionChatbot.objects.get_or_create(
            session_id=session_id,
            defaults={
                'correo_electronico': correo,
                'nombre': nombre,
                'telefono': telefono
            }
        )
        
        # Actualizar datos si se proporcionan
        if correo and not conversacion.correo_electronico:
            conversacion.correo_electronico = correo
        if nombre and not conversacion.nombre:
            conversacion.nombre = nombre
        if telefono and not conversacion.telefono:
            conversacion.telefono = telefono
        
        # Intentar vincular con paciente si hay correo
        if conversacion.correo_electronico and not conversacion.paciente:
            try:
                usuario = Usuario.objects.get(correoelectronico=conversacion.correo_electronico)
                paciente = Paciente.objects.get(codusuario=usuario)
                conversacion.paciente = paciente
            except (Usuario.DoesNotExist, Paciente.DoesNotExist):
                pass
        
        conversacion.save()
        
        # Guardar mensaje del usuario
        MensajeChatbot.objects.create(
            conversacion=conversacion,
            tipo='usuario',
            mensaje=mensaje_usuario
        )
        
        # Procesar con el motor del bot
        engine = ChatbotEngine(conversacion)
        respuesta_data = engine.procesar_mensaje(mensaje_usuario)
        
        # Guardar respuesta del bot
        MensajeChatbot.objects.create(
            conversacion=conversacion,
            tipo='bot',
            mensaje=respuesta_data['mensaje'],
            metadata={
                'intent': respuesta_data.get('intent'),
                'opciones': respuesta_data.get('opciones', []),
                'metadata': respuesta_data.get('metadata', {})
            }
        )
        
        # Serializar respuesta
        respuesta_serializer = ChatbotRespuesta(data=respuesta_data)
        respuesta_serializer.is_valid(raise_exception=True)
        
        return Response(respuesta_serializer.data)
    
    @action(detail=False, methods=['get'])
    def historial(self, request):
        """
        Obtener historial de conversación.
        Query params: session_id
        """
        session_id = request.query_params.get('session_id')
        
        if not session_id:
            return Response(
                {'error': 'Debe proporcionar session_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            conversacion = ConversacionChatbot.objects.get(session_id=session_id)
            serializer = ConversacionChatbotSerializer(conversacion)
            return Response(serializer.data)
        except ConversacionChatbot.DoesNotExist:
            return Response(
                {'error': 'Conversación no encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['post'])
    def reset(self, request):
        """
        Reiniciar conversación (limpiar contexto).
        Body: { "session_id": "..." }
        """
        session_id = request.data.get('session_id')
        
        if not session_id:
            return Response(
                {'error': 'Debe proporcionar session_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            conversacion = ConversacionChatbot.objects.get(session_id=session_id)
            conversacion.contexto = {}
            conversacion.save()
            
            return Response({'mensaje': 'Conversación reiniciada'})
        except ConversacionChatbot.DoesNotExist:
            return Response(
                {'error': 'Conversación no encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )
