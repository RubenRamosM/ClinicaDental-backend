# Integración de Stripe para Pago de Presupuestos/Tratamientos

## ✅ Funcionalidad Implementada

Se ha agregado integración completa de Stripe para permitir el pago de **presupuestos/tratamientos** mediante tarjeta de crédito/débito.

## 🔧 Endpoints Nuevos

### 1. Crear Payment Intent para Presupuesto

```http
POST /api/v1/pagos/stripe/crear-intencion-presupuesto/
Authorization: Token {token}
Content-Type: application/json

{
  "presupuesto_id": 123,
  "monto": 1500.00  // Opcional, si no se envía usa el total del presupuesto
}
```

**Response (201):**
```json
{
  "client_secret": "pi_xxx_secret_xxx",
  "pago_id": 456,
  "codigo_pago": "PRES-XXXXXXXX",
  "monto": 1500.00,
  "moneda": "BOB",
  "presupuesto": {
    "id": 123,
    "codigo": "PRES-2025-001",
    "total": 1500.00,
    "estado": "pendiente"
  }
}
```

**Validaciones:**
- ✅ El presupuesto debe existir
- ✅ El presupuesto debe estar en estado `pendiente` o `aprobado`
- ✅ El monto no puede ser mayor al total del presupuesto
- ✅ Crea registro en `PagoEnLinea` con estado `pendiente`
- ✅ Genera Payment Intent real en Stripe

### 2. Confirmar Pago de Presupuesto

```http
POST /api/v1/pagos/stripe/confirmar-pago-presupuesto/
Authorization: Token {token}
Content-Type: application/json

{
  "pago_id": 456,
  "presupuesto_id": 123,
  "payment_intent_id": "pi_xxx"  // Opcional
}
```

**Response (200):**
```json
{
  "success": true,
  "pago": {
    "id": 456,
    "codigo_pago": "PRES-XXXXXXXX",
    "monto": "1500.00",
    "estado": "aprobado",
    "stripe_payment_intent_id": "pi_xxx",
    ...
  },
  "presupuesto": {
    "id": 123,
    "codigo": "PRES-2025-001",
    "estado": "aprobado",
    "total": 1500.00
  },
  "mensaje": "Pago confirmado exitosamente. El presupuesto ha sido aprobado."
}
```

**Proceso automático:**
1. ✅ Verifica el estado del Payment Intent en Stripe
2. ✅ Si el pago fue exitoso (`succeeded`):
   - Actualiza `PagoEnLinea.estado` a `aprobado`
   - Guarda el `charge_id` de Stripe
   - **Aprueba automáticamente el presupuesto** (cambia estado a `aprobado`)

## 📋 Modelo de Datos

### PagoEnLinea

Los pagos de presupuestos se registran con:

```python
{
  "codigo_pago": "PRES-XXXXXXXX",        # Código único
  "origen_tipo": "plan_completo",        # Indica que es un presupuesto
  "monto": 1500.00,                      # Monto pagado
  "moneda": "BOB",                       # Bolivianos
  "estado": "pendiente" | "aprobado",    # Estado del pago
  "metodo_pago": "tarjeta",              # Siempre tarjeta para Stripe
  "stripe_payment_intent_id": "pi_xxx",  # ID del Payment Intent
  "stripe_charge_id": "ch_xxx",          # ID del cargo (después de confirmar)
  "stripe_metadata": {                   # Metadata adicional
    "presupuesto_id": 123,
    "presupuesto_codigo": "PRES-2025-001",
    "total_presupuesto": "1500.00"
  },
  "descripcion": "Pago presupuesto: PRES-2025-001 - Total: Bs. 1500.00"
}
```

## 🔄 Flujo de Pago Completo

### Frontend (React/Next.js)

```javascript
// 1. Paciente selecciona presupuesto a pagar
const presupuesto = await fetch('/api/v1/tratamientos/presupuestos/123');

// 2. Crear Payment Intent
const response = await fetch('/api/v1/pagos/stripe/crear-intencion-presupuesto/', {
  method: 'POST',
  headers: {
    'Authorization': `Token ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    presupuesto_id: presupuesto.id,
    monto: presupuesto.total  // O monto parcial
  })
});

const { client_secret, pago_id, presupuesto_id } = await response.json();

// 3. Procesar pago con Stripe.js
const stripe = await loadStripe(STRIPE_PUBLIC_KEY);
const { error, paymentIntent } = await stripe.confirmCardPayment(client_secret, {
  payment_method: {
    card: cardElement,
    billing_details: {
      name: 'Ana López',
      email: 'ana.lopez@email.com'
    }
  }
});

if (error) {
  console.error('Error en pago:', error);
  return;
}

// 4. Confirmar pago en backend
const confirmResponse = await fetch('/api/v1/pagos/stripe/confirmar-pago-presupuesto/', {
  method: 'POST',
  headers: {
    'Authorization': `Token ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    pago_id: pago_id,
    presupuesto_id: presupuesto_id,
    payment_intent_id: paymentIntent.id
  })
});

const result = await confirmResponse.json();
if (result.success) {
  alert('¡Pago exitoso! El presupuesto ha sido aprobado.');
  // Redirigir a página de confirmación
}
```

## 🧪 Testing

### Pruebas con archivo .http

Ver archivo `test_stripe_presupuestos.http` para pruebas completas.

### Pruebas E2E (Python)

Crear `flujo_10_stripe_presupuestos.py` similar a `flujo_09_stripe.py`:

```python
def crear_intencion_presupuesto(token, presupuesto_id):
    """Crear Payment Intent para presupuesto."""
    url = f"{BASE_URL}/api/v1/pagos/stripe/crear-intencion-presupuesto/"
    headers = {"Authorization": f"Token {token}"}
    payload = {
        "presupuesto_id": presupuesto_id,
        "monto": 500.00
    }
    
    response = requests.post(url, json=payload, headers=headers)
    data = response.json()
    
    return data.get('pago_id'), data.get('client_secret')

def confirmar_pago_presupuesto(token, pago_id, presupuesto_id):
    """Confirmar pago (simulado para testing)."""
    # En testing, marcar como aprobado directamente en BD
    # En producción, esto lo hace Stripe
    pago = PagoEnLinea.objects.get(id=pago_id)
    pago.estado = 'aprobado'
    pago.save()
    
    # Confirmar en API
    url = f"{BASE_URL}/api/v1/pagos/stripe/confirmar-pago-presupuesto/"
    headers = {"Authorization": f"Token {token}"}
    payload = {
        "pago_id": pago_id,
        "presupuesto_id": presupuesto_id
    }
    
    response = requests.post(url, json=payload, headers=headers)
    return response.json()
```

## 🔐 Seguridad

### Validaciones Implementadas

1. ✅ **Autenticación requerida**: `@permission_classes([IsAuthenticated])`
2. ✅ **Validación de presupuesto**: Debe existir y estar en estado válido
3. ✅ **Validación de monto**: No puede exceder el total del presupuesto
4. ✅ **Verificación con Stripe**: Confirma estado real del pago antes de aprobar
5. ✅ **Metadata de trazabilidad**: Guarda info del presupuesto en Stripe

### Permisos

- **Crear Payment Intent**: Cualquier usuario autenticado
- **Confirmar Pago**: Cualquier usuario autenticado (pero debe tener el `pago_id`)
- **Ver Pagos**: Pacientes ven solo sus pagos, Admin ve todos

## 📊 Diferencias con Pago de Consultas

| Característica | Consultas | Presupuestos |
|---------------|-----------|--------------|
| Endpoint crear | `/stripe/crear-intencion-consulta/` | `/stripe/crear-intencion-presupuesto/` |
| Endpoint confirmar | `/stripe/confirmar-pago/` | `/stripe/confirmar-pago-presupuesto/` |
| Código de pago | `CITA-XXXXXXXX` | `PRES-XXXXXXXX` |
| origen_tipo | `consulta` | `plan_completo` |
| Acción al confirmar | Crea consulta | Aprueba presupuesto |
| Monto por defecto | Del tipo de consulta | Total del presupuesto |

## 🎯 Casos de Uso

### CU20: Generar y Pagar Presupuesto

1. Odontólogo crea presupuesto para paciente
2. Presupuesto queda en estado `pendiente`
3. Paciente ve presupuesto en su portal
4. Paciente selecciona "Pagar con tarjeta"
5. Sistema crea Payment Intent en Stripe
6. Paciente ingresa datos de tarjeta
7. Stripe procesa el pago
8. Backend confirma pago y aprueba presupuesto automáticamente
9. Paciente recibe confirmación

### CU21: Pago Parcial de Presupuesto

1. Presupuesto total: Bs. 1500
2. Paciente paga Bs. 500 como anticipo
3. Se registra pago parcial
4. Presupuesto se aprueba
5. Saldo pendiente: Bs. 1000 (manejado por sistema de pagos interno)

## 📝 Próximos Pasos

- [ ] Implementar webhook de Stripe para confirmaciones automáticas
- [ ] Agregar soporte para pagos parciales múltiples
- [ ] Vincular pagos con el sistema interno de cuotas
- [ ] Generar PDF de recibo de pago
- [ ] Enviar email de confirmación al paciente
- [ ] Implementar reembolsos desde panel admin

## 🐛 Solución de Problemas

### Error: "No se puede pagar un presupuesto en estado: rechazado"
- **Causa**: Solo se pueden pagar presupuestos pendientes o aprobados
- **Solución**: Verificar estado del presupuesto antes de intentar pagar

### Error: "El monto a pagar no puede ser mayor al total"
- **Causa**: Intentando pagar más del total del presupuesto
- **Solución**: Ajustar monto o usar monto total automáticamente

### Payment Intent created pero pago no confirmado
- **Causa**: Falta llamar al endpoint de confirmación
- **Solución**: Siempre confirmar después de que Stripe procese el pago

## 📚 Referencias

- [Stripe Payment Intents API](https://stripe.com/docs/payments/payment-intents)
- [Stripe.js Reference](https://stripe.com/docs/js)
- [Guía de Testing Stripe](https://stripe.com/docs/testing)
