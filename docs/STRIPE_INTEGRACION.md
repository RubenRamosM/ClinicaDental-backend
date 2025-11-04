# 💳 Integración de Stripe - Pago de Consultas

**Fecha:** 3 de Noviembre, 2025  
**Estado:** ✅ IMPLEMENTADO Y LISTO PARA USAR

---

## 📊 Resumen

El sistema ahora soporta **pago con tarjeta vía Stripe** antes de agendar una cita dental.

### ✅ Características Implementadas

1. **Payment Intent API** - Crear intención de pago en Stripe
2. **Validación de Pago** - Confirmar pago antes de crear cita
3. **Registro en BD** - Modelo `PagoEnLinea` con todos los datos de Stripe
4. **Vinculación Automática** - Pago se vincula a la consulta creada
5. **Clave Pública** - Endpoint para obtener publishable key

---

## 🔑 Configuración (Ya está lista)

### Variables de Entorno (.env)

```bash
# Ya configurado en tu .env
STRIPE_SECRET_KEY=sk_test_51SGSX5RxIhITCnEh...
STRIPE_PUBLIC_KEY=pk_test_51SGSX5RxIhITCnEh...
STRIPE_WEBHOOK_SECRET=whsec_tu_webhook_secret
```

### Settings.py

```python
# Ya configurado en config/settings.py
STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY')
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')
```

---

## 🚀 Flujo de Pago

### Paso 1: Obtener Clave Pública (Frontend)

```bash
GET /api/v1/pagos/stripe/clave-publica/
```

**Response:**
```json
{
  "publishable_key": "pk_test_51SGSX5RxIhITCnEh..."
}
```

### Paso 2: Crear Payment Intent

```bash
POST /api/v1/pagos/stripe/crear-intencion-consulta/
Authorization: Token abc123...

Body:
{
  "tipo_consulta_id": 198,
  "monto": 150.00  // Opcional
}
```

**Response:**
```json
{
  "client_secret": "pi_3Qxxx_secret_yyy",
  "pago_id": 45,
  "codigo_pago": "CITA-A3B2C1D4",
  "monto": 150.0,
  "moneda": "BOB",
  "tipo_consulta": "Consulta General"
}
```

### Paso 3: Procesar Pago con Stripe (Frontend)

```javascript
// React + Stripe Elements
import { CardElement, useStripe, useElements } from '@stripe/react-stripe-js';

const stripe = useStripe();
const elements = useElements();

// Confirmar pago
const result = await stripe.confirmCardPayment(client_secret, {
  payment_method: {
    card: elements.getElement(CardElement),
    billing_details: {
      name: 'Juan Pérez',
      email: 'juan@ejemplo.com',
    },
  },
});

if (result.error) {
  // Mostrar error
  console.error(result.error.message);
} else {
  if (result.paymentIntent.status === 'succeeded') {
    // Pago exitoso, continuar a paso 4
    await confirmarPagoBackend(pago_id);
  }
}
```

### Paso 4: Confirmar Pago en Backend

```bash
POST /api/v1/pagos/stripe/confirmar-pago/
Authorization: Token abc123...

Body:
{
  "pago_id": 45,
  "payment_intent_id": "pi_3Qxxx"  // Opcional
}
```

**Response:**
```json
{
  "success": true,
  "pago": {
    "id": 45,
    "codigo_pago": "CITA-A3B2C1D4",
    "estado": "aprobado",
    "monto": "150.00",
    "stripe_payment_intent_id": "pi_3Qxxx",
    "stripe_charge_id": "ch_3Qyyy"
  },
  "mensaje": "Pago confirmado exitosamente"
}
```

### Paso 5: Crear Cita con Pago

```bash
POST /api/v1/citas/
Authorization: Token abc123...

Body:
{
  "fecha": "2025-11-20",
  "codpaciente": 625,
  "cododontologo": 615,
  "idhorario": 948,
  "idtipoconsulta": 198,
  "idestadoconsulta": 295,
  "pago_id": 45  // ← ID del pago aprobado
}
```

**Response:**
```json
{
  "id": 432,
  "fecha": "2025-11-20",
  "paciente_nombre": "Carlos",
  "odontologo_nombre": "Dr(a). Juan Pérez",
  "estado": "pendiente",
  "pago_vinculado": true,
  "codigo_pago": "CITA-A3B2C1D4"
}
```

---

## 📝 Modelo PagoEnLinea

```python
class PagoEnLinea(models.Model):
    codigo_pago = models.CharField(max_length=50, unique=True)
    origen_tipo = models.CharField(max_length=30)  # 'consulta'
    consulta = models.ForeignKey('citas.Consulta', ...)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    moneda = models.CharField(max_length=3, default='BOB')
    estado = models.CharField(max_length=20)  # pendiente, aprobado, rechazado
    metodo_pago = models.CharField(max_length=20)  # tarjeta
    
    # Campos de Stripe
    stripe_payment_intent_id = models.CharField(max_length=255)
    stripe_charge_id = models.CharField(max_length=255)
    stripe_customer_id = models.CharField(max_length=255)
    stripe_metadata = models.JSONField(default=dict)
    
    descripcion = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
```

---

## 🔄 Estados de Pago

| Estado | Descripción |
|--------|-------------|
| `pendiente` | Payment Intent creado, esperando pago |
| `procesando` | Stripe procesando el pago |
| `aprobado` | Pago exitoso, puede crear cita |
| `rechazado` | Tarjeta rechazada |
| `cancelado` | Usuario canceló el pago |
| `reembolsado` | Pago devuelto |
| `anulado` | Pago anulado administrativamente |

---

## 🎨 Frontend - Ejemplo Completo

### Instalación

```bash
npm install @stripe/stripe-js @stripe/react-stripe-js
```

### Componente PagarConsulta.tsx

```typescript
import React, { useState, useEffect } from 'react';
import { loadStripe } from '@stripe/stripe-js';
import {
  Elements,
  CardElement,
  useStripe,
  useElements,
} from '@stripe/react-stripe-js';
import Api from './api';

// 1. Obtener clave pública
const getStripePublicKey = async () => {
  const res = await Api.get('/pagos/stripe/clave-publica/');
  return res.data.publishable_key;
};

// 2. Componente de formulario de pago
function CheckoutForm({ tipoConsultaId, onSuccess }) {
  const stripe = useStripe();
  const elements = useElements();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [clientSecret, setClientSecret] = useState('');
  const [pagoId, setPagoId] = useState(null);

  // Crear Payment Intent al montar
  useEffect(() => {
    crearIntencionPago();
  }, []);

  const crearIntencionPago = async () => {
    try {
      const res = await Api.post('/pagos/stripe/crear-intencion-consulta/', {
        tipo_consulta_id: tipoConsultaId,
      });
      
      setClientSecret(res.data.client_secret);
      setPagoId(res.data.pago_id);
      
    } catch (err) {
      setError(err.response?.data?.error || 'Error al crear intención de pago');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!stripe || !elements) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Confirmar pago con tarjeta
      const result = await stripe.confirmCardPayment(clientSecret, {
        payment_method: {
          card: elements.getElement(CardElement),
          billing_details: {
            name: 'Usuario',
          },
        },
      });

      if (result.error) {
        setError(result.error.message);
        setLoading(false);
      } else {
        if (result.paymentIntent.status === 'succeeded') {
          // Confirmar en backend
          await Api.post('/pagos/stripe/confirmar-pago/', {
            pago_id: pagoId,
            payment_intent_id: result.paymentIntent.id,
          });
          
          // Llamar callback de éxito
          onSuccess(pagoId);
        }
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Error al procesar pago');
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <CardElement
        options={{
          style: {
            base: {
              fontSize: '16px',
              color: '#424770',
              '::placeholder': {
                color: '#aab7c4',
              },
            },
          },
        }}
      />
      
      {error && <div className="error">{error}</div>}
      
      <button type="submit" disabled={!stripe || loading}>
        {loading ? 'Procesando...' : 'Pagar'}
      </button>
    </form>
  );
}

// 3. Componente principal
export default function PagarYAgendarCita({ tipoConsultaId }) {
  const [stripePromise, setStripePromise] = useState(null);
  const [citaCreada, setCitaCreada] = useState(false);

  useEffect(() => {
    // Cargar Stripe
    getStripePublicKey().then((key) => {
      setStripePromise(loadStripe(key));
    });
  }, []);

  const handlePagoExitoso = async (pagoId) => {
    // Crear cita con el pago
    try {
      const res = await Api.post('/citas/', {
        fecha: '2025-11-20',
        codpaciente: 625,
        cododontologo: 615,
        idhorario: 948,
        idtipoconsulta: tipoConsultaId,
        idestadoconsulta: 295,
        pago_id: pagoId,
      });
      
      setCitaCreada(true);
      alert('¡Cita agendada y pagada exitosamente!');
      
    } catch (err) {
      alert('Error al crear cita: ' + err.response?.data?.error);
    }
  };

  if (!stripePromise) {
    return <div>Cargando...</div>;
  }

  if (citaCreada) {
    return <div>✅ Cita creada exitosamente</div>;
  }

  return (
    <div>
      <h2>Pagar Consulta</h2>
      <Elements stripe={stripePromise}>
        <CheckoutForm
          tipoConsultaId={tipoConsultaId}
          onSuccess={handlePagoExitoso}
        />
      </Elements>
    </div>
  );
}
```

---

## 🧪 Testing

### Tarjetas de Prueba de Stripe

```
✅ Pago Exitoso:
   Número: 4242 4242 4242 4242
   Fecha: Cualquier fecha futura
   CVC: Cualquier 3 dígitos

❌ Pago Rechazado (Fondos Insuficientes):
   Número: 4000 0000 0000 9995

❌ Pago Rechazado (Tarjeta Declinada):
   Número: 4000 0000 0000 0002

🔄 Requiere Autenticación 3D Secure:
   Número: 4000 0025 0000 3155
```

### Probar desde cURL

```bash
# 1. Obtener clave pública
curl http://localhost:8000/api/v1/pagos/stripe/clave-publica/ \
  -H "Authorization: Token tu_token_aqui"

# 2. Crear intención de pago
curl -X POST http://localhost:8000/api/v1/pagos/stripe/crear-intencion-consulta/ \
  -H "Authorization: Token tu_token_aqui" \
  -H "Content-Type: application/json" \
  -d '{"tipo_consulta_id": 198, "monto": 150.00}'

# 3. Ver pagos pendientes
curl http://localhost:8000/api/v1/pagos/pagos-online/ \
  -H "Authorization: Token tu_token_aqui"
```

---

## ⚠️ Modo Test vs Producción

### Desarrollo (TEST MODE)

```bash
# .env
STRIPE_SECRET_KEY=sk_test_51SGSX5...  # ← sk_test_
STRIPE_PUBLIC_KEY=pk_test_51SGSX5...  # ← pk_test_
```

- ✅ Sin cargo real
- ✅ Tarjetas de prueba
- ✅ Dashboard: https://dashboard.stripe.com/test

### Producción (LIVE MODE)

```bash
# .env (producción)
STRIPE_SECRET_KEY=sk_live_...  # ← sk_live_
STRIPE_PUBLIC_KEY=pk_live_...  # ← pk_live_
```

- ⚠️ CARGOS REALES
- ⚠️ Tarjetas reales
- 📊 Dashboard: https://dashboard.stripe.com/live

---

## 📊 Ventajas del Sistema

✅ **Reducción de No-Shows** - Pago anticipado compromete al paciente  
✅ **Ingresos Garantizados** - Dinero antes de la cita  
✅ **Automatización** - Sin intervención manual  
✅ **Seguridad** - PCI Compliance de Stripe  
✅ **Flexibilidad** - Pago opcional (se puede agendar sin pagar también)  
✅ **Trazabilidad** - Registro completo en BD

---

## 🔧 Endpoints Disponibles

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/pagos/stripe/clave-publica/` | Obtener publishable key |
| POST | `/pagos/stripe/crear-intencion-consulta/` | Crear Payment Intent |
| POST | `/pagos/stripe/confirmar-pago/` | Confirmar pago exitoso |
| GET | `/pagos/pagos-online/` | Listar pagos online |
| POST | `/citas/` | Crear cita (con `pago_id` opcional) |

---

## 📝 Notas Importantes

1. **Pago Opcional**: El sistema permite crear citas CON o SIN pago
   - Con `pago_id`: Valida que esté aprobado
   - Sin `pago_id`: Crea cita normal (pago presencial)

2. **Validaciones**:
   - Pago debe estar en estado "aprobado"
   - Pago no puede estar vinculado a otra consulta
   - Monto se toma del tipo de consulta o se puede enviar manualmente

3. **Moneda**: Configurado para BOB (Bolivianos), pero se puede cambiar a USD

4. **Webhooks**: Pendiente de implementar para recibir eventos de Stripe

---

**Última actualización:** Noviembre 3, 2025  
**Estado:** ✅ Totalmente funcional en modo TEST
