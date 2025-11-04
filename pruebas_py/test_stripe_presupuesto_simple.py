"""
FLUJO 10: Prueba simple de Payment Intent para Presupuestos
Test rápido de integración de Stripe con presupuestos
"""
import requests

BASE_URL = "http://localhost:8000"

# 1. Login
print("\n1. Login paciente...")
response = requests.post(f"{BASE_URL}/api/v1/auth/login/", json={
    "correo": "ana.lopez@email.com",
    "password": "paciente123"
})
token = response.json()['token']
print(f"✓ Token: {token[:20]}...")

# 2. Listar presupuestos
print("\n2. Listar presupuestos...")
headers = {"Authorization": f"Token {token}"}
response = requests.get(f"{BASE_URL}/api/v1/tratamientos/presupuestos/", headers=headers)
presupuestos = response.json().get('results', [])
print(f"✓ Total presupuestos: {len(presupuestos)}")

if presupuestos:
    presupuesto = presupuestos[0]
    presupuesto_id = presupuesto['id']
    print(f"  Usando presupuesto ID: {presupuesto_id}, Total: {presupuesto.get('total', 0)}")
    
    # 3. Crear Payment Intent
    print("\n3. Crear Payment Intent...")
    monto_a_pagar = min(400.00, float(presupuesto.get('total', 400)))  # Usar monto válido
    response = requests.post(
        f"{BASE_URL}/api/v1/pagos/stripe/crear-intencion-presupuesto/",
        json={"presupuesto_id": presupuesto_id, "monto": monto_a_pagar},
        headers=headers
    )
    
    if response.status_code == 201:
        data = response.json()
        print(f"✓ Payment Intent creado")
        print(f"  Pago ID: {data['pago_id']}")
        print(f"  Código: {data['codigo_pago']}")
        print(f"  Monto: Bs. {data['monto']}")
        
        #  4. Simular aprobación (actualizar BD)
        print("\n4. Simular aprobación de pago...")
        import os, sys, django
        sys.path.insert(0, '..')
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
        django.setup()
        
        from apps.sistema_pagos.models import PagoEnLinea
        pago = PagoEnLinea.objects.get(id=data['pago_id'])
        pago.estado = 'aprobado'
        pago.save()
        print(f"✓ Pago marcado como aprobado")
        
        # 5. Confirmar pago
        print("\n5. Confirmar pago...")
        response = requests.post(
            f"{BASE_URL}/api/v1/pagos/stripe/confirmar-pago-presupuesto/",
            json={
                "pago_id": data['pago_id'],
                "presupuesto_id": presupuesto_id
            },
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Pago confirmado")
            print(f"  Presupuesto estado: {result['presupuesto']['estado']}")
            print(f"  Mensaje: {result['mensaje']}")
        else:
            print(f"✗ Error al confirmar: {response.status_code}")
            print(f"  {response.text}")
    else:
        print(f"✗ Error al crear Payment Intent: {response.status_code}")
        print(f"  {response.text}")
else:
    print("✗ No hay presupuestos. Necesitas crear uno primero.")
    print("\nCreando presupuesto de prueba...")
    
    # Login admin para crear presupuesto
    response = requests.post(f"{BASE_URL}/api/v1/auth/login/", json={
        "correo": "admin@clinica.com",
        "password": "admin123"
    })
    admin_token = response.json()['token']
    admin_headers = {"Authorization": f"Token {admin_token}"}
    
    # Obtener IDs necesarios
    import os, sys, django
    sys.path.insert(0, '..')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()
    
    from apps.usuarios.models import Paciente, Odontologo
    from apps.tratamientos.models import Plantratamiento, Presupuesto, ItemPresupuesto
    from apps.administracion_clinica.models import Tratamiento
    
    paciente = Paciente.objects.first()
    odontologo = Odontologo.objects.first()
    
    # Crear plan de tratamiento
    plan = Plantratamiento.objects.create(
        codpaciente=paciente,
        cododontologo=odontologo,
        diagnostico="Plan de prueba para Stripe",
        estado="activo"
    )
    
    # Crear presupuesto
    presupuesto = Presupuesto.objects.create(
        plan_tratamiento=plan,
        notas="Presupuesto de prueba E2E",
        condiciones="Válido 30 días"
    )
    
    # Agregar items
    tratamientos = Tratamiento.objects.all()[:2]
    for i, trat in enumerate(tratamientos):
        ItemPresupuesto.objects.create(
            presupuesto=presupuesto,
            tratamiento=trat,
            descripcion=trat.nombre,
            cantidad=1,
            precio_unitario=250 + (i * 100),
            descuento=0
        )
    
    # Calcular total
    from decimal import Decimal
    total = sum(item.subtotal for item in presupuesto.items.all())
    presupuesto.subtotal = total
    presupuesto.total = total
    presupuesto.save()
    
    print(f"✓ Presupuesto creado: ID {presupuesto.id}, Total: Bs. {total}")
    print("\n🔄 Ejecuta este script de nuevo para probarlo")

print("\n" + "=" * 60)
print("FIN DEL FLUJO 10")
print("=" * 60)
