"""
FLUJO 09: PRUEBAS DE INTEGRACION CON STRIPE
============================================
Este flujo prueba el sistema de pagos en linea con Stripe:
1. Autenticacion de usuarios (admin, paciente)
2. Obtener tipos de consulta y precios
3. Crear Payment Intent en Stripe
4. Simular pago con tarjeta de prueba
5. Confirmar pago
6. Crear cita vinculada al pago
7. Verificar vinculacion pago-cita
"""

import requests
import sys
import os
import django

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
    paciente_id = response_paciente.json().get('usuario', {}).get('codigo')
    print(f"✓ Paciente autenticado (ID: {paciente_id})")
    
    return True, admin_token, paciente_token


def obtener_tipos_consulta(token):
    """Obtener tipos de consulta disponibles y sus precios."""
    print("\n=== SECCION 2: OBTENER TIPOS DE CONSULTA ===")
    
    headers = {"Authorization": f"Token {token}"}
    url = f"{BASE_URL}/api/v1/citas/tipos-consulta/"
    
    print_http_transaction(
        metodo="GET",
        url=url,
        headers=headers,
        descripcion="Obtener tipos de consulta"
    )
    
    response = requests.get(url, headers=headers)
    
    print_http_transaction(
        metodo="GET",
        url=url,
        headers=headers,
        response_status=response.status_code,
        response_body=response.json() if response.status_code == 200 else response.text,
        descripcion="Respuesta - Tipos de consulta"
    )
    
    if response.status_code == 200:
        data = response.json()
        tipos = data.get('results', data if isinstance(data, list) else [])
        if tipos:
            tipo_seleccionado = tipos[0]
            print(f"✓ Se encontraron {len(tipos)} tipos de consulta")
            print(f"  Tipo seleccionado: {tipo_seleccionado.get('nombre')} - Duracion: {tipo_seleccionado.get('duracion_estimada')} min")
            return True, tipo_seleccionado
        else:
            print("⚠ No hay tipos de consulta disponibles")
            return False, None
    else:
        print("✗ Error al obtener tipos de consulta")
        return False, None


def crear_payment_intent(token, monto, tipo_consulta_id):
    """Crear Payment Intent en Stripe."""
    print("\n=== SECCION 3: CREAR PAYMENT INTENT EN STRIPE ===")
    
    headers = {"Authorization": f"Token {token}"}
    url = f"{BASE_URL}/api/v1/pagos/stripe/crear-intencion-consulta/"
    
    payload = {
        "tipo_consulta_id": tipo_consulta_id,
        "monto": monto
    }
    
    print_http_transaction(
        metodo="POST",
        url=url,
        headers=headers,
        body=payload,
        descripcion="Crear Payment Intent"
    )
    
    response = requests.post(url, json=payload, headers=headers)
    
    print_http_transaction(
        metodo="POST",
        url=url,
        headers=headers,
        body=payload,
        response_status=response.status_code,
        response_body=response.json() if response.status_code == 200 else response.text,
        descripcion="Respuesta - Payment Intent creado"
    )
    
    if response.status_code == 200 or response.status_code == 201:
        data = response.json()
        client_secret = data.get('client_secret')
        pago_id = data.get('pago_id')
        codigo_pago = data.get('codigo_pago')
        
        print(f"✓ Payment Intent creado exitosamente")
        print(f"  Codigo Pago: {codigo_pago}")
        print(f"  Pago ID (DB): {pago_id}")
        print(f"  Client Secret: {client_secret[:20]}..." if client_secret else "  Client Secret: None")
        
        # El payment_intent_id no viene en la respuesta, usar codigo_pago
        return True, client_secret, codigo_pago, pago_id
    else:
        print("✗ Error al crear Payment Intent")
        return False, None, None, None


def confirmar_pago(token, pago_id):
    """Confirmar el pago (simular pago exitoso)."""
    print("\n=== SECCION 4: CONFIRMAR PAGO ===")
    
    headers = {"Authorization": f"Token {token}"}
    url = f"{BASE_URL}/api/v1/pagos/stripe/confirmar-pago/"
    
    payload = {
        "pago_id": pago_id
    }
    
    print_http_transaction(
        metodo="POST",
        url=url,
        headers=headers,
        body=payload,
        descripcion="Confirmar pago"
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
    
    if response.status_code == 200:
        data = response.json()
        estado = data.get('estado')
        print(f"✓ Pago confirmado exitosamente")
        print(f"  Estado: {estado}")
        return True, estado
    else:
        print("✗ Error al confirmar pago")
        return False, None


def crear_cita_con_pago(token, pago_id, tipo_consulta_id):
    """Crear una cita vinculada al pago."""
    print("\n=== SECCION 5: CREAR CITA VINCULADA AL PAGO ===")
    
    headers = {"Authorization": f"Token {token}"}
    url = f"{BASE_URL}/api/v1/citas/consultas/"
    
    # Obtener fecha/hora disponible (usaremos fecha futura)
    from datetime import datetime, timedelta
    fecha_cita = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    
    # Usar IDs del seeder: paciente 641, odontologo 637, horario 982
    payload = {
        "codpaciente": 641,
        "cododontologo": 637,
        "fecha": fecha_cita,
        "idhorario": 982,  # ID del primer horario (08:00)
        "idtipoconsulta": tipo_consulta_id,
        "motivo_consulta": "Consulta pagada con Stripe",
        "horario_preferido": "cualquiera",
        "pago_id": pago_id  # Vincular con el pago
    }
    
    print_http_transaction(
        metodo="POST",
        url=url,
        headers=headers,
        body=payload,
        descripcion="Crear cita con pago vinculado"
    )
    
    response = requests.post(url, json=payload, headers=headers)
    
    print_http_transaction(
        metodo="POST",
        url=url,
        headers=headers,
        body=payload,
        response_status=response.status_code,
        response_body=response.json() if response.status_code == 200 else response.text,
        descripcion="Respuesta - Cita creada"
    )
    
    if response.status_code == 200 or response.status_code == 201:
        data = response.json()
        consulta_id = data.get('codigo')
        pago_vinculado = data.get('pago_vinculado', False)
        print(f"✓ Cita creada exitosamente")
        print(f"  Consulta ID: {consulta_id}")
        print(f"  Pago vinculado: {pago_vinculado}")
        return True, consulta_id
    else:
        error_text = response.text if response.text else "Sin mensaje de error"
        print(f"✗ Error al crear cita: {error_text}")
        return False, None


def verificar_vinculacion(token, consulta_id, pago_id):
    """Verificar que el pago y la cita esten correctamente vinculados."""
    print("\n=== SECCION 6: VERIFICAR VINCULACION PAGO-CITA ===")
    
    headers = {"Authorization": f"Token {token}"}
    
    # Verificar consulta
    print("\n[6.1] Verificar datos de la consulta")
    url_consulta = f"{BASE_URL}/api/v1/citas/consultas/{consulta_id}/"
    
    print_http_transaction(
        metodo="GET",
        url=url_consulta,
        headers=headers,
        descripcion="Obtener detalles de consulta"
    )
    
    response_consulta = requests.get(url_consulta, headers=headers)
    
    print_http_transaction(
        metodo="GET",
        url=url_consulta,
        headers=headers,
        response_status=response_consulta.status_code,
        response_body=response_consulta.json() if response_consulta.status_code == 200 else response_consulta.text,
        descripcion="Respuesta - Consulta"
    )
    
    consulta_ok = False
    if response_consulta.status_code == 200:
        consulta_data = response_consulta.json()
        print(f"✓ Consulta obtenida - ID: {consulta_data.get('codigo')}")
        consulta_ok = True
    else:
        print("✗ Error al obtener consulta")
    
    # Verificar pago
    print("\n[6.2] Verificar datos del pago")
    url_pago = f"{BASE_URL}/api/v1/pagos/pagos-online/{pago_id}/"
    
    print_http_transaction(
        metodo="GET",
        url=url_pago,
        headers=headers,
        descripcion="Obtener detalles de pago"
    )
    
    response_pago = requests.get(url_pago, headers=headers)
    
    print_http_transaction(
        metodo="GET",
        url=url_pago,
        headers=headers,
        response_status=response_pago.status_code,
        response_body=response_pago.json() if response_pago.status_code == 200 else response_pago.text,
        descripcion="Respuesta - Pago"
    )
    
    pago_ok = False
    vinculacion_ok = False
    if response_pago.status_code == 200:
        pago_data = response_pago.json()
        consulta_vinculada = pago_data.get('consulta')
        print(f"✓ Pago obtenido - Estado: {pago_data.get('estado')}")
        print(f"  Consulta vinculada: {consulta_vinculada}")
        pago_ok = True
        
        if consulta_vinculada == consulta_id:
            print("✓ Vinculacion correcta: Pago y Cita estan conectados")
            vinculacion_ok = True
        else:
            print("✗ Error: La vinculacion no coincide")
    else:
        print("✗ Error al obtener pago")
    
    return consulta_ok and pago_ok and vinculacion_ok


def listar_pagos(token):
    """Listar todos los pagos en linea."""
    print("\n=== SECCION 7: LISTAR PAGOS EN LINEA ===")
    
    headers = {"Authorization": f"Token {token}"}
    url = f"{BASE_URL}/api/v1/pagos/pagos-online/"
    
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
    
    if response.status_code == 200:
        data = response.json()
        pagos = data.get('results', data if isinstance(data, list) else [])
        print(f"✓ Se encontraron {len(pagos)} pagos en linea")
        
        if pagos:
            print("\nUltimos 3 pagos:")
            for pago in pagos[:3]:
                print(f"  - ID {pago.get('codigo')}: ${pago.get('monto')} - Estado: {pago.get('estado')}")
        
        return True
    else:
        print("✗ Error al listar pagos")
        return False


def main():
    """Ejecutar el flujo completo de pruebas de Stripe."""
    print("=" * 60)
    print("FLUJO 09: PRUEBAS DE INTEGRACION CON STRIPE")
    print("=" * 60)
    
    # Inicializar reporte JSON
    reporte = crear_reporte_json(9, "Pruebas de Integracion con Stripe")
    
    # SECCION 1: Autenticacion
    exito_auth, admin_token, paciente_token = autenticar_usuarios()
    reporte.agregar_seccion(
        numero=1,
        nombre="Autenticacion de Usuarios",
        exito=exito_auth
    )
    
    if not exito_auth or not paciente_token:
        print("\n✗ No se puede continuar sin autenticacion")
        reporte.agregar_error("Autenticacion", "Fallo la autenticacion de usuarios")
        archivo_generado = reporte.generar_archivo()
        print(f"\n✓ Reporte JSON generado: {archivo_generado}")
        return
    
    # Usar token de paciente para el flujo de pago
    token = paciente_token
    
    # SECCION 2: Obtener tipos de consulta
    exito_tipos, tipo_consulta = obtener_tipos_consulta(token)
    reporte.agregar_seccion(
        numero=2,
        nombre="Obtener Tipos de Consulta",
        exito=exito_tipos
    )
    
    if not exito_tipos or not tipo_consulta:
        print("\n✗ No se puede continuar sin tipos de consulta")
        reporte.agregar_error("Tipos Consulta", "No hay tipos de consulta disponibles")
        archivo_generado = reporte.generar_archivo()
        print(f"\n✓ Reporte JSON generado: {archivo_generado}")
        return
    
    tipo_consulta_id = tipo_consulta.get('id')
    tipo_consulta_nombre = tipo_consulta.get('nombre')
    monto = 100.00  # Monto fijo para la prueba (100 Bs)
    
    # SECCION 3: Crear Payment Intent
    exito_intent, client_secret, codigo_pago, pago_id = crear_payment_intent(
        token, monto, tipo_consulta_id
    )
    reporte.agregar_seccion(
        numero=3,
        nombre="Crear Payment Intent",
        exito=exito_intent,
        detalles={"codigo_pago": codigo_pago, "pago_id": pago_id, "monto": monto}
    )
    
    if not exito_intent:
        print("\n✗ No se puede continuar sin Payment Intent")
        reporte.agregar_error("Payment Intent", "Error al crear Payment Intent en Stripe")
        archivo_generado = reporte.generar_archivo()
        print(f"\n✓ Reporte JSON generado: {archivo_generado}")
        return
    
    reporte.agregar_dato_creado("pago", pago_id, {
        "codigo_pago": codigo_pago,
        "monto": monto,
        "tipo_consulta": tipo_consulta_nombre
    })
    
    # SECCION 4: Confirmar pago (NOTA: requiere interaccion real con Stripe)
    # En un flujo real, el frontend usaria Stripe.js para procesar el pago
    # Para pruebas E2E, simulamos que el pago fue aprobado manualmente
    print("\n=== SECCION 4: SIMULAR CONFIRMACION DE PAGO ===")
    print("NOTA: En produccion, el frontend procesaria el pago con Stripe.js")
    print("Para pruebas E2E, marcaremos el pago como aprobado manualmente en la BD")
    
    # Actualizar estado del pago directamente en la BD (solo para testing)
    from apps.sistema_pagos.models import PagoEnLinea
    try:
        pago = PagoEnLinea.objects.get(id=pago_id)
        pago.estado = 'aprobado'
        pago.save()
        print(f"✓ Pago marcado como aprobado (ID: {pago_id})")
        exito_confirmar = True
        estado_pago = 'aprobado'
    except Exception as e:
        print(f"✗ Error al actualizar estado del pago: {e}")
        exito_confirmar = False
        estado_pago = None
    
    reporte.agregar_seccion(
        numero=4,
        nombre="Simular Confirmacion de Pago",
        exito=exito_confirmar,
        detalles={"estado": estado_pago, "nota": "Simulado para testing E2E"}
    )
    
    if not exito_confirmar:
        print("\n✗ No se puede continuar sin confirmar el pago")
        reporte.agregar_error("Confirmar Pago", "Error al confirmar el pago")
        archivo_generado = reporte.generar_archivo()
        print(f"\n✓ Reporte JSON generado: {archivo_generado}")
        return
    
    # SECCION 5: Crear cita con pago
    exito_cita, consulta_id = crear_cita_con_pago(token, pago_id, tipo_consulta_id)
    reporte.agregar_seccion(
        numero=5,
        nombre="Crear Cita con Pago Vinculado",
        exito=exito_cita,
        detalles={"consulta_id": consulta_id, "pago_id": pago_id}
    )
    
    if exito_cita:
        reporte.agregar_dato_creado("consulta", consulta_id, {
            "tipo_consulta": tipo_consulta_nombre,
            "pago_id": pago_id
        })
    
    # SECCION 6: Verificar vinculacion
    exito_verificar = verificar_vinculacion(token, consulta_id, pago_id) if exito_cita else False
    reporte.agregar_seccion(
        numero=6,
        nombre="Verificar Vinculacion Pago-Cita",
        exito=exito_verificar
    )
    
    # SECCION 7: Listar pagos
    exito_listar = listar_pagos(admin_token)
    reporte.agregar_seccion(
        numero=7,
        nombre="Listar Pagos en Linea",
        exito=exito_listar
    )
    
    # Generar reporte JSON
    archivo_generado = reporte.generar_archivo()
    
    print("\n" + "=" * 60)
    print("RESUMEN DEL FLUJO 09")
    print("=" * 60)
    print(f"Autenticacion: {'✓' if exito_auth else '✗'}")
    print(f"Tipos de consulta: {'✓' if exito_tipos else '✗'}")
    print(f"Payment Intent: {'✓' if exito_intent else '✗'}")
    print(f"Confirmar pago: {'✓' if exito_confirmar else '✗'}")
    print(f"Crear cita: {'✓' if exito_cita else '✗'}")
    print(f"Verificar vinculacion: {'✓' if exito_verificar else '✗'}")
    print(f"Listar pagos: {'✓' if exito_listar else '✗'}")
    if exito_cita:
        print(f"\nDatos creados:")
        print(f"  - Pago ID: {pago_id}")
        print(f"  - Consulta ID: {consulta_id}")
        print(f"  - Monto: ${monto}")
    print(f"\n✓ Reporte JSON generado: {archivo_generado}")
    print("=" * 60)


if __name__ == "__main__":
    main()
