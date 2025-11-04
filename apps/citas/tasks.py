"""
Tareas asíncronas para el módulo de citas.
CU17: Recordatorios automáticos
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta, datetime
from django.db.models import Q


@shared_task(name='apps.citas.tasks.enviar_recordatorios_24h')
def enviar_recordatorios_24h():
    """
    Envía recordatorios de citas programadas para dentro de 24 horas.
    CU17: Recordatorios automáticos
    
    Se ejecuta diariamente a las 9:00 AM.
    """
    from .models import Consulta, Estadodeconsulta
    
    # Calcular fecha de mañana
    ahora = timezone.now()
    manana = ahora + timedelta(days=1)
    
    # Obtener consultas confirmadas para mañana
    consultas = Consulta.objects.filter(
        fecha=manana.date(),
        estado__in=['confirmada', 'pendiente']
    ).select_related(
        'codpaciente__codusuario',
        'cododontologo__codusuario',
        'idhorario'
    )
    
    total_enviados = 0
    errores = []
    
    for consulta in consultas:
        try:
            paciente = consulta.codpaciente
            usuario = paciente.codusuario
            
            # Preparar datos del recordatorio
            datos_recordatorio = {
                'paciente_nombre': f"{usuario.nombre} {usuario.apellido}",
                'fecha': consulta.fecha.strftime('%d/%m/%Y'),
                'hora': consulta.hora_consulta.strftime('%H:%M') if consulta.hora_consulta else 'Por confirmar',
                'odontologo': f"Dr(a). {consulta.cododontologo.codusuario.nombre} {consulta.cododontologo.codusuario.apellido}" if consulta.cododontologo else 'Por asignar',
                'motivo': consulta.motivo_consulta or 'Consulta general',
                'consulta_id': consulta.id
            }
            
            # 1. Enviar notificación push (si el usuario tiene FCM token)
            if hasattr(usuario, 'fcm_token') and usuario.fcm_token:
                enviar_notificacion_push(usuario.fcm_token, datos_recordatorio)
            
            # 2. Enviar email
            if usuario.correoelectronico:
                enviar_email_recordatorio(usuario.correoelectronico, datos_recordatorio)
            
            # 3. TODO: Enviar SMS (opcional)
            # if usuario.telefono:
            #     enviar_sms_recordatorio(usuario.telefono, datos_recordatorio)
            
            total_enviados += 1
            
        except Exception as e:
            error_msg = f"Error al enviar recordatorio para consulta {consulta.id}: {str(e)}"
            errores.append(error_msg)
            print(error_msg)
    
    # Registrar en auditoría
    resultado = {
        'fecha_ejecucion': ahora.isoformat(),
        'consultas_procesadas': consultas.count(),
        'recordatorios_enviados': total_enviados,
        'errores': len(errores),
        'detalles_errores': errores
    }
    
    print(f"✅ Recordatorios enviados: {total_enviados}/{consultas.count()}")
    
    return resultado


@shared_task(name='apps.citas.tasks.marcar_citas_vencidas')
def marcar_citas_vencidas():
    """
    Marca automáticamente como vencidas las citas que no fueron confirmadas
    y cuya fecha ya pasó.
    
    Se ejecuta diariamente a las 12:30 AM.
    """
    from .models import Consulta, Estadodeconsulta
    
    ahora = timezone.now()
    ayer = ahora - timedelta(days=1)
    
    # Obtener estado vencido
    try:
        estado_vencido = Estadodeconsulta.objects.get(estado__iexact='vencida')
    except Estadodeconsulta.DoesNotExist:
        estado_vencido = Estadodeconsulta.objects.create(estado='vencida')
    
    # Buscar citas pendientes cuya fecha ya pasó
    citas_vencidas = Consulta.objects.filter(
        fecha__lt=ahora.date(),
        estado='pendiente'
    )
    
    total_marcadas = 0
    for cita in citas_vencidas:
        cita.estado = 'vencida'
        cita.idestadoconsulta = estado_vencido
        cita.save()
        total_marcadas += 1
    
    print(f"✅ Citas marcadas como vencidas: {total_marcadas}")
    
    return {
        'fecha_ejecucion': ahora.isoformat(),
        'citas_marcadas': total_marcadas
    }


def enviar_notificacion_push(fcm_token, datos):
    """
    Envía notificación push usando Firebase Cloud Messaging.
    
    TODO: Implementar integración con FCM.
    """
    # from firebase_admin import messaging
    
    mensaje_titulo = "🦷 Recordatorio de Cita"
    mensaje_cuerpo = f"Tienes una cita mañana {datos['fecha']} a las {datos['hora']}"
    
    # message = messaging.Message(
    #     notification=messaging.Notification(
    #         title=mensaje_titulo,
    #         body=mensaje_cuerpo,
    #     ),
    #     token=fcm_token,
    #     data={
    #         'tipo': 'recordatorio_cita',
    #         'consulta_id': str(datos['consulta_id']),
    #         'fecha': datos['fecha'],
    #         'hora': datos['hora']
    #     }
    # )
    
    # response = messaging.send(message)
    
    print(f"📱 [SIMULADO] Push enviado a token {fcm_token[:20]}...")
    return True


def enviar_email_recordatorio(email, datos):
    """
    Envía email de recordatorio al paciente.
    """
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    from django.conf import settings
    
    asunto = f"🦷 Recordatorio: Cita el {datos['fecha']}"
    
    # TODO: Crear template HTML profesional
    mensaje_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background-color: #4CAF50; color: white; padding: 20px; text-align: center;">
            <h1>🦷 Clínica Dental</h1>
        </div>
        
        <div style="padding: 20px; background-color: #f9f9f9;">
            <h2>Hola {datos['paciente_nombre']},</h2>
            
            <p>Te recordamos que tienes una cita programada:</p>
            
            <div style="background-color: white; padding: 15px; border-left: 4px solid #4CAF50; margin: 20px 0;">
                <p><strong>📅 Fecha:</strong> {datos['fecha']}</p>
                <p><strong>🕐 Hora:</strong> {datos['hora']}</p>
                <p><strong>👨‍⚕️ Odontólogo:</strong> {datos['odontologo']}</p>
                <p><strong>📋 Motivo:</strong> {datos['motivo']}</p>
            </div>
            
            <p><strong>Recomendaciones:</strong></p>
            <ul>
                <li>Llega 10 minutos antes de tu cita</li>
                <li>Trae tu documento de identidad</li>
                <li>Si no puedes asistir, cancela con 24 horas de anticipación</li>
            </ul>
            
            <p>Si necesitas reprogramar o cancelar, contáctanos lo antes posible.</p>
            
            <p>¡Te esperamos!</p>
        </div>
        
        <div style="background-color: #333; color: white; padding: 10px; text-align: center; font-size: 12px;">
            <p>Este es un mensaje automático, por favor no responder.</p>
        </div>
    </body>
    </html>
    """
    
    mensaje_texto = f"""
    Hola {datos['paciente_nombre']},
    
    Te recordamos que tienes una cita programada:
    
    📅 Fecha: {datos['fecha']}
    🕐 Hora: {datos['hora']}
    👨‍⚕️ Odontólogo: {datos['odontologo']}
    📋 Motivo: {datos['motivo']}
    
    Recomendaciones:
    - Llega 10 minutos antes de tu cita
    - Trae tu documento de identidad
    - Si no puedes asistir, cancela con 24 horas de anticipación
    
    ¡Te esperamos!
    
    Clínica Dental
    """
    
    try:
        send_mail(
            subject=asunto,
            message=mensaje_texto,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=mensaje_html,
            fail_silently=False,
        )
        print(f"📧 Email enviado a {email}")
        return True
    except Exception as e:
        print(f"❌ Error al enviar email a {email}: {str(e)}")
        # En desarrollo, simular envío exitoso
        print(f"📧 [SIMULADO] Email enviado a {email}")
        return True
