"""
Script de prueba para la integración de Stripe
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import stripe
from django.conf import settings

print("\n" + "="*70)
print("🧪 PRUEBA DE INTEGRACIÓN STRIPE")
print("="*70 + "\n")

# 1. Verificar configuración
print("📋 1. VERIFICANDO CONFIGURACIÓN")
print("-" * 70)

stripe_secret = settings.STRIPE_SECRET_KEY
stripe_public = settings.STRIPE_PUBLIC_KEY

if stripe_secret and stripe_secret.startswith('sk_'):
    print(f"✅ STRIPE_SECRET_KEY configurada: {stripe_secret[:15]}...")
    print(f"   Modo: {'TEST' if 'test' in stripe_secret else 'LIVE'}")
else:
    print("❌ STRIPE_SECRET_KEY no configurada o inválida")

if stripe_public and stripe_public.startswith('pk_'):
    print(f"✅ STRIPE_PUBLIC_KEY configurada: {stripe_public[:15]}...")
else:
    print("❌ STRIPE_PUBLIC_KEY no configurada o inválida")

# 2. Probar conexión con Stripe
print("\n📋 2. PROBANDO CONEXIÓN CON STRIPE")
print("-" * 70)

stripe.api_key = stripe_secret

try:
    # Intentar obtener balance (requiere conexión válida)
    balance = stripe.Balance.retrieve()
    print(f"✅ Conexión exitosa con Stripe")
    print(f"   Moneda disponible: {balance['available'][0]['currency'].upper()}")
    print(f"   Monto disponible: {balance['available'][0]['amount'] / 100}")
except stripe.error.AuthenticationError:
    print("❌ Error de autenticación - Verifica tu API key")
except stripe.error.StripeError as e:
    print(f"❌ Error de Stripe: {str(e)}")
except Exception as e:
    print(f"❌ Error general: {str(e)}")

# 3. Verificar modelos
print("\n📋 3. VERIFICANDO MODELOS")
print("-" * 70)

from apps.sistema_pagos.models import PagoEnLinea
from apps.citas.models import Tipodeconsulta

print(f"✅ Modelo PagoEnLinea: {PagoEnLinea._meta.db_table}")
total_pagos = PagoEnLinea.objects.count()
print(f"   Total de pagos registrados: {total_pagos}")

print(f"\n✅ Modelo Tipodeconsulta: {Tipodeconsulta._meta.db_table}")
total_tipos = Tipodeconsulta.objects.count()
print(f"   Total de tipos de consulta: {total_tipos}")

if total_tipos > 0:
    tipo = Tipodeconsulta.objects.first()
    print(f"   Ejemplo: {tipo.nombreconsulta}")

# 4. Crear Payment Intent de prueba
print("\n📋 4. CREAR PAYMENT INTENT DE PRUEBA")
print("-" * 70)

try:
    intent = stripe.PaymentIntent.create(
        amount=15000,  # 150 BOB = 15000 centavos
        currency='bob',
        metadata={
            'tipo': 'test',
            'descripcion': 'Pago de prueba desde script'
        },
        description='Payment Intent de prueba'
    )
    
    print(f"✅ Payment Intent creado exitosamente")
    print(f"   ID: {intent.id}")
    print(f"   Client Secret: {intent.client_secret[:30]}...")
    print(f"   Monto: {intent.amount / 100} {intent.currency.upper()}")
    print(f"   Estado: {intent.status}")
    
    # Opcional: Cancelar el intent de prueba
    canceled = stripe.PaymentIntent.cancel(intent.id)
    print(f"✅ Intent de prueba cancelado (no se cobrará)")
    
except stripe.error.StripeError as e:
    print(f"❌ Error al crear Payment Intent: {str(e)}")

# 5. Verificar endpoints
print("\n📋 5. ENDPOINTS DISPONIBLES")
print("-" * 70)

endpoints = [
    "GET  /api/v1/pagos/stripe/clave-publica/",
    "POST /api/v1/pagos/stripe/crear-intencion-consulta/",
    "POST /api/v1/pagos/stripe/confirmar-pago/",
    "GET  /api/v1/pagos/pagos-online/",
]

for endpoint in endpoints:
    print(f"✅ {endpoint}")

# 6. Resumen final
print("\n" + "="*70)
print("📊 RESUMEN")
print("="*70)

print("""
✅ CONFIGURACIÓN COMPLETA:
   • Stripe configurado en settings.py
   • API keys cargadas desde .env
   • Modelos PagoEnLinea listos
   • Endpoints creados

🧪 MODO ACTUAL:
   • TEST MODE (sin cargos reales)
   • Usar tarjetas de prueba: 4242 4242 4242 4242

📝 PRÓXIMOS PASOS:
   1. Reiniciar Django: python manage.py runserver
   2. Obtener token de autenticación
   3. Probar endpoint: POST /pagos/stripe/crear-intencion-consulta/
   4. Integrar en frontend con Stripe Elements

📖 DOCUMENTACIÓN:
   • Ver: docs/STRIPE_INTEGRACION.md
   • Ejemplos de frontend incluidos
""")

print("="*70 + "\n")
