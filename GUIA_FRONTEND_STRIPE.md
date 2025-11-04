# 🎨 GUÍA COMPLETA PARA INTEGRACIÓN STRIPE EN FRONTEND

## 📋 TABLA DE CONTENIDOS
1. [Instalación de Dependencias](#1-instalación-de-dependencias)
2. [Configuración Inicial](#2-configuración-inicial)
3. [Componentes React](#3-componentes-react)
4. [Flujo de Pago Completo](#4-flujo-de-pago-completo)
5. [Manejo de Errores](#5-manejo-de-errores)
6. [Testing](#6-testing)

---

## 1. INSTALACIÓN DE DEPENDENCIAS

```bash
npm install @stripe/stripe-js @stripe/react-stripe-js
```

**Versiones recomendadas:**
- `@stripe/stripe-js`: ^4.0.0
- `@stripe/react-stripe-js`: ^2.8.0

---

## 2. CONFIGURACIÓN INICIAL

### 2.1 Variables de Entorno (`.env`)

```env
# Frontend
VITE_API_URL=http://localhost:8000/api/v1
VITE_STRIPE_PUBLIC_KEY=pk_test_51SGSX5RxIhITCnEhcPNiGfOpV4L9Pe1lNlryCgvqODk6Xk9gm3AqlDo6rTtoModZ0l6Hibn5XexCkATvJu2MAOCU00W3EreDIW
```

### 2.2 Cliente API (`src/services/api.ts`)

```typescript
import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para agregar token automáticamente
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Token ${token}`;
  }
  return config;
});

export default api;
```

### 2.3 Servicio Stripe (`src/services/stripeService.ts`)

```typescript
import api from './api';

export interface TipoConsulta {
  id: number;
  nombre: string;
  costo: number;
  descripcion: string;
}

export interface PaymentIntentResponse {
  client_secret: string;
  pago_id: number;
  codigo_pago: string;
  monto: number;
  moneda: string;
}

export interface ConfirmPaymentResponse {
  success: boolean;
  mensaje: string;
  pago: {
    id: number;
    codigo_pago: string;
    estado: string;
    monto: number;
  };
}

class StripeService {
  // Obtener clave pública de Stripe
  async getPublishableKey(): Promise<string> {
    const response = await api.get('/pagos/stripe/clave-publica/');
    return response.data.publishable_key;
  }

  // Crear Payment Intent
  async createPaymentIntent(
    tipoConsultaId: number,
    monto?: number
  ): Promise<PaymentIntentResponse> {
    const response = await api.post('/pagos/stripe/crear-intencion-consulta/', {
      tipo_consulta_id: tipoConsultaId,
      monto: monto,
    });
    return response.data;
  }

  // Confirmar pago
  async confirmPayment(pagoId: number): Promise<ConfirmPaymentResponse> {
    const response = await api.post('/pagos/stripe/confirmar-pago/', {
      pago_id: pagoId,
    });
    return response.data;
  }

  // Obtener tipos de consulta
  async getTiposConsulta(): Promise<TipoConsulta[]> {
    const response = await api.get('/tipos-consulta/');
    return response.data.results || response.data;
  }
}

export default new StripeService();
```

---

## 3. COMPONENTES REACT

### 3.1 Componente Principal: AgendarCitaConPago

```tsx
// src/pages/AgendarCitaConPago.tsx
import React, { useState, useEffect } from 'react';
import { loadStripe } from '@stripe/stripe-js';
import { Elements } from '@stripe/react-stripe-js';
import FormularioCita from '../components/FormularioCita';
import CheckoutForm from '../components/CheckoutForm';
import stripeService from '../services/stripeService';

const AgendarCitaConPago: React.FC = () => {
  const [stripePromise, setStripePromise] = useState(null);
  const [paso, setPaso] = useState<'seleccion' | 'pago' | 'confirmacion'>('seleccion');
  const [datosConsulta, setDatosConsulta] = useState(null);
  const [clientSecret, setClientSecret] = useState('');
  const [pagoId, setPagoId] = useState<number | null>(null);

  useEffect(() => {
    // Cargar Stripe con clave pública
    const initStripe = async () => {
      const publicKey = await stripeService.getPublishableKey();
      setStripePromise(loadStripe(publicKey));
    };
    initStripe();
  }, []);

  const handleSeleccionarConsulta = async (datos: any) => {
    setDatosConsulta(datos);
    
    // Crear Payment Intent
    try {
      const response = await stripeService.createPaymentIntent(
        datos.tipoConsultaId,
        datos.monto
      );
      
      setClientSecret(response.client_secret);
      setPagoId(response.pago_id);
      setPaso('pago');
    } catch (error) {
      console.error('Error al crear intención de pago:', error);
      alert('Error al iniciar el pago. Por favor intenta nuevamente.');
    }
  };

  const handlePagoExitoso = () => {
    setPaso('confirmacion');
  };

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Agendar Cita con Pago</h1>

      {/* Paso 1: Seleccionar consulta */}
      {paso === 'seleccion' && (
        <FormularioCita onSubmit={handleSeleccionarConsulta} />
      )}

      {/* Paso 2: Realizar pago */}
      {paso === 'pago' && stripePromise && clientSecret && (
        <Elements stripe={stripePromise} options={{ clientSecret }}>
          <CheckoutForm
            datosConsulta={datosConsulta}
            pagoId={pagoId}
            onSuccess={handlePagoExitoso}
          />
        </Elements>
      )}

      {/* Paso 3: Confirmación */}
      {paso === 'confirmacion' && (
        <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded">
          <h2 className="text-xl font-bold mb-2">¡Pago Exitoso!</h2>
          <p>Tu cita ha sido agendada correctamente.</p>
          <p className="mt-2">Código de pago: <strong>{datosConsulta?.codigoPago}</strong></p>
        </div>
      )}
    </div>
  );
};

export default AgendarCitaConPago;
```

### 3.2 Formulario de Cita

```tsx
// src/components/FormularioCita.tsx
import React, { useState, useEffect } from 'react';
import stripeService, { TipoConsulta } from '../services/stripeService';

interface Props {
  onSubmit: (datos: any) => void;
}

const FormularioCita: React.FC<Props> = ({ onSubmit }) => {
  const [tiposConsulta, setTiposConsulta] = useState<TipoConsulta[]>([]);
  const [tipoSeleccionado, setTipoSeleccionado] = useState<number | null>(null);
  const [fecha, setFecha] = useState('');
  const [hora, setHora] = useState('');
  const [motivo, setMotivo] = useState('');

  useEffect(() => {
    // Cargar tipos de consulta
    const cargarTipos = async () => {
      try {
        const tipos = await stripeService.getTiposConsulta();
        setTiposConsulta(tipos);
      } catch (error) {
        console.error('Error al cargar tipos de consulta:', error);
      }
    };
    cargarTipos();
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    const tipoConsulta = tiposConsulta.find(t => t.id === tipoSeleccionado);
    
    onSubmit({
      tipoConsultaId: tipoSeleccionado,
      monto: tipoConsulta?.costo,
      fecha,
      hora,
      motivo,
      nombreConsulta: tipoConsulta?.nombre,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="max-w-2xl mx-auto bg-white shadow-md rounded px-8 pt-6 pb-8 mb-4">
      <h2 className="text-2xl font-bold mb-6">Datos de la Cita</h2>

      {/* Tipo de Consulta */}
      <div className="mb-4">
        <label className="block text-gray-700 text-sm font-bold mb-2">
          Tipo de Consulta *
        </label>
        <select
          value={tipoSeleccionado || ''}
          onChange={(e) => setTipoSeleccionado(Number(e.target.value))}
          className="shadow border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
          required
        >
          <option value="">Seleccionar...</option>
          {tiposConsulta.map((tipo) => (
            <option key={tipo.id} value={tipo.id}>
              {tipo.nombre} - Bs. {tipo.costo.toFixed(2)}
            </option>
          ))}
        </select>
      </div>

      {/* Fecha */}
      <div className="mb-4">
        <label className="block text-gray-700 text-sm font-bold mb-2">
          Fecha *
        </label>
        <input
          type="date"
          value={fecha}
          onChange={(e) => setFecha(e.target.value)}
          className="shadow border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
          required
        />
      </div>

      {/* Hora */}
      <div className="mb-4">
        <label className="block text-gray-700 text-sm font-bold mb-2">
          Hora *
        </label>
        <input
          type="time"
          value={hora}
          onChange={(e) => setHora(e.target.value)}
          className="shadow border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
          required
        />
      </div>

      {/* Motivo */}
      <div className="mb-6">
        <label className="block text-gray-700 text-sm font-bold mb-2">
          Motivo de la Consulta
        </label>
        <textarea
          value={motivo}
          onChange={(e) => setMotivo(e.target.value)}
          className="shadow border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
          rows={4}
          placeholder="Describe brevemente el motivo de tu consulta..."
        />
      </div>

      <button
        type="submit"
        className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline w-full"
        disabled={!tipoSeleccionado}
      >
        Continuar al Pago
      </button>
    </form>
  );
};

export default FormularioCita;
```

### 3.3 Formulario de Pago con Stripe Elements

```tsx
// src/components/CheckoutForm.tsx
import React, { useState } from 'react';
import { useStripe, useElements, CardElement } from '@stripe/react-stripe-js';
import stripeService from '../services/stripeService';
import api from '../services/api';

interface Props {
  datosConsulta: any;
  pagoId: number;
  onSuccess: () => void;
}

const CheckoutForm: React.FC<Props> = ({ datosConsulta, pagoId, onSuccess }) => {
  const stripe = useStripe();
  const elements = useElements();
  const [procesando, setProcesando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();

    if (!stripe || !elements) {
      return;
    }

    setProcesando(true);
    setError(null);

    const cardElement = elements.getElement(CardElement);

    try {
      // 1. Confirmar pago con Stripe
      const { error: stripeError, paymentIntent } = await stripe.confirmCardPayment(
        datosConsulta.clientSecret,
        {
          payment_method: {
            card: cardElement!,
            billing_details: {
              name: datosConsulta.nombrePaciente || 'Paciente',
            },
          },
        }
      );

      if (stripeError) {
        throw new Error(stripeError.message);
      }

      if (paymentIntent.status === 'succeeded') {
        // 2. Confirmar en backend
        const confirmacion = await stripeService.confirmPayment(pagoId);

        if (confirmacion.success) {
          // 3. Crear la cita con el pago vinculado
          await api.post('/citas/', {
            fecha: datosConsulta.fecha,
            hora: datosConsulta.hora,
            motivo: datosConsulta.motivo,
            tipo_consulta: datosConsulta.tipoConsultaId,
            pago_id: pagoId, // ← Vincula el pago
          });

          onSuccess();
        } else {
          throw new Error('Error al confirmar el pago en el servidor');
        }
      }
    } catch (err: any) {
      setError(err.message || 'Error al procesar el pago');
      console.error('Error en pago:', err);
    } finally {
      setProcesando(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="max-w-2xl mx-auto bg-white shadow-md rounded px-8 pt-6 pb-8 mb-4">
      <h2 className="text-2xl font-bold mb-6">Información de Pago</h2>

      {/* Resumen de Consulta */}
      <div className="bg-gray-100 p-4 rounded mb-6">
        <h3 className="font-bold mb-2">Resumen de tu Cita:</h3>
        <p><strong>Tipo:</strong> {datosConsulta.nombreConsulta}</p>
        <p><strong>Fecha:</strong> {datosConsulta.fecha} a las {datosConsulta.hora}</p>
        <p className="text-xl font-bold mt-2">
          Total a pagar: Bs. {datosConsulta.monto?.toFixed(2)}
        </p>
      </div>

      {/* Stripe Card Element */}
      <div className="mb-6">
        <label className="block text-gray-700 text-sm font-bold mb-2">
          Datos de Tarjeta
        </label>
        <div className="shadow border rounded py-3 px-3 bg-white">
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
                invalid: {
                  color: '#9e2146',
                },
              },
            }}
          />
        </div>
      </div>

      {/* Mensaje de Error */}
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {/* Tarjetas de Prueba */}
      <div className="bg-blue-50 border border-blue-200 text-blue-800 px-4 py-3 rounded mb-4 text-sm">
        <p className="font-bold">💳 Tarjetas de Prueba:</p>
        <p>Exitosa: 4242 4242 4242 4242</p>
        <p>Declinada: 4000 0000 0000 9995</p>
        <p>CVV: Cualquier 3 dígitos | Fecha: Cualquier fecha futura</p>
      </div>

      {/* Botón de Pago */}
      <button
        type="submit"
        disabled={!stripe || procesando}
        className={`w-full font-bold py-3 px-4 rounded focus:outline-none focus:shadow-outline ${
          procesando
            ? 'bg-gray-400 cursor-not-allowed'
            : 'bg-green-500 hover:bg-green-700 text-white'
        }`}
      >
        {procesando ? 'Procesando...' : `Pagar Bs. ${datosConsulta.monto?.toFixed(2)}`}
      </button>
    </form>
  );
};

export default CheckoutForm;
```

---

## 4. FLUJO DE PAGO COMPLETO

### Diagrama de Secuencia

```
USUARIO                FRONTEND              BACKEND              STRIPE
  |                       |                      |                   |
  |--1. Llenar formulario-->|                      |                   |
  |                       |                      |                   |
  |                       |--2. POST crear-intencion-->|              |
  |                       |      (tipo_consulta_id)    |              |
  |                       |                      |                   |
  |                       |                      |--3. PaymentIntent.create()-->|
  |                       |                      |                   |
  |                       |<--4. client_secret, pago_id---|           |
  |                       |                      |                   |
  |<--5. Mostrar CardElement--|                      |                   |
  |                       |                      |                   |
  |--6. Ingresar tarjeta--->|                      |                   |
  |                       |                      |                   |
  |                       |--7. confirmCardPayment()----------------->|
  |                       |                      |                   |
  |                       |<--8. paymentIntent.status = 'succeeded'---|
  |                       |                      |                   |
  |                       |--9. POST confirmar-pago-->|              |
  |                       |      (pago_id)            |              |
  |                       |                      |--10. Verify PaymentIntent-->|
  |                       |                      |                   |
  |                       |                      |<--11. status = 'succeeded'--|
  |                       |                      |                   |
  |                       |                      |--12. Update estado='aprobado'|
  |                       |<--13. success=true----|                   |
  |                       |                      |                   |
  |                       |--14. POST /citas/--->|                   |
  |                       |    {pago_id: 45}     |                   |
  |                       |                      |--15. Validate pago|
  |                       |                      |--16. Create Consulta|
  |                       |                      |--17. Link pago->consulta|
  |                       |<--18. Cita creada----|                   |
  |                       |                      |                   |
  |<--19. Mostrar confirmación-|                      |                   |
```

### Pasos Detallados

1. **Usuario llena formulario** de tipo de consulta, fecha, hora
2. **Frontend crea Payment Intent** → `POST /api/v1/pagos/stripe/crear-intencion-consulta/`
3. **Backend crea PaymentIntent** en Stripe con el monto
4. **Backend devuelve** `client_secret` + `pago_id` al frontend
5. **Frontend muestra** Stripe CardElement
6. **Usuario ingresa** datos de tarjeta
7. **Frontend confirma pago** con `stripe.confirmCardPayment()`
8. **Stripe procesa** el pago y devuelve `paymentIntent.status = 'succeeded'`
9. **Frontend confirma** en backend → `POST /api/v1/pagos/stripe/confirmar-pago/`
10. **Backend verifica** con Stripe que el pago fue exitoso
11. **Backend actualiza** `PagoEnLinea.estado = 'aprobado'`
12. **Frontend crea cita** → `POST /api/v1/citas/` con `pago_id`
13. **Backend valida** que el pago esté aprobado
14. **Backend vincula** pago a la consulta creada
15. **Frontend muestra confirmación** al usuario

---

## 5. MANEJO DE ERRORES

### 5.1 Errores Comunes

```typescript
// src/utils/stripeErrors.ts
export const getStripeErrorMessage = (errorCode: string): string => {
  const errorMessages: Record<string, string> = {
    'card_declined': 'Tu tarjeta fue declinada. Por favor intenta con otra tarjeta.',
    'insufficient_funds': 'Fondos insuficientes en la tarjeta.',
    'expired_card': 'Tu tarjeta ha expirado.',
    'incorrect_cvc': 'El código de seguridad (CVV) es incorrecto.',
    'processing_error': 'Error al procesar el pago. Intenta nuevamente.',
    'invalid_number': 'Número de tarjeta inválido.',
  };

  return errorMessages[errorCode] || 'Error desconocido. Por favor contacta a soporte.';
};
```

### 5.2 Componente de Manejo de Errores

```tsx
// src/components/ErrorBoundary.tsx
import React from 'react';

interface Props {
  children: React.ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error en pago:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          <h2 className="font-bold">¡Algo salió mal!</h2>
          <p>{this.state.error?.message}</p>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            className="mt-3 bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 rounded"
          >
            Intentar nuevamente
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
```

---

## 6. TESTING

### 6.1 Tarjetas de Prueba Stripe

| Número | Resultado | CVV | Fecha |
|--------|-----------|-----|-------|
| `4242 4242 4242 4242` | ✅ Pago exitoso | Cualquier 3 dígitos | Cualquier fecha futura |
| `4000 0000 0000 9995` | ❌ Pago declinado | Cualquier 3 dígitos | Cualquier fecha futura |
| `4000 0000 0000 9987` | ❌ Fondos insuficientes | Cualquier 3 dígitos | Cualquier fecha futura |
| `4000 0000 0000 0069` | ❌ Tarjeta expirada | Cualquier 3 dígitos | Fecha pasada |

### 6.2 Test con Jest + React Testing Library

```typescript
// src/components/__tests__/CheckoutForm.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Elements } from '@stripe/react-stripe-js';
import { loadStripe } from '@stripe/stripe-js';
import CheckoutForm from '../CheckoutForm';

const stripePromise = loadStripe('pk_test_...');

describe('CheckoutForm', () => {
  it('debe mostrar el formulario de pago', () => {
    const mockDatos = {
      nombreConsulta: 'Control',
      fecha: '2025-11-15',
      hora: '10:00',
      monto: 150,
    };

    render(
      <Elements stripe={stripePromise}>
        <CheckoutForm
          datosConsulta={mockDatos}
          pagoId={123}
          onSuccess={() => {}}
        />
      </Elements>
    );

    expect(screen.getByText(/Información de Pago/i)).toBeInTheDocument();
    expect(screen.getByText(/Bs. 150.00/i)).toBeInTheDocument();
  });

  it('debe deshabilitar el botón mientras procesa', async () => {
    const mockDatos = {
      nombreConsulta: 'Control',
      monto: 150,
    };

    render(
      <Elements stripe={stripePromise}>
        <CheckoutForm
          datosConsulta={mockDatos}
          pagoId={123}
          onSuccess={() => {}}
        />
      </Elements>
    );

    const submitButton = screen.getByRole('button', { name: /Pagar/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(submitButton).toBeDisabled();
      expect(screen.getByText(/Procesando/i)).toBeInTheDocument();
    });
  });
});
```

---

## 📊 ENDPOINTS DEL BACKEND

### GET `/api/v1/pagos/stripe/clave-publica/`
**Respuesta:**
```json
{
  "publishable_key": "pk_test_51SGSX5RxIhITCnEh..."
}
```

### POST `/api/v1/pagos/stripe/crear-intencion-consulta/`
**Request:**
```json
{
  "tipo_consulta_id": 198,
  "monto": 150.00
}
```
**Respuesta:**
```json
{
  "client_secret": "pi_3SPRXy..._secret_abc123",
  "pago_id": 45,
  "codigo_pago": "CITA-A3B2C1D4",
  "monto": 150.00,
  "moneda": "bob"
}
```

### POST `/api/v1/pagos/stripe/confirmar-pago/`
**Request:**
```json
{
  "pago_id": 45
}
```
**Respuesta:**
```json
{
  "success": true,
  "mensaje": "Pago confirmado exitosamente",
  "pago": {
    "id": 45,
    "codigo_pago": "CITA-A3B2C1D4",
    "estado": "aprobado",
    "monto": 150.00
  }
}
```

### POST `/api/v1/citas/`
**Request:**
```json
{
  "fecha": "2025-11-20",
  "hora": "14:30",
  "motivo": "Control general",
  "tipo_consulta": 198,
  "pago_id": 45
}
```
**Respuesta:**
```json
{
  "id": 432,
  "fecha": "2025-11-20",
  "hora": "14:30",
  "estado": "programada",
  "pago_vinculado": true,
  "codigo_pago": "CITA-A3B2C1D4"
}
```

---

## 🚀 PASOS PARA IMPLEMENTAR

### Checklist de Implementación

- [ ] 1. Instalar dependencias npm
- [ ] 2. Configurar variables de entorno (.env)
- [ ] 3. Crear servicio `stripeService.ts`
- [ ] 4. Crear componente `FormularioCita.tsx`
- [ ] 5. Crear componente `CheckoutForm.tsx`
- [ ] 6. Crear página `AgendarCitaConPago.tsx`
- [ ] 7. Configurar rutas en router
- [ ] 8. Probar con tarjeta de prueba 4242 4242 4242 4242
- [ ] 9. Implementar manejo de errores
- [ ] 10. Escribir tests unitarios
- [ ] 11. Probar flujo completo end-to-end
- [ ] 12. Documentar para producción

---

## 🔒 SEGURIDAD

### ⚠️ IMPORTANTE - NO HACER:

1. **NUNCA** incluir `STRIPE_SECRET_KEY` en el frontend
2. **NUNCA** validar pagos solo del lado del cliente
3. **NUNCA** confiar en datos del frontend sin validación
4. **NUNCA** mostrar claves privadas en logs o consola

### ✅ MEJORES PRÁCTICAS:

1. Validar **SIEMPRE** en backend antes de crear la cita
2. Usar HTTPS en producción
3. Implementar rate limiting para prevenir abuso
4. Registrar intentos de pago en logs de auditoría
5. Notificar al usuario por email al confirmar pago

---

## 📞 SOPORTE

Si tienes problemas:
1. Verifica que el servidor Django esté corriendo en `http://localhost:8000`
2. Confirma que las claves de Stripe sean correctas (TEST mode)
3. Revisa la consola del navegador para errores
4. Verifica que el token de autenticación sea válido
5. Confirma que el tipo de consulta exista en la base de datos

**Documentación oficial:**
- [Stripe React Elements](https://stripe.com/docs/stripe-js/react)
- [Stripe Payment Intents](https://stripe.com/docs/payments/payment-intents)
- [Stripe Test Cards](https://stripe.com/docs/testing)

---

## 🎯 PRÓXIMOS PASOS

Después de implementar el flujo básico:

1. **Webhooks** - Recibir notificaciones asíncronas de Stripe
2. **Reembolsos** - Permitir cancelaciones con reembolso
3. **Historial de pagos** - Mostrar pagos anteriores del usuario
4. **Emails** - Enviar confirmaciones automáticas
5. **Modo producción** - Cambiar a claves LIVE de Stripe

---

## 📄 FACTURACIÓN ELECTRÓNICA

### 7.1 Modelos de Facturación Disponibles

El backend ya tiene implementados los siguientes modelos para facturación:

```python
# Modelos disponibles en apps/sistema_pagos/models.py
- Factura           # Encabezado de factura
- Itemdefactura     # Items/líneas de la factura
- Estadodefactura   # Estados: Pendiente, Pagada, Anulada, etc.
- Tipopago          # Tipos: Efectivo, Tarjeta, Transferencia, etc.
- Pago              # Registro de pagos vinculado a factura
```

### 7.2 Flujo de Facturación con Stripe

```typescript
// src/services/facturaService.ts
import api from './api';

export interface Factura {
  id: number;
  fechaemision: string;
  montototal: number;
  idestadofactura: number;
  estado_nombre?: string;
  items?: ItemFactura[];
  pagos?: PagoFactura[];
}

export interface ItemFactura {
  id?: number;
  descripcion: string;
  monto: number;
}

export interface PagoFactura {
  id?: number;
  montopagado: number;
  fechapago: string;
  idtipopago: number;
  codigo_pago_stripe?: string; // Vinculación con PagoEnLinea
}

class FacturaService {
  // Generar factura después de pago exitoso
  async generarFacturaDesdePago(pagoId: number): Promise<Factura> {
    const response = await api.post('/facturas/generar-desde-pago/', {
      pago_id: pagoId,
    });
    return response.data;
  }

  // Obtener factura por ID
  async obtenerFactura(facturaId: number): Promise<Factura> {
    const response = await api.get(`/facturas/${facturaId}/`);
    return response.data;
  }

  // Descargar PDF de factura
  async descargarFacturaPDF(facturaId: number): Promise<Blob> {
    const response = await api.get(`/facturas/${facturaId}/pdf/`, {
      responseType: 'blob',
    });
    return response.data;
  }

  // Enviar factura por email
  async enviarFacturaEmail(facturaId: number, email: string): Promise<void> {
    await api.post(`/facturas/${facturaId}/enviar-email/`, { email });
  }

  // Listar facturas del usuario
  async listarFacturas(): Promise<Factura[]> {
    const response = await api.get('/facturas/');
    return response.data.results || response.data;
  }
}

export default new FacturaService();
```

### 7.3 Componente de Factura

```tsx
// src/components/VistaFactura.tsx
import React, { useEffect, useState } from 'react';
import facturaService, { Factura } from '../services/facturaService';

interface Props {
  pagoId: number;
  onClose?: () => void;
}

const VistaFactura: React.FC<Props> = ({ pagoId, onClose }) => {
  const [factura, setFactura] = useState<Factura | null>(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    cargarFactura();
  }, [pagoId]);

  const cargarFactura = async () => {
    try {
      setCargando(true);
      const facturaGenerada = await facturaService.generarFacturaDesdePago(pagoId);
      setFactura(facturaGenerada);
    } catch (err: any) {
      setError(err.message || 'Error al cargar la factura');
    } finally {
      setCargando(false);
    }
  };

  const descargarPDF = async () => {
    if (!factura) return;
    
    try {
      const blob = await facturaService.descargarFacturaPDF(factura.id);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `factura-${factura.id}.pdf`;
      link.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert('Error al descargar la factura');
    }
  };

  const enviarPorEmail = async () => {
    if (!factura) return;
    
    const email = prompt('Ingresa el email donde deseas recibir la factura:');
    if (!email) return;

    try {
      await facturaService.enviarFacturaEmail(factura.id, email);
      alert(`Factura enviada a ${email}`);
    } catch (err) {
      alert('Error al enviar la factura por email');
    }
  };

  if (cargando) {
    return (
      <div className="text-center p-8">
        <div className="spinner-border" role="status">
          <span className="sr-only">Cargando...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
        {error}
      </div>
    );
  }

  if (!factura) return null;

  return (
    <div className="bg-white shadow-lg rounded-lg p-6 max-w-3xl mx-auto">
      {/* Encabezado */}
      <div className="border-b pb-4 mb-4">
        <div className="flex justify-between items-start">
          <div>
            <h2 className="text-2xl font-bold text-gray-800">FACTURA</h2>
            <p className="text-gray-600">Nº {factura.id.toString().padStart(6, '0')}</p>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-600">Fecha de Emisión</p>
            <p className="font-bold">{new Date(factura.fechaemision).toLocaleDateString('es-BO')}</p>
          </div>
        </div>
      </div>

      {/* Información de la Clínica */}
      <div className="mb-6">
        <h3 className="font-bold text-gray-800 mb-2">CLÍNICA DENTAL</h3>
        <p className="text-sm text-gray-600">NIT: 123456789</p>
        <p className="text-sm text-gray-600">Dirección: Av. Principal #123</p>
        <p className="text-sm text-gray-600">Teléfono: +591 12345678</p>
      </div>

      {/* Items de la Factura */}
      <div className="mb-6">
        <h3 className="font-bold text-gray-800 mb-3">DETALLE</h3>
        <table className="w-full">
          <thead className="bg-gray-100">
            <tr>
              <th className="text-left p-2">Descripción</th>
              <th className="text-right p-2">Monto</th>
            </tr>
          </thead>
          <tbody>
            {factura.items?.map((item, index) => (
              <tr key={index} className="border-b">
                <td className="p-2">{item.descripcion}</td>
                <td className="text-right p-2">Bs. {item.monto.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
          <tfoot className="bg-gray-50">
            <tr>
              <td className="p-2 font-bold text-right">TOTAL:</td>
              <td className="p-2 font-bold text-right text-xl">
                Bs. {factura.montototal.toFixed(2)}
              </td>
            </tr>
          </tfoot>
        </table>
      </div>

      {/* Estado de Pago */}
      <div className="mb-6">
        <h3 className="font-bold text-gray-800 mb-3">ESTADO DE PAGO</h3>
        <div className="bg-green-50 border border-green-200 rounded p-3">
          <p className="text-green-800">
            <strong>✓ PAGADO</strong> - {factura.estado_nombre}
          </p>
          {factura.pagos?.map((pago, index) => (
            <p key={index} className="text-sm text-gray-600 mt-1">
              Pago de Bs. {pago.montopagado.toFixed(2)} el{' '}
              {new Date(pago.fechapago).toLocaleDateString('es-BO')}
              {pago.codigo_pago_stripe && (
                <span className="ml-2 text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                  Stripe: {pago.codigo_pago_stripe}
                </span>
              )}
            </p>
          ))}
        </div>
      </div>

      {/* Acciones */}
      <div className="flex gap-3 pt-4 border-t">
        <button
          onClick={descargarPDF}
          className="flex-1 bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
        >
          📥 Descargar PDF
        </button>
        <button
          onClick={enviarPorEmail}
          className="flex-1 bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded"
        >
          📧 Enviar por Email
        </button>
        {onClose && (
          <button
            onClick={onClose}
            className="bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-2 px-4 rounded"
          >
            Cerrar
          </button>
        )}
      </div>

      {/* Nota Legal */}
      <div className="mt-6 pt-4 border-t text-xs text-gray-500 text-center">
        <p>Esta factura es válida sin firma ni sello</p>
        <p>Gracias por su preferencia</p>
      </div>
    </div>
  );
};

export default VistaFactura;
```

### 7.4 Integración con CheckoutForm

Modifica el componente `CheckoutForm.tsx` para mostrar la factura después del pago:

```tsx
// Agregar al CheckoutForm.tsx después de crear la cita exitosamente:

const handleSubmit = async (event: React.FormEvent) => {
  event.preventDefault();

  if (!stripe || !elements) {
    return;
  }

  setProcesando(true);
  setError(null);

  const cardElement = elements.getElement(CardElement);

  try {
    // 1. Confirmar pago con Stripe
    const { error: stripeError, paymentIntent } = await stripe.confirmCardPayment(
      datosConsulta.clientSecret,
      {
        payment_method: {
          card: cardElement!,
          billing_details: {
            name: datosConsulta.nombrePaciente || 'Paciente',
          },
        },
      }
    );

    if (stripeError) {
      throw new Error(stripeError.message);
    }

    if (paymentIntent.status === 'succeeded') {
      // 2. Confirmar en backend
      const confirmacion = await stripeService.confirmPayment(pagoId);

      if (confirmacion.success) {
        // 3. Crear la cita
        await api.post('/citas/', {
          fecha: datosConsulta.fecha,
          hora: datosConsulta.hora,
          motivo: datosConsulta.motivo,
          tipo_consulta: datosConsulta.tipoConsultaId,
          pago_id: pagoId,
        });

        // 4. NUEVO: Generar factura automáticamente
        const factura = await facturaService.generarFacturaDesdePago(pagoId);
        
        // 5. Pasar factura al componente padre
        onSuccess(factura);
      } else {
        throw new Error('Error al confirmar el pago en el servidor');
      }
    }
  } catch (err: any) {
    setError(err.message || 'Error al procesar el pago');
    console.error('Error en pago:', err);
  } finally {
    setProcesando(false);
  }
};
```

### 7.5 Actualizar AgendarCitaConPago

```tsx
// src/pages/AgendarCitaConPago.tsx
import React, { useState, useEffect } from 'react';
import { loadStripe } from '@stripe/stripe-js';
import { Elements } from '@stripe/react-stripe-js';
import FormularioCita from '../components/FormularioCita';
import CheckoutForm from '../components/CheckoutForm';
import VistaFactura from '../components/VistaFactura';
import stripeService from '../services/stripeService';

const AgendarCitaConPago: React.FC = () => {
  const [stripePromise, setStripePromise] = useState(null);
  const [paso, setPaso] = useState<'seleccion' | 'pago' | 'factura'>('seleccion');
  const [datosConsulta, setDatosConsulta] = useState(null);
  const [clientSecret, setClientSecret] = useState('');
  const [pagoId, setPagoId] = useState<number | null>(null);

  useEffect(() => {
    const initStripe = async () => {
      const publicKey = await stripeService.getPublishableKey();
      setStripePromise(loadStripe(publicKey));
    };
    initStripe();
  }, []);

  const handleSeleccionarConsulta = async (datos: any) => {
    setDatosConsulta(datos);
    
    try {
      const response = await stripeService.createPaymentIntent(
        datos.tipoConsultaId,
        datos.monto
      );
      
      setClientSecret(response.client_secret);
      setPagoId(response.pago_id);
      setPaso('pago');
    } catch (error) {
      console.error('Error al crear intención de pago:', error);
      alert('Error al iniciar el pago. Por favor intenta nuevamente.');
    }
  };

  const handlePagoExitoso = (factura: any) => {
    setDatosConsulta({ ...datosConsulta, factura });
    setPaso('factura');
  };

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Agendar Cita con Pago</h1>

      {/* Paso 1: Seleccionar consulta */}
      {paso === 'seleccion' && (
        <FormularioCita onSubmit={handleSeleccionarConsulta} />
      )}

      {/* Paso 2: Realizar pago */}
      {paso === 'pago' && stripePromise && clientSecret && (
        <Elements stripe={stripePromise} options={{ clientSecret }}>
          <CheckoutForm
            datosConsulta={datosConsulta}
            pagoId={pagoId}
            onSuccess={handlePagoExitoso}
          />
        </Elements>
      )}

      {/* Paso 3: Mostrar Factura */}
      {paso === 'factura' && pagoId && (
        <div>
          <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-6">
            <h2 className="text-xl font-bold mb-2">✅ ¡Pago Exitoso!</h2>
            <p>Tu cita ha sido agendada correctamente.</p>
          </div>
          <VistaFactura
            pagoId={pagoId}
            onClose={() => window.location.href = '/mis-citas'}
          />
        </div>
      )}
    </div>
  );
};

export default AgendarCitaConPago;
```

### 7.6 Historial de Facturas

```tsx
// src/pages/MisFacturas.tsx
import React, { useEffect, useState } from 'react';
import facturaService, { Factura } from '../services/facturaService';

const MisFacturas: React.FC = () => {
  const [facturas, setFacturas] = useState<Factura[]>([]);
  const [cargando, setCargando] = useState(true);

  useEffect(() => {
    cargarFacturas();
  }, []);

  const cargarFacturas = async () => {
    try {
      const lista = await facturaService.listarFacturas();
      setFacturas(lista);
    } catch (error) {
      console.error('Error al cargar facturas:', error);
    } finally {
      setCargando(false);
    }
  };

  const descargarPDF = async (facturaId: number) => {
    try {
      const blob = await facturaService.descargarFacturaPDF(facturaId);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `factura-${facturaId}.pdf`;
      link.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert('Error al descargar la factura');
    }
  };

  if (cargando) {
    return <div className="text-center p-8">Cargando facturas...</div>;
  }

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Mis Facturas</h1>

      {facturas.length === 0 ? (
        <div className="bg-gray-100 p-8 rounded text-center">
          <p className="text-gray-600">No tienes facturas aún</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {facturas.map((factura) => (
            <div
              key={factura.id}
              className="bg-white shadow rounded-lg p-4 flex justify-between items-center"
            >
              <div>
                <h3 className="font-bold text-lg">
                  Factura Nº {factura.id.toString().padStart(6, '0')}
                </h3>
                <p className="text-gray-600">
                  {new Date(factura.fechaemision).toLocaleDateString('es-BO')}
                </p>
                <p className="text-sm text-gray-500">{factura.estado_nombre}</p>
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold text-gray-800">
                  Bs. {factura.montototal.toFixed(2)}
                </p>
                <button
                  onClick={() => descargarPDF(factura.id)}
                  className="mt-2 bg-blue-500 hover:bg-blue-700 text-white text-sm font-bold py-1 px-3 rounded"
                >
                  📥 Descargar PDF
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default MisFacturas;
```

### 7.7 Backend - Endpoints Necesarios

**IMPORTANTE**: Debes implementar estos endpoints en el backend Django:

```python
# apps/sistema_pagos/views.py

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Factura, Itemdefactura, PagoEnLinea, Pago

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generar_factura_desde_pago(request):
    """Genera una factura a partir de un pago en línea exitoso"""
    pago_id = request.data.get('pago_id')
    
    # Obtener pago
    pago_online = PagoEnLinea.objects.get(id=pago_id, estado='aprobado')
    
    # Crear factura
    factura = Factura.objects.create(
        fechaemision=timezone.now().date(),
        montototal=pago_online.monto,
        idestadofactura_id=1  # Estado "Pagada"
    )
    
    # Crear item de factura
    Itemdefactura.objects.create(
        idfactura=factura,
        descripcion=pago_online.descripcion,
        monto=pago_online.monto
    )
    
    # Vincular pago tradicional
    Pago.objects.create(
        idfactura=factura,
        idtipopago_id=2,  # Tipo "Tarjeta"
        montopagado=pago_online.monto,
        fechapago=timezone.now().date()
    )
    
    serializer = FacturaSerializer(factura)
    return Response(serializer.data, status=201)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def descargar_factura_pdf(request, factura_id):
    """Genera y descarga PDF de factura"""
    from django.http import HttpResponse
    from reportlab.pdfgen import canvas
    
    factura = Factura.objects.get(id=factura_id)
    
    # Crear PDF (simplificado)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="factura-{factura_id}.pdf"'
    
    p = canvas.Canvas(response)
    p.drawString(100, 800, f"FACTURA Nº {factura.id}")
    p.drawString(100, 780, f"Fecha: {factura.fechaemision}")
    p.drawString(100, 760, f"Total: Bs. {factura.montototal}")
    p.showPage()
    p.save()
    
    return response
```

### 7.8 Resumen de Facturación

**Flujo Completo:**
1. ✅ Usuario paga con Stripe
2. ✅ Backend confirma pago (`estado='aprobado'`)
3. ✅ Frontend solicita generar factura
4. ✅ Backend crea `Factura` + `Itemdefactura` + `Pago`
5. ✅ Frontend muestra factura
6. ✅ Usuario puede descargar PDF o enviar por email

**Ventajas:**
- ✅ Facturación automática post-pago
- ✅ Historial completo de facturas
- ✅ Descarga en PDF
- ✅ Envío por email
- ✅ Integración con sistema contable

---

✅ **BACKEND LISTO** | 🚀 **FRONTEND POR IMPLEMENTAR** | 📄 **FACTURACIÓN INCLUIDA**
