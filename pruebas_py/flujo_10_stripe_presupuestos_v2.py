"""
FLUJO 10: PRUEBAS DE INTEGRACION CON STRIPE - PRESUPUESTOS
===========================================================
Este flujo prueba el sistema de pagos de presupuestos con Stripe:
1. Autenticacion de usuarios (admin, paciente)
2. Listar presupuestos pendientes/aprobados
3. Crear Payment Intent en Stripe para presupuesto
4. Simular confirmación de pago
5. Confirmar pago y aprobar presupuesto
6. Verificar que presupuesto fue aprobado
7. Listar pagos del paciente
"""

import requests
import sys
import os
import django
from decimal import Decimal

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from json_output_helper import crear_reporte_json
from http_logger import (
    print_http_transaction,
    print_seccion,
    print_exito,
    print_error,
    print_info
)

BASE_URL = "http://localhost:8000"


def autenticar_usuarios():
    """Autenticar admin y paciente."""
    print("\n=== SECCION 1: AUTENTICACION DE USUARIOS ===")
    
    # Login como admin
    payload_admin = {
        "correo": "admin@clinica.com",
        "password": "admin123"
    }
    
    url = f"{BASE_URL}/api/v1/auth/login/"
    
    print("\n[1.1] Login como Administrador")
    print_http_transaction(
        metodo="POST",
        url=url,
        body=payload_admin,
        descripcion="Login como administrador"
    )
    
    response_admin = requests.post(url, json=payload_admin)
    
    print_http_transaction(
        metodo="POST",
        url=url,
        body=payload_admin,
        response_status=response_admin.status_code,
        response_body=response_admin.json() if response_admin.status_code == 200 else response_admin.text,
        descripcion="Respuesta login admin"
    )
    
    if response_admin.status_code != 200:
        print("✗ Error en autenticacion de admin")
        return False, None, None
    
    admin_token = response_admin.json().get('token')
    print(f"✓ Admin autenticado")
    
    # Login como paciente
    payload_paciente = {
        "correo": "ana.lopez@email.com",
        "password": "paciente123"
    }
    
    print("\n[1.2] Login como Paciente")
    print_http_transaction(
        metodo="POST",
        url=url,
        body=payload_paciente,
        descripcion="Login como paciente"
    )
    
    response_paciente = requests.post(url, json=payload_paciente)
    
    print_http_transaction(
        metodo="POST",
        url=url,
        body=payload_paciente,
        response_status=response_paciente.status_code,
        response_body=response_paciente.json() if response_paciente.status_code == 200 else response_paciente.text,
        descripcion="Respuesta login paciente"
    )
    
    if response_paciente.status_code != 200:
        print("✗ Error en autenticacion de paciente")
        return False, admin_token, None
    
    paciente_token = response_paciente.json().get('token')
    paciente_id = response_paciente.json()['usuario']['codigo']
    print(f"✓ Paciente autenticado (ID: {paciente_id})")
    
    return True, admin_token, paciente_token


def listar_presupuestos(token):
    """Listar presupuestos del paciente."""
    print("\n=== SECCION 2: LISTAR PRESUPUESTOS ===")
    
    url = f"{BASE_URL}/api/v1/tratamientos/presupuestos/"
    headers = {"Authorization": f"Token {token}"}
    
    print_http_transaction(
        metodo="GET",
        url=url,
        headers=headers,
        descripcion="Listar presupuestos"
    )
    
    response = requests.get(url, headers=headers)
    
    print_http_transaction(
        metodo="GET",
        url=url,
        headers=headers,
        response_status=response.status_code,
        response_body=response.json() if response.status_code == 200 else response.text,
        descripcion="Respuesta - Presupuestos"
    )
    
    if response.status_code != 200:
        print("✗ Error al listar presupuestos")
        return False, None
    
    presupuestos = response.json().get('results', [])
    print(f"✓ Se encontraron {len(presupuestos)} presupuestos")
    
    # Buscar presupuesto pendiente o aprobado
    presupuesto_seleccionado = None
    for presup in presupuestos:
        if presup.get('estado') in ['pendiente', 'aprobado']:
            presupuesto_seleccionado = presup
            break
    
    if presupuesto_seleccionado:
        print(f"  Presupuesto seleccionado: ID {presupuesto_seleccionado['id']}, Total: Bs. {presupuesto_seleccionado['total']}")
        return True, presupuesto_seleccionado
    else:
        print("✗ No hay presupuestos pendientes/aprobados disponibles")
        return False, None


def crear_payment_intent_presupuesto(token, presupuesto_id, monto):
    """Crear Payment Intent para presupuesto en Stripe."""
    print("\n=== SECCION 3: CREAR PAYMENT INTENT PARA PRESUPUESTO ===")
    
    url = f"{BASE_URL}/api/v1/pagos/stripe/crear-intencion-presupuesto/"
    headers = {"Authorization": f"Token {token}"}
    
    payload = {
        "presupuesto_id": presupuesto_id,
        "monto": monto
    }
    
    print_http_transaction(
        metodo="POST",
        url=url,
        headers=headers,
        body=payload,
        descripcion="Crear Payment Intent para presupuesto"
    )
    
    response = requests.post(url, json=payload, headers=headers)
    
    print_http_transaction(
        metodo="POST",
        url=url,
        headers=headers,
        body=payload,
        response_status=response.status_code,
        response_body=response.json() if response.status_code == 201 else response.text,
        descripcion="Respuesta - Payment Intent creado"
    )
    
    if response.status_code != 201:
        print("✗ Error al crear Payment Intent")
        return False, None, None, None
    
    data = response.json()
    pago_id = data.get('pago_id')
    codigo_pago = data.get('codigo_pago')
    client_secret = data.get('client_secret')
    
    print(f"✓ Payment Intent creado exitosamente")
    print(f"  Codigo Pago: {codigo_pago}")
    print(f"  Pago ID (DB): {pago_id}")
    print(f"  Client Secret: {client_secret[:30]}...")
    
    return True, pago_id, codigo_pago, client_secret


def marcar_pago_aprobado(pago_id):
    """Marcar pago como aprobado en la base de datos (simulación)."""
    print("\n=== SECCION 4: SIMULAR CONFIRMACION DE PAGO ===")
    print("NOTA: En produccion, el frontend procesaria el pago con Stripe.js")
    print("Para pruebas E2E, marcaremos el pago como aprobado manualmente en la BD")
    
    from apps.sistema_pagos.models import PagoEnLinea
    
    try:
        pago = PagoEnLinea.objects.get(id=pago_id)
        pago.estado = 'aprobado'
        pago.save()
        print(f"✓ Pago marcado como aprobado (ID: {pago_id})")
        return True
    except Exception as e:
        print(f"✗ Error al marcar pago: {str(e)}")
        return False


def confirmar_pago_presupuesto(token, pago_id, payment_intent_id):
    """Confirmar pago de presupuesto y aprobar presupuesto."""
    print("\n=== SECCION 5: CONFIRMAR PAGO Y APROBAR PRESUPUESTO ===")
    
    url = f"{BASE_URL}/api/v1/pagos/stripe/confirmar-pago-presupuesto/"
    headers = {"Authorization": f"Token {token}"}
    
    payload = {
        "pago_id": pago_id,
        "payment_intent_id": payment_intent_id
    }
    
    print_http_transaction(
        metodo="POST",
        url=url,
        headers=headers,
        body=payload,
        descripcion="Confirmar pago de presupuesto"
    )
    
    response = requests.post(url, json=payload, headers=headers)
    
    print_http_transaction(
        metodo="POST",
        url=url,
        headers=headers,
        body=payload,
        response_status=response.status_code,
        response_body=response.json() if response.status_code == 200 else response.text,
        descripcion="Respuesta - Pago confirmado"
    )
    
    if response.status_code != 200:
        print("✗ Error al confirmar pago")
        return False, None
    
    data = response.json()
    presupuesto_id = data.get('presupuesto', {}).get('id')
    presupuesto_estado = data.get('presupuesto', {}).get('estado')
    
    print(f"✓ Pago confirmado y presupuesto aprobado")
    print(f"  Presupuesto ID: {presupuesto_id}")
    print(f"  Estado: {presupuesto_estado}")
    
    return True, presupuesto_id


def verificar_aprobacion_presupuesto(token, presupuesto_id):
    """Verificar que el presupuesto fue aprobado."""
    print("\n=== SECCION 6: VERIFICAR APROBACION DE PRESUPUESTO ===")
    
    print("\n[6.1] Verificar datos del presupuesto")
    
    url = f"{BASE_URL}/api/v1/tratamientos/presupuestos/{presupuesto_id}/"
    headers = {"Authorization": f"Token {token}"}
    
    print_http_transaction(
        metodo="GET",
        url=url,
        headers=headers,
        descripcion="Obtener detalles de presupuesto"
    )
    
    response = requests.get(url, headers=headers)
    
    print_http_transaction(
        metodo="GET",
        url=url,
        headers=headers,
        response_status=response.status_code,
        response_body=response.json() if response.status_code == 200 else response.text,
        descripcion="Respuesta - Presupuesto"
    )
    
    if response.status_code != 200:
        print("✗ Error al obtener presupuesto")
        return False
    
    presupuesto = response.json()
    estado = presupuesto.get('estado')
    
    print(f"✓ Presupuesto obtenido - Estado: {estado}")
    
    if estado == 'aprobado':
        print("✓ Presupuesto correctamente aprobado")
        return True
    else:
        print(f"✗ Presupuesto NO está aprobado (estado: {estado})")
        return False


def listar_pagos(token):
    """Listar pagos en línea."""
    print("\n=== SECCION 7: LISTAR PAGOS EN LINEA ===")
    
    url = f"{BASE_URL}/api/v1/pagos/pagos-online/"
    headers = {"Authorization": f"Token {token}"}
    
    print_http_transaction(
        metodo="GET",
        url=url,
        headers=headers,
        descripcion="Listar pagos en linea"
    )
    
    response = requests.get(url, headers=headers)
    
    print_http_transaction(
        metodo="GET",
        url=url,
        headers=headers,
        response_status=response.status_code,
        response_body=response.json() if response.status_code == 200 else response.text,
        descripcion="Respuesta - Lista de pagos"
    )
    
    if response.status_code != 200:
        print("✗ Error al listar pagos")
        return False
    
    data = response.json()
    pagos = data.get('results', [])
    total_pagos = data.get('count', 0)
    
    print(f"✓ Se encontraron {total_pagos} pagos en linea")
    
    if pagos:
        print("\nUltimos 3 pagos:")
        for pago in pagos[:3]:
            codigo = pago.get('codigo_pago')
            monto = pago.get('monto')
            estado = pago.get('estado')
            origen = pago.get('origen_tipo')
            print(f"  - {codigo}: Bs. {monto} - Estado: {estado} - Origen: {origen}")
    
    return True


def main():
    """Ejecutar flujo completo."""
    # Crear reporte JSON
    reporte = crear_reporte_json(10, "Stripe - Presupuestos")
    
    print("=" * 60)
    print("FLUJO 10: PRUEBAS DE INTEGRACION CON STRIPE - PRESUPUESTOS")
    print("=" * 60)
    
    # Variables de contexto
    presupuesto_id = None
    pago_id = None
    payment_intent_id = None
    monto = 0
    
    # SECCION 1: Autenticacion
    exito_auth, admin_token, token = autenticar_usuarios()
    reporte.agregar_seccion(
        numero=1,
        nombre="Autenticacion",
        exito=exito_auth,
        detalles={"admin_autenticado": admin_token is not None, "paciente_autenticado": token is not None}
    )
    
    if not exito_auth or not token:
        reporte.generar_archivo()
        print("\n✓ Reporte JSON generado: salida_flujo10.json")
        return
    
    # SECCION 2: Listar presupuestos
    exito_listar, presupuesto = listar_presupuestos(token)
    
    if exito_listar and presupuesto:
        presupuesto_id = presupuesto['id']
        total_presupuesto = float(presupuesto['total'])
        monto = total_presupuesto  # Pagar el total del presupuesto
        
        reporte.agregar_seccion(
            numero=2,
            nombre="Listar presupuestos",
            exito=True,
            detalles={
                "presupuesto_id": presupuesto_id,
                "total": str(total_presupuesto),
                "estado": presupuesto.get('estado')
            }
        )
    else:
        reporte.agregar_seccion(
            numero=2,
            nombre="Listar presupuestos",
            exito=False,
            detalles={"error": "No se encontraron presupuestos disponibles"}
        )
        reporte.generar_archivo()
        print("\n✓ Reporte JSON generado: salida_flujo10.json")
        return
    
    # SECCION 3: Crear Payment Intent
    exito_payment, pago_id, codigo_pago, client_secret = crear_payment_intent_presupuesto(
        token, presupuesto_id, monto
    )
    
    if exito_payment:
        payment_intent_id = client_secret.split('_secret_')[0] if client_secret else None
        
        reporte.agregar_seccion(
            numero=3,
            nombre="Payment Intent",
            exito=True,
            detalles={
                "pago_id": pago_id,
                "codigo_pago": codigo_pago,
                "monto": str(monto),
                "presupuesto_id": presupuesto_id
            }
        )
    else:
        reporte.agregar_seccion(
            numero=3,
            nombre="Payment Intent",
            exito=False
        )
        reporte.generar_archivo()
        print("\n✓ Reporte JSON generado: salida_flujo10.json")
        return
    
    # SECCION 4: Marcar pago como aprobado (simulación)
    exito_aprobado = marcar_pago_aprobado(pago_id)
    reporte.agregar_seccion(
        numero=4,
        nombre="Confirmar pago",
        exito=exito_aprobado,
        detalles={"pago_id": pago_id}
    )
    
    if not exito_aprobado:
        reporte.generar_archivo()
        print("\n✓ Reporte JSON generado: salida_flujo10.json")
        return
    
    # SECCION 5: Confirmar pago y aprobar presupuesto
    exito_confirmar, presupuesto_confirmado_id = confirmar_pago_presupuesto(
        token, pago_id, payment_intent_id
    )
    reporte.agregar_seccion(
        numero=5,
        nombre="Aprobar presupuesto",
        exito=exito_confirmar,
        detalles={
            "pago_id": pago_id,
            "presupuesto_id": presupuesto_confirmado_id
        }
    )
    
    if not exito_confirmar:
        reporte.generar_archivo()
        print("\n✓ Reporte JSON generado: salida_flujo10.json")
        return
    
    # SECCION 6: Verificar aprobación
    exito_verificar = verificar_aprobacion_presupuesto(token, presupuesto_id)
    reporte.agregar_seccion(
        numero=6,
        nombre="Verificar aprobacion",
        exito=exito_verificar,
        detalles={"presupuesto_id": presupuesto_id}
    )
    
    # SECCION 7: Listar pagos
    exito_listar_pagos = listar_pagos(admin_token)
    reporte.agregar_seccion(
        numero=7,
        nombre="Listar pagos",
        exito=exito_listar_pagos
    )
    
    # Resumen final
    print("\n" + "=" * 60)
    print("RESUMEN DEL FLUJO 10")
    print("=" * 60)
    print(f"Autenticacion: {'✓' if exito_auth else '✗'}")
    print(f"Listar presupuestos: {'✓' if exito_listar else '✗'}")
    print(f"Payment Intent: {'✓' if exito_payment else '✗'}")
    print(f"Confirmar pago: {'✓' if exito_aprobado else '✗'}")
    print(f"Aprobar presupuesto: {'✓' if exito_confirmar else '✗'}")
    print(f"Verificar aprobacion: {'✓' if exito_verificar else '✗'}")
    print(f"Listar pagos: {'✓' if exito_listar_pagos else '✗'}")
    
    print(f"\nDatos creados:")
    print(f"  - Presupuesto ID: {presupuesto_id}")
    print(f"  - Pago ID: {pago_id}")
    print(f"  - Monto: Bs. {monto}")
    
    reporte.generar_archivo()
    print("\n✓ Reporte JSON generado: salida_flujo10.json")
    print("=" * 60)


if __name__ == "__main__":
    main()
