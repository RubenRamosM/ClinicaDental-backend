from django.contrib import admin
from .models import ConversacionChatbot, MensajeChatbot


@admin.register(ConversacionChatbot)
class ConversacionChatbotAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'nombre', 'correo_electronico', 'paciente', 'ultima_interaccion']
    list_filter = ['ultima_interaccion', 'fecha_creacion']
    search_fields = ['session_id', 'nombre', 'correo_electronico']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion', 'ultima_interaccion']


@admin.register(MensajeChatbot)
class MensajeChatbotAdmin(admin.ModelAdmin):
    list_display = ['conversacion', 'tipo', 'mensaje_truncado', 'fecha_creacion']
    list_filter = ['tipo', 'fecha_creacion']
    search_fields = ['mensaje', 'conversacion__session_id']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    
    def mensaje_truncado(self, obj):
        return obj.mensaje[:50] + '...' if len(obj.mensaje) > 50 else obj.mensaje
    mensaje_truncado.short_description = 'Mensaje'
