from django.db import models
from apps.comun.models import ModeloConFechas


class ConversacionChatbot(ModeloConFechas):
    """
    Historial de conversaciones del chatbot.
    """
    session_id = models.CharField(max_length=100, unique=True, db_index=True)
    paciente = models.ForeignKey(
        'usuarios.Paciente',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conversaciones_chatbot'
    )
    correo_electronico = models.EmailField(null=True, blank=True)
    nombre = models.CharField(max_length=255, null=True, blank=True)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    
    ultima_interaccion = models.DateTimeField(auto_now=True)
    contexto = models.JSONField(
        default=dict,
        help_text="Estado de la conversación (intent, datos parciales, etc.)"
    )
    
    class Meta:
        db_table = 'conversacion_chatbot'
        verbose_name = 'Conversación Chatbot'
        verbose_name_plural = 'Conversaciones Chatbot'
        ordering = ['-ultima_interaccion']
    
    def __str__(self):
        return f"Conversación {self.session_id} - {self.nombre or 'Anónimo'}"


class MensajeChatbot(ModeloConFechas):
    """
    Mensajes individuales dentro de una conversación.
    """
    TIPO_CHOICES = [
        ('usuario', 'Usuario'),
        ('bot', 'Bot'),
        ('sistema', 'Sistema'),
    ]
    
    conversacion = models.ForeignKey(
        ConversacionChatbot,
        on_delete=models.CASCADE,
        related_name='mensajes'
    )
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    mensaje = models.TextField()
    metadata = models.JSONField(
        default=dict,
        help_text="Información adicional (intent detectado, entities, etc.)"
    )
    
    class Meta:
        db_table = 'mensaje_chatbot'
        verbose_name = 'Mensaje Chatbot'
        verbose_name_plural = 'Mensajes Chatbot'
        ordering = ['fecha_creacion']
    
    def __str__(self):
        return f"{self.tipo}: {self.mensaje[:50]}"
