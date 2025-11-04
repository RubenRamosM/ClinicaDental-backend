# 🤖 Chatbot de Citas - Clínica Dental

## 📋 Descripción

Chatbot inteligente para gestionar citas de manera conversacional. Permite a los pacientes:
- ✅ Ver sus citas agendadas
- ✅ Reservar nuevas citas
- ✅ Consultar horarios disponibles
- ✅ Cancelar citas existentes

## 🚀 Características

### ✨ Funcionalidades Principales

1. **Ver Citas**
   - Muestra próximas citas del paciente
   - Incluye fecha, hora, tipo y estado
   - Filtrado automático por paciente autenticado

2. **Reservar Citas (Flujo en 4 pasos)**
   - Paso 1: Selección de fecha
   - Paso 2: Selección de horario disponible
   - Paso 3: Selección de tipo de consulta
   - Paso 4: Confirmación final

3. **Horarios Disponibles**
   - Consulta de slots libres por fecha
   - Actualización en tiempo real

4. **Cancelar Citas**
   - Lista de citas futuras cancelables
   - Confirmación antes de cancelar

### 🧠 Procesamiento Inteligente

- **Detección de Intents**: Reconoce la intención del usuario mediante palabras clave
- **Contexto Persistente**: Mantiene el estado de la conversación
- **Multi-paso**: Maneja flujos complejos con múltiples pasos
- **Validaciones**: Fecha futura, disponibilidad, paciente válido

## 📊 Arquitectura

```
apps/chatbot/
├── models.py              # ConversacionChatbot, MensajeChatbot
├── serializers.py         # Serializers de requests/responses
├── bot_engine.py          # Motor de procesamiento de intents
├── views.py               # API ViewSet (mensaje, historial, reset)
├── urls.py                # Routing
└── admin.py               # Administración Django
```

### Modelos

**ConversacionChatbot**
- `session_id`: ID único de sesión
- `paciente`: Relación con paciente (opcional)
- `correo_electronico`, `nombre`, `telefono`
- `contexto`: Estado JSON de la conversación
- `ultima_interaccion`: Timestamp

**MensajeChatbot**
- `conversacion`: FK a ConversacionChatbot
- `tipo`: usuario | bot | sistema
- `mensaje`: Texto del mensaje
- `metadata`: Información adicional (intent, opciones)

## 🔌 API Endpoints

### POST `/api/v1/chatbot/mensaje/`

Enviar mensaje al chatbot.

**Request:**
```json
{
  "session_id": "unique-session-id",
  "mensaje": "Hola, quiero ver mis citas",
  "correo_electronico": "paciente@example.com",  // opcional
  "nombre": "Juan Pérez",  // opcional
  "telefono": "77777777"  // opcional
}
```

**Response:**
```json
{
  "mensaje": "¡Hola Juan! 👋 Soy el asistente virtual de la Clínica Dental. ¿En qué puedo ayudarte?",
  "opciones": [
    "Ver mis citas",
    "Reservar una cita",
    "Horarios disponibles",
    "Ayuda"
  ],
  "intent": "saludo",
  "metadata": {}
}
```

### GET `/api/v1/chatbot/historial/?session_id=xxx`

Obtener historial completo de una conversación.

**Response:**
```json
{
  "id": 1,
  "session_id": "unique-session-id",
  "paciente": 5,
  "correo_electronico": "paciente@example.com",
  "nombre": "Juan Pérez",
  "telefono": "77777777",
  "ultima_interaccion": "2025-11-03T15:00:00Z",
  "contexto": {},
  "mensajes": [
    {
      "id": 1,
      "tipo": "usuario",
      "mensaje": "Hola",
      "metadata": {},
      "fecha_creacion": "2025-11-03T15:00:00Z"
    },
    {
      "id": 2,
      "tipo": "bot",
      "mensaje": "¡Hola! ¿En qué puedo ayudarte?",
      "metadata": {
        "intent": "saludo",
        "opciones": ["Ver citas", "Reservar"]
      },
      "fecha_creacion": "2025-11-03T15:00:01Z"
    }
  ]
}
```

### POST `/api/v1/chatbot/reset/`

Reiniciar conversación (limpiar contexto).

**Request:**
```json
{
  "session_id": "unique-session-id"
}
```

**Response:**
```json
{
  "mensaje": "Conversación reiniciada"
}
```

## 🎯 Intents Soportados

| Intent | Palabras Clave | Descripción |
|--------|---------------|-------------|
| `saludo` | hola, buenos días, hey | Saludo inicial |
| `ver_citas` | ver citas, mis citas, consultas | Listar citas del paciente |
| `reservar_cita` | reservar, agendar, quiero cita | Iniciar flujo de reserva |
| `cancelar_cita` | cancelar, eliminar cita | Iniciar flujo de cancelación |
| `horarios_disponibles` | horarios, disponibilidad, cuándo hay | Ver horarios libres |
| `ayuda` | ayuda, help, opciones | Mostrar menú de ayuda |
| `despedida` | adiós, chao, gracias | Terminar conversación |

## 📝 Ejemplo de Uso

### Flujo Completo de Reserva

**1. Saludo e inicio:**
```
Usuario: Hola
Bot: ¡Hola! 👋 Soy el asistente virtual...
```

**2. Solicitar reserva:**
```
Usuario: Quiero reservar una cita
Bot: 📅 Perfecto, vamos a reservar tu cita. ¿Para qué fecha te gustaría?
```

**3. Proporcionar fecha:**
```
Usuario: mañana
Bot: ✅ Fecha: 04/11/2025

🕐 Horarios disponibles:
1. 08:00
2. 09:00
3. 10:00
...

¿Qué horario prefieres?
```

**4. Seleccionar horario:**
```
Usuario: 2
Bot: ✅ Horario seleccionado: 09:00

🦷 Tipo de consulta:
1. Primera Vez
2. Control
3. Urgencia

¿Qué tipo de consulta necesitas?
```

**5. Seleccionar tipo:**
```
Usuario: 1
Bot: 📋 Resumen de tu cita:

📅 Fecha: 04/11/2025
🕐 Hora: 09:00
🦷 Tipo: Primera Vez

¿Confirmas la cita?
```

**6. Confirmar:**
```
Usuario: sí
Bot: ✅ ¡Cita reservada exitosamente!

📅 Fecha: 04/11/2025
🕐 Hora: 09:00
🦷 Tipo: Primera Vez
📋 ID: #123

¿Hay algo más en que pueda ayudarte?
```

## 🧪 Pruebas

### Usando REST Client (VS Code)

1. Abrir `test_chatbot.http`
2. Ejecutar requests en orden
3. Verificar respuestas del bot

### Usando Postman/Newman

1. Importar colección desde `test_chatbot.http`
2. Ejecutar flujos completos
3. Validar contexto y respuestas

## 🔧 Configuración

### 1. Instalación

```bash
# Agregar app a INSTALLED_APPS
INSTALLED_APPS = [
    ...
    "apps.chatbot",
]

# Agregar URLs
urlpatterns = [
    ...
    path('api/v1/', include('apps.chatbot.urls')),
]
```

### 2. Migraciones

```bash
python manage.py makemigrations chatbot
python manage.py migrate chatbot
```

### 3. Crear Tipos de Consulta Permitidos

En el admin de Django, marcar tipos de consulta con:
```python
permite_agendamiento_web = True
```

## 🎨 Frontend Integration

### React Example

```typescript
// Servicio de chatbot
import axios from 'axios';

const API_URL = 'http://localhost:8000/api/v1';

interface ChatMessage {
  tipo: 'usuario' | 'bot';
  mensaje: string;
  opciones?: string[];
}

class ChatbotService {
  private sessionId: string;
  
  constructor() {
    this.sessionId = `session-${Date.now()}`;
  }
  
  async enviarMensaje(
    mensaje: string,
    correo?: string,
    nombre?: string
  ): Promise<ChatMessage> {
    const response = await axios.post(`${API_URL}/chatbot/mensaje/`, {
      session_id: this.sessionId,
      mensaje,
      correo_electronico: correo,
      nombre
    });
    
    return {
      tipo: 'bot',
      mensaje: response.data.mensaje,
      opciones: response.data.opciones
    };
  }
  
  async obtenerHistorial() {
    const response = await axios.get(
      `${API_URL}/chatbot/historial/?session_id=${this.sessionId}`
    );
    return response.data.mensajes;
  }
}

export default new ChatbotService();
```

### Componente de Chat

```typescript
import React, { useState } from 'react';
import chatbotService from './services/chatbotService';

const Chatbot: React.FC = () => {
  const [mensajes, setMensajes] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  
  const enviar = async () => {
    // Agregar mensaje del usuario
    setMensajes([...mensajes, { tipo: 'usuario', mensaje: input }]);
    
    // Obtener respuesta del bot
    const respuesta = await chatbotService.enviarMensaje(input);
    setMensajes(prev => [...prev, respuesta]);
    
    setInput('');
  };
  
  return (
    <div className="chatbot">
      <div className="mensajes">
        {mensajes.map((msg, i) => (
          <div key={i} className={msg.tipo}>
            {msg.mensaje}
            {msg.opciones && (
              <div className="opciones">
                {msg.opciones.map(opt => (
                  <button onClick={() => setInput(opt)}>{opt}</button>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
      <input
        value={input}
        onChange={e => setInput(e.target.value)}
        onKeyPress={e => e.key === 'Enter' && enviar()}
      />
      <button onClick={enviar}>Enviar</button>
    </div>
  );
};
```

## 📈 Mejoras Futuras

### Versión 1.1
- [ ] Soporte para recordatorios de citas
- [ ] Notificaciones push cuando se reserva
- [ ] Integración con WhatsApp/Telegram

### Versión 2.0
- [ ] NLP avanzado (spaCy, Transformers)
- [ ] Soporte multi-idioma
- [ ] Respuestas con IA generativa (GPT)
- [ ] Análisis de sentimiento

### Versión 3.0
- [ ] Reconocimiento de voz
- [ ] Avatar animado
- [ ] Historial de salud conversacional

## 🐛 Troubleshooting

**Problema:** "Paciente no identificado"
- **Solución:** Proporcionar `correo_electronico` en el request

**Problema:** "No hay horarios disponibles"
- **Solución:** Verificar que existan horarios en la DB y que no estén todos ocupados

**Problema:** Intent no reconocido
- **Solución:** Usar palabras clave exactas del listado de intents

## 📚 Documentación Adicional

- [Django REST Framework](https://www.django-rest-framework.org/)
- [Chatbot Design Patterns](https://www.chatbotguide.org/)
- [Conversational UI Best Practices](https://uxdesign.cc/conversational-ui/)

## 👨‍💻 Desarrollo

```bash
# Ejecutar tests
python manage.py test apps.chatbot

# Ver logs de conversaciones
python manage.py shell
>>> from apps.chatbot.models import ConversacionChatbot
>>> ConversacionChatbot.objects.all()
```

## 📄 Licencia

Proyecto privado - Clínica Dental

---

✨ **¡Chatbot listo para usar!** ✨
