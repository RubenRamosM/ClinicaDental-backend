"""
Motor del chatbot - Procesamiento de intents y generación de respuestas.
"""
from datetime import datetime, timedelta
from django.db.models import Q
from apps.citas.models import Consulta, Horario, Tipodeconsulta
from apps.usuarios.models import Paciente
from apps.profesionales.models import Odontologo
import re


class ChatbotEngine:
    """
    Motor simple de procesamiento de mensajes del chatbot.
    """
    
    # Palabras clave para detectar intents
    INTENTS = {
        'saludo': ['hola', 'buenos días', 'buenas tardes', 'buenas noches', 'hey', 'saludos'],
        'ver_citas': ['ver citas', 'mis citas', 'citas', 'consultas', 'ver consultas', 'mis consultas'],
        'reservar_cita': ['reservar', 'agendar', 'crear cita', 'nueva cita', 'quiero cita', 'necesito cita'],
        'cancelar_cita': ['cancelar', 'eliminar cita', 'borrar cita'],
        'horarios_disponibles': ['horarios', 'disponibilidad', 'horarios disponibles', 'cuándo hay'],
        'ayuda': ['ayuda', 'help', 'qué puedes hacer', 'opciones'],
        'despedida': ['adiós', 'chao', 'hasta luego', 'gracias', 'bye'],
    }
    
    def __init__(self, conversacion):
        """
        Inicializar con el contexto de la conversación.
        """
        self.conversacion = conversacion
        self.contexto = conversacion.contexto
    
    def procesar_mensaje(self, mensaje):
        """
        Procesar mensaje del usuario y generar respuesta.
        
        Returns:
            dict: {
                'mensaje': str,
                'opciones': list (opcional),
                'intent': str,
                'metadata': dict
            }
        """
        mensaje_lower = mensaje.lower().strip()
        
        # Detectar intent
        intent = self._detectar_intent(mensaje_lower)
        
        # Procesar según intent
        if intent == 'saludo':
            return self._responder_saludo()
        
        elif intent == 'ver_citas':
            return self._ver_citas_paciente()
        
        elif intent == 'reservar_cita':
            return self._iniciar_reserva_cita(mensaje)
        
        elif intent == 'horarios_disponibles':
            return self._mostrar_horarios_disponibles(mensaje)
        
        elif intent == 'cancelar_cita':
            return self._iniciar_cancelar_cita()
        
        elif intent == 'ayuda':
            return self._mostrar_ayuda()
        
        elif intent == 'despedida':
            return self._responder_despedida()
        
        # Manejar flujos multi-paso según contexto
        if self.contexto.get('estado') == 'esperando_fecha':
            return self._procesar_fecha(mensaje)
        
        elif self.contexto.get('estado') == 'esperando_horario':
            return self._procesar_horario(mensaje)
        
        elif self.contexto.get('estado') == 'esperando_tipo_consulta':
            return self._procesar_tipo_consulta(mensaje)
        
        elif self.contexto.get('estado') == 'esperando_confirmacion':
            return self._procesar_confirmacion(mensaje)
        
        elif self.contexto.get('estado') == 'esperando_cita_cancelar':
            return self._procesar_cancelacion(mensaje)
        
        # No entendido
        return {
            'mensaje': '🤔 No entendí tu mensaje. Escribe "ayuda" para ver qué puedo hacer.',
            'intent': 'no_entendido',
            'opciones': ['Ver mis citas', 'Reservar cita', 'Ayuda'],
            'metadata': {}
        }
    
    def _detectar_intent(self, mensaje):
        """
        Detectar intención del usuario basado en palabras clave.
        """
        for intent, keywords in self.INTENTS.items():
            for keyword in keywords:
                if keyword in mensaje:
                    return intent
        return 'no_entendido'
    
    def _responder_saludo(self):
        """Respuesta a saludo inicial."""
        nombre = self.conversacion.nombre or 'amigo/a'
        return {
            'mensaje': f'¡Hola {nombre}! 👋 Soy el asistente virtual de la Clínica Dental. ¿En qué puedo ayudarte?',
            'intent': 'saludo',
            'opciones': ['Ver mis citas', 'Reservar una cita', 'Horarios disponibles', 'Ayuda'],
            'metadata': {}
        }
    
    def _ver_citas_paciente(self):
        """Mostrar citas del paciente."""
        if not self.conversacion.paciente:
            return {
                'mensaje': '⚠️ Necesito tu correo electrónico para ver tus citas. Por favor, proporciona tu correo.',
                'intent': 'ver_citas',
                'metadata': {'requiere_autenticacion': True}
            }
        
        # Obtener citas futuras y recientes
        hoy = datetime.now().date()
        citas = Consulta.objects.filter(
            codpaciente=self.conversacion.paciente
        ).filter(
            Q(fecha__gte=hoy) | Q(fecha__gte=hoy - timedelta(days=30))
        ).order_by('fecha', 'idhorario__hora')[:5]
        
        if not citas.exists():
            return {
                'mensaje': '📅 No tienes citas registradas.\n\n¿Te gustaría reservar una cita?',
                'intent': 'ver_citas',
                'opciones': ['Sí, reservar cita', 'No, gracias'],
                'metadata': {'tiene_citas': False}
            }
        
        # Formatear lista de citas
        mensaje = '📋 **Tus citas:**\n\n'
        for i, cita in enumerate(citas, 1):
            estado_emoji = {
                'pendiente': '⏳',
                'confirmada': '✅',
                'cancelada': '❌',
                'completada': '✔️'
            }.get(cita.estado, '📌')
            
            mensaje += f"{i}. {estado_emoji} {cita.fecha.strftime('%d/%m/%Y')} - {cita.idhorario.hora.strftime('%H:%M')}\n"
            mensaje += f"   Tipo: {cita.idtipoconsulta.nombreconsulta}\n"
            mensaje += f"   Estado: {cita.get_estado_display()}\n\n"
        
        return {
            'mensaje': mensaje,
            'intent': 'ver_citas',
            'opciones': ['Reservar otra cita', 'Cancelar una cita'],
            'metadata': {'cantidad_citas': citas.count()}
        }
    
    def _iniciar_reserva_cita(self, mensaje):
        """Iniciar flujo de reserva de cita."""
        # Limpiar contexto previo
        self.contexto = {
            'estado': 'esperando_fecha',
            'datos_cita': {}
        }
        self.conversacion.contexto = self.contexto
        self.conversacion.save()
        
        return {
            'mensaje': '📅 Perfecto, vamos a reservar tu cita.\n\n¿Para qué fecha te gustaría? (formato: DD/MM/YYYY o "mañana", "pasado mañana")',
            'intent': 'reservar_cita',
            'metadata': {'paso': 1, 'total_pasos': 3}
        }
    
    def _procesar_fecha(self, mensaje):
        """Procesar fecha proporcionada por el usuario."""
        fecha = self._parsear_fecha(mensaje)
        
        if not fecha:
            return {
                'mensaje': '⚠️ No pude entender la fecha. Por favor ingresa en formato DD/MM/YYYY o palabras como "mañana".',
                'intent': 'reservar_cita',
                'metadata': {'error': 'fecha_invalida'}
            }
        
        # Validar que sea fecha futura
        if fecha < datetime.now().date():
            return {
                'mensaje': '⚠️ La fecha debe ser futura. ¿Qué fecha te gustaría?',
                'intent': 'reservar_cita',
                'metadata': {'error': 'fecha_pasada'}
            }
        
        # Guardar en contexto
        self.contexto['datos_cita']['fecha'] = fecha.isoformat()
        
        # Obtener horarios disponibles
        horarios = self._obtener_horarios_disponibles(fecha)
        
        if not horarios:
            return {
                'mensaje': f'😔 No hay horarios disponibles para {fecha.strftime("%d/%m/%Y")}.\n\n¿Te gustaría otra fecha?',
                'intent': 'reservar_cita',
                'metadata': {'horarios_disponibles': 0}
            }
        
        # Mostrar horarios
        mensaje = f'✅ Fecha: {fecha.strftime("%d/%m/%Y")}\n\n'
        mensaje += '🕐 **Horarios disponibles:**\n\n'
        for i, horario in enumerate(horarios[:8], 1):  # Máximo 8 horarios
            mensaje += f"{i}. {horario.hora.strftime('%H:%M')}\n"
        
        mensaje += '\n¿Qué horario prefieres? (escribe el número)'
        
        # Actualizar estado
        self.contexto['estado'] = 'esperando_horario'
        self.contexto['horarios_disponibles'] = [h.id for h in horarios]
        self.conversacion.contexto = self.contexto
        self.conversacion.save()
        
        return {
            'mensaje': mensaje,
            'intent': 'reservar_cita',
            'metadata': {'paso': 2, 'total_pasos': 3, 'horarios_count': len(horarios)}
        }
    
    def _procesar_horario(self, mensaje):
        """Procesar selección de horario."""
        try:
            seleccion = int(mensaje.strip())
            horarios_ids = self.contexto.get('horarios_disponibles', [])
            
            if seleccion < 1 or seleccion > len(horarios_ids):
                raise ValueError()
            
            horario_id = horarios_ids[seleccion - 1]
            horario = Horario.objects.get(id=horario_id)
            
            # Guardar en contexto
            self.contexto['datos_cita']['horario_id'] = horario_id
            
            # Mostrar tipos de consulta
            tipos = Tipodeconsulta.objects.filter(permite_agendamiento_web=True)
            
            if not tipos.exists():
                # Si no hay tipos permitidos, usar tipos genéricos
                tipos = Tipodeconsulta.objects.all()[:5]
            
            mensaje = f'✅ Horario seleccionado: {horario.hora.strftime("%H:%M")}\n\n'
            mensaje += '🦷 **Tipo de consulta:**\n\n'
            
            for i, tipo in enumerate(tipos, 1):
                mensaje += f"{i}. {tipo.nombreconsulta}\n"
            
            mensaje += '\n¿Qué tipo de consulta necesitas? (escribe el número)'
            
            # Actualizar estado
            self.contexto['estado'] = 'esperando_tipo_consulta'
            self.contexto['tipos_disponibles'] = [t.id for t in tipos]
            self.conversacion.contexto = self.contexto
            self.conversacion.save()
            
            return {
                'mensaje': mensaje,
                'intent': 'reservar_cita',
                'metadata': {'paso': 3, 'total_pasos': 4}
            }
            
        except (ValueError, Horario.DoesNotExist):
            return {
                'mensaje': '⚠️ Selección inválida. Por favor escribe el número del horario.',
                'intent': 'reservar_cita',
                'metadata': {'error': 'seleccion_invalida'}
            }
    
    def _procesar_tipo_consulta(self, mensaje):
        """Procesar selección de tipo de consulta."""
        try:
            seleccion = int(mensaje.strip())
            tipos_ids = self.contexto.get('tipos_disponibles', [])
            
            if seleccion < 1 or seleccion > len(tipos_ids):
                raise ValueError()
            
            tipo_id = tipos_ids[seleccion - 1]
            tipo = Tipodeconsulta.objects.get(id=tipo_id)
            
            # Guardar en contexto
            self.contexto['datos_cita']['tipo_consulta_id'] = tipo_id
            
            # Resumen para confirmación
            datos = self.contexto['datos_cita']
            fecha = datetime.fromisoformat(datos['fecha'])
            horario = Horario.objects.get(id=datos['horario_id'])
            
            mensaje = '📋 **Resumen de tu cita:**\n\n'
            mensaje += f"📅 Fecha: {fecha.strftime('%d/%m/%Y')}\n"
            mensaje += f"🕐 Hora: {horario.hora.strftime('%H:%M')}\n"
            mensaje += f"🦷 Tipo: {tipo.nombreconsulta}\n\n"
            mensaje += '¿Confirmas la cita? (escribe "sí" o "no")'
            
            # Actualizar estado
            self.contexto['estado'] = 'esperando_confirmacion'
            self.conversacion.contexto = self.contexto
            self.conversacion.save()
            
            return {
                'mensaje': mensaje,
                'intent': 'reservar_cita',
                'opciones': ['Sí', 'No'],
                'metadata': {'paso': 4, 'total_pasos': 4}
            }
            
        except (ValueError, Tipodeconsulta.DoesNotExist, Horario.DoesNotExist):
            return {
                'mensaje': '⚠️ Selección inválida. Por favor escribe el número del tipo de consulta.',
                'intent': 'reservar_cita',
                'metadata': {'error': 'seleccion_invalida'}
            }
    
    def _procesar_confirmacion(self, mensaje):
        """Procesar confirmación final y crear la cita."""
        confirmacion = mensaje.lower().strip()
        
        if confirmacion in ['sí', 'si', 'confirmar', 'ok', 's', 'yes']:
            # Crear la cita
            resultado = self._crear_cita_definitiva()
            
            if resultado['success']:
                # Limpiar contexto
                self.contexto = {}
                self.conversacion.contexto = self.contexto
                self.conversacion.save()
                
                return {
                    'mensaje': f"✅ ¡Cita reservada exitosamente!\n\n{resultado['mensaje']}\n\n¿Hay algo más en que pueda ayudarte?",
                    'intent': 'reservar_cita',
                    'opciones': ['Ver mis citas', 'Reservar otra cita', 'No, gracias'],
                    'metadata': {'cita_id': resultado['cita_id']}
                }
            else:
                return {
                    'mensaje': f"❌ Error al crear la cita: {resultado['error']}\n\n¿Deseas intentar nuevamente?",
                    'intent': 'reservar_cita',
                    'opciones': ['Sí, intentar de nuevo', 'No'],
                    'metadata': {'error': resultado['error']}
                }
        else:
            # Cancelar reserva
            self.contexto = {}
            self.conversacion.contexto = self.contexto
            self.conversacion.save()
            
            return {
                'mensaje': 'Reserva cancelada. ¿Hay algo más en que pueda ayudarte?',
                'intent': 'reservar_cita',
                'opciones': ['Ver mis citas', 'Reservar cita', 'Ayuda'],
                'metadata': {}
            }
    
    def _crear_cita_definitiva(self):
        """Crear la cita en la base de datos."""
        try:
            datos = self.contexto.get('datos_cita', {})
            
            # Validar datos completos
            if not all([datos.get('fecha'), datos.get('horario_id'), datos.get('tipo_consulta_id')]):
                return {'success': False, 'error': 'Datos incompletos'}
            
            # Validar paciente
            if not self.conversacion.paciente:
                return {'success': False, 'error': 'Paciente no identificado'}
            
            # Obtener objetos
            from apps.citas.models import Estadodeconsulta
            fecha = datetime.fromisoformat(datos['fecha']).date()
            horario = Horario.objects.get(id=datos['horario_id'])
            tipo = Tipodeconsulta.objects.get(id=datos['tipo_consulta_id'])
            estado_pendiente = Estadodeconsulta.objects.get(estado='Pendiente')
            
            # Verificar disponibilidad nuevamente
            existe = Consulta.objects.filter(
                fecha=fecha,
                idhorario=horario
            ).exists()
            
            if existe:
                return {'success': False, 'error': 'El horario ya fue reservado'}
            
            # Crear consulta
            consulta = Consulta.objects.create(
                fecha=fecha,
                codpaciente=self.conversacion.paciente,
                idhorario=horario,
                idtipoconsulta=tipo,
                idestadoconsulta=estado_pendiente,
                estado='pendiente',
                motivo_consulta=datos.get('motivo', 'Agendado via chatbot'),
                tipo_consulta='primera_vez'
            )
            
            mensaje = f"📅 Fecha: {fecha.strftime('%d/%m/%Y')}\n"
            mensaje += f"🕐 Hora: {horario.hora.strftime('%H:%M')}\n"
            mensaje += f"🦷 Tipo: {tipo.nombreconsulta}\n"
            mensaje += f"📋 ID: #{consulta.id}"
            
            return {
                'success': True,
                'cita_id': consulta.id,
                'mensaje': mensaje
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _mostrar_horarios_disponibles(self, mensaje):
        """Mostrar horarios disponibles para hoy o mañana."""
        # Intentar parsear fecha del mensaje, sino usar mañana
        fecha = self._parsear_fecha(mensaje)
        if not fecha or fecha < datetime.now().date():
            fecha = datetime.now().date() + timedelta(days=1)
        
        horarios = self._obtener_horarios_disponibles(fecha)
        
        if not horarios:
            return {
                'mensaje': f'😔 No hay horarios disponibles para {fecha.strftime("%d/%m/%Y")}.\n\n¿Te gustaría ver otra fecha?',
                'intent': 'horarios_disponibles',
                'metadata': {}
            }
        
        mensaje_resp = f'🕐 **Horarios disponibles para {fecha.strftime("%d/%m/%Y")}:**\n\n'
        for horario in horarios[:10]:
            mensaje_resp += f"• {horario.hora.strftime('%H:%M')}\n"
        
        mensaje_resp += '\n¿Te gustaría reservar una cita?'
        
        return {
            'mensaje': mensaje_resp,
            'intent': 'horarios_disponibles',
            'opciones': ['Sí, reservar', 'Ver otra fecha', 'No'],
            'metadata': {'fecha': fecha.isoformat(), 'cantidad': len(horarios)}
        }
    
    def _iniciar_cancelar_cita(self):
        """Iniciar flujo de cancelación de cita."""
        if not self.conversacion.paciente:
            return {
                'mensaje': '⚠️ Necesito tu correo electrónico para ver tus citas.',
                'intent': 'cancelar_cita',
                'metadata': {'requiere_autenticacion': True}
            }
        
        # Obtener citas futuras
        hoy = datetime.now().date()
        citas = Consulta.objects.filter(
            codpaciente=self.conversacion.paciente,
            fecha__gte=hoy,
            estado__in=['pendiente', 'confirmada']
        ).order_by('fecha', 'idhorario__hora')[:5]
        
        if not citas.exists():
            return {
                'mensaje': 'No tienes citas futuras para cancelar.',
                'intent': 'cancelar_cita',
                'metadata': {}
            }
        
        mensaje = '📋 **Citas que puedes cancelar:**\n\n'
        for i, cita in enumerate(citas, 1):
            mensaje += f"{i}. {cita.fecha.strftime('%d/%m/%Y')} - {cita.idhorario.hora.strftime('%H:%M')}\n"
            mensaje += f"   {cita.idtipoconsulta.nombreconsulta}\n\n"
        
        mensaje += '¿Qué cita deseas cancelar? (escribe el número)'
        
        # Guardar contexto
        self.contexto = {
            'estado': 'esperando_cita_cancelar',
            'citas_cancelables': [c.id for c in citas]
        }
        self.conversacion.contexto = self.contexto
        self.conversacion.save()
        
        return {
            'mensaje': mensaje,
            'intent': 'cancelar_cita',
            'metadata': {'cantidad': citas.count()}
        }
    
    def _procesar_cancelacion(self, mensaje):
        """Procesar cancelación de cita."""
        try:
            seleccion = int(mensaje.strip())
            citas_ids = self.contexto.get('citas_cancelables', [])
            
            if seleccion < 1 or seleccion > len(citas_ids):
                raise ValueError()
            
            cita_id = citas_ids[seleccion - 1]
            cita = Consulta.objects.get(id=cita_id)
            
            # Cancelar la cita
            from apps.citas.models import Estadodeconsulta
            estado_cancelada = Estadodeconsulta.objects.get(estado='Cancelada')
            cita.estado = 'cancelada'
            cita.idestadoconsulta = estado_cancelada
            cita.motivo_cancelacion = 'Cancelada via chatbot'
            cita.save()
            
            # Limpiar contexto
            self.contexto = {}
            self.conversacion.contexto = self.contexto
            self.conversacion.save()
            
            return {
                'mensaje': f'✅ Cita del {cita.fecha.strftime("%d/%m/%Y")} cancelada exitosamente.\n\n¿Hay algo más en que pueda ayudarte?',
                'intent': 'cancelar_cita',
                'opciones': ['Ver mis citas', 'Reservar cita', 'No'],
                'metadata': {'cita_id': cita_id}
            }
            
        except (ValueError, Consulta.DoesNotExist):
            return {
                'mensaje': '⚠️ Selección inválida. Por favor escribe el número de la cita.',
                'intent': 'cancelar_cita',
                'metadata': {'error': 'seleccion_invalida'}
            }
    
    def _mostrar_ayuda(self):
        """Mostrar opciones de ayuda."""
        return {
            'mensaje': '🤖 **¿En qué puedo ayudarte?**\n\n'
                      '• Ver mis citas\n'
                      '• Reservar una cita\n'
                      '• Cancelar una cita\n'
                      '• Ver horarios disponibles\n\n'
                      'Solo escríbeme lo que necesitas.',
            'intent': 'ayuda',
            'opciones': ['Ver mis citas', 'Reservar cita', 'Horarios disponibles'],
            'metadata': {}
        }
    
    def _responder_despedida(self):
        """Responder a despedida."""
        return {
            'mensaje': '👋 ¡Hasta pronto! Si necesitas algo más, estoy aquí para ayudarte.',
            'intent': 'despedida',
            'metadata': {}
        }
    
    # Métodos auxiliares
    
    def _parsear_fecha(self, texto):
        """
        Parsear fecha del texto.
        Soporta: DD/MM/YYYY, "mañana", "pasado mañana"
        """
        texto = texto.lower().strip()
        
        # Palabras clave
        if 'mañana' in texto and 'pasado' not in texto:
            return datetime.now().date() + timedelta(days=1)
        
        if 'pasado mañana' in texto or 'pasadomañana' in texto:
            return datetime.now().date() + timedelta(days=2)
        
        if 'hoy' in texto:
            return datetime.now().date()
        
        # Intentar parsear DD/MM/YYYY
        match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', texto)
        if match:
            dia, mes, año = match.groups()
            try:
                return datetime(int(año), int(mes), int(dia)).date()
            except ValueError:
                pass
        
        return None
    
    def _obtener_horarios_disponibles(self, fecha):
        """Obtener horarios disponibles para una fecha."""
        # IDs de horarios ocupados
        horarios_ocupados = Consulta.objects.filter(
            fecha=fecha
        ).values_list('idhorario_id', flat=True)
        
        # Horarios disponibles
        return Horario.objects.exclude(id__in=horarios_ocupados).order_by('hora')
