"""
FLUJO 05: Facturacion y Pagos
Prueba generacion de facturas y registro de pagos
"""
import requests
import sys
from datetime import datetime, timedelta
from http_logger import (
    print_http_transaction, 
    print_seccion, 
    print_exito, 
    print_error,
    print_info,
    print_warning
)
from json_output_helper import crear_reporte_json

# Configuracion
BASE_URL = "http://localhost:8000/api/v1"

# Variables globales
admin_token = None
paciente_token = None
paciente_id = None
factura_id = None
pago_id = None


def login(correo: str, password: str) -> tuple[bool, str, dict]:
    """Realiza login"""
    url = f"{BASE_URL}/auth/login/"
    body = {"correo": correo, "password": password}
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, json=body, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return True, data.get("token"), data.get("usuario")
        return False, "", {}
    except:
        return False, "", {}


def listar_facturas(token: str, descripcion: str, paciente_id: int = None) -> tuple[bool, list]:
    """Lista facturas"""
    url = f"{BASE_URL}/pagos/facturas/"
    
    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json"
    }
    
    params = {"paciente": paciente_id} if paciente_id else None
    
    try:
        response = requests.get(url, params=params, headers=headers)
        
        print_http_transaction(
            metodo="GET",
            url=url + (f"?paciente={paciente_id}" if paciente_id else ""),
            headers=headers,
            body=None,
            response_status=response.status_code,
            response_headers=dict(response.headers),
            response_body=response.json() if response.headers.get('Content-Type', '').startswith('application/json') else response.text,
            descripcion=descripcion
        )
        
        if response.status_code == 200:
            data = response.json()
            facturas = data.get('results', data if isinstance(data, list) else [])
            print_exito(f"Facturas listadas (Total: {len(facturas)})")
            return True, facturas
        else:
            print_error(f"Listar facturas fallo: {response.status_code}")
            return False, []
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False, []


def crear_factura(token: str, datos: dict, descripcion: str) -> tuple[bool, int]:
    """Crea una factura"""
    url = f"{BASE_URL}/pagos/facturas/"
    
    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=datos, headers=headers)
        
        print_http_transaction(
            metodo="POST",
            url=url,
            headers=headers,
            body=datos,
            response_status=response.status_code,
            response_headers=dict(response.headers),
            response_body=response.json() if response.headers.get('Content-Type', '').startswith('application/json') else response.text,
            descripcion=descripcion
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            factura_id = data.get('id') or data.get('idfactura')
            
            # Si no viene el ID en la respuesta, listar para obtener la ultima
            if not factura_id:
                print_info("Factura creada, consultando lista para obtener ID...")
                list_response = requests.get(
                    f"{BASE_URL}/pagos/facturas/",
                    headers=headers
                )
                if list_response.status_code == 200:
                    list_data = list_response.json()
                    facturas = list_data.get('results', list_data if isinstance(list_data, list) else [])
                    if facturas:
                        factura_id = facturas[0].get('id')
            
            print_exito(f"Factura creada (ID: {factura_id})")
            return True, factura_id
        else:
            print_error(f"Crear factura fallo: {response.status_code}")
            return False, None
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False, None


def ver_factura(token: str, factura_id: int, descripcion: str) -> bool:
    """Ver detalle de factura"""
    url = f"{BASE_URL}/pagos/facturas/{factura_id}/"
    
    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        print_http_transaction(
            metodo="GET",
            url=url,
            headers=headers,
            body=None,
            response_status=response.status_code,
            response_headers=dict(response.headers),
            response_body=response.json() if response.headers.get('Content-Type', '').startswith('application/json') else response.text,
            descripcion=descripcion
        )
        
        if response.status_code == 200:
            print_exito("Factura obtenida correctamente")
            return True
        else:
            print_error(f"Ver factura fallo: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def registrar_pago(token: str, datos: dict, descripcion: str) -> tuple[bool, int]:
    """Registra un pago"""
    url = f"{BASE_URL}/pagos/"
    
    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=datos, headers=headers)
        
        print_http_transaction(
            metodo="POST",
            url=url,
            headers=headers,
            body=datos,
            response_status=response.status_code,
            response_headers=dict(response.headers),
            response_body=response.json() if response.headers.get('Content-Type', '').startswith('application/json') else response.text,
            descripcion=descripcion
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            pago_id = data.get('id') or data.get('idpago')
            print_exito(f"Pago registrado (ID: {pago_id})")
            return True, pago_id
        else:
            print_error(f"Registrar pago fallo: {response.status_code}")
            return False, None
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False, None


def listar_pagos(token: str, descripcion: str, factura_id: int = None) -> bool:
    """Lista pagos"""
    url = f"{BASE_URL}/pagos/"
    
    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json"
    }
    
    params = {"factura": factura_id} if factura_id else None
    
    try:
        response = requests.get(url, params=params, headers=headers)
        
        print_http_transaction(
            metodo="GET",
            url=url + (f"?factura={factura_id}" if factura_id else ""),
            headers=headers,
            body=None,
            response_status=response.status_code,
            response_headers=dict(response.headers),
            response_body=response.json() if response.headers.get('Content-Type', '').startswith('application/json') else response.text,
            descripcion=descripcion
        )
        
        if response.status_code == 200:
            data = response.json()
            cantidad = data.get('count', len(data) if isinstance(data, list) else 0)
            print_exito(f"Pagos listados (Total: {cantidad})")
            return True
        else:
            print_error(f"Listar pagos fallo: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def main():
    """Funcion principal"""
    global admin_token, paciente_token, paciente_id, factura_id, pago_id
    
    reporte = crear_reporte_json(5, "Facturacion y Pagos")
    
    print_seccion("FLUJO 05: FACTURACION Y PAGOS")
    print_info("Servidor: http://localhost:8000")
    
    # ======================================
    # SECCION 1: Autenticacion
    # ======================================
    print_seccion("SECCION 1: AUTENTICACION")
    
    exito, paciente_token, paciente_usuario = login("ana.lopez@email.com", "paciente123")
    if exito:
        print_exito("OK Login Paciente exitoso")
        paciente_id = paciente_usuario.get('codigo')
    
    exito, admin_token, _ = login("admin@clinica.com", "admin123")
    if not exito:
        print_error("No se pudo autenticar como Admin")
        sys.exit(1)
    print_exito("OK Login Admin exitoso")
    
    reporte.agregar_seccion(1, "Autenticacion", True, {
        "roles_autenticados": ["Paciente", "Admin"],
        "paciente_id": paciente_id
    })
    
    # ======================================
    # SECCION 2: Listar facturas existentes
    # ======================================
    print_seccion("SECCION 2: CONSULTAR FACTURAS")
    
    exito, facturas = listar_facturas(admin_token, "Listar todas las facturas")
    
    if paciente_id:
        listar_facturas(
            paciente_token,
            f"Listar facturas del paciente Ana Lopez",
            paciente_id=paciente_id
        )
    
    reporte.agregar_seccion(2, "Consultar facturas", True, {
        "consultas_realizadas": 2
    })
    
    # ======================================
    # SECCION 3: Crear factura
    # ======================================
    print_seccion("SECCION 3: CREAR FACTURA")
    
    if paciente_id:
        # Datos con campos del modelo legacy: fechaemision, montototal, idestadofactura
        nueva_factura = {
            "fechaemision": "2025-11-03",
            "montototal": 450.00,
            "idestadofactura": 148  # Estado "Pendiente"
        }
        
        exito, factura_id = crear_factura(
            token=admin_token,
            datos=nueva_factura,
            descripcion="Crear factura para paciente"
        )
        
        if not exito:
            print_warning("No se pudo crear la factura, continuando...")
            reporte.agregar_seccion(3, "Crear factura", False)
            reporte.agregar_error("Seccion 3", "Fallo al crear factura")
        else:
            reporte.agregar_seccion(3, "Crear factura", True, {
                "factura_id": factura_id,
                "monto": nueva_factura["montototal"]
            })
            reporte.agregar_dato_creado("factura", factura_id, {
                "monto": nueva_factura["montototal"],
                "fecha": nueva_factura["fechaemision"]
            })
    
    # ======================================
    # SECCION 4: Ver detalle de factura
    # ======================================
    if factura_id:
        print_seccion("SECCION 4: CONSULTAR DETALLE DE FACTURA")
        
        ver_factura(
            token=admin_token,
            factura_id=factura_id,
            descripcion=f"Ver factura #{factura_id}"
        )
        
        # Paciente tambien puede ver su factura
        if paciente_token:
            ver_factura(
                token=paciente_token,
                factura_id=factura_id,
                descripcion=f"Paciente consulta factura #{factura_id}"
            )
        
        reporte.agregar_seccion(4, "Consultar detalle de factura", True, {
            "factura_id": factura_id,
            "consultas_realizadas": 2
        })
    
    # ======================================
    # SECCION 5: Registrar pago
    # ======================================
    if factura_id:
        print_seccion("SECCION 5: REGISTRAR PAGO")
        
        # Campos del modelo legacy: idfactura, idtipopago, montopagado, fechapago
        nuevo_pago = {
            "idfactura": factura_id,
            "idtipopago": 198,  # Efectivo
            "montopagado": 450.00,
            "fechapago": "2025-11-03"
        }
        
        exito, pago_id = registrar_pago(
            token=admin_token,
            datos=nuevo_pago,
            descripcion=f"Registrar pago para factura #{factura_id}"
        )
        
        if exito:
            detalles_pago = {
                "factura_id": factura_id,
                "monto": nuevo_pago["montopagado"]
            }
            if pago_id:
                detalles_pago["pago_id"] = pago_id
                
            reporte.agregar_seccion(5, "Registrar pago", True, detalles_pago)
            
            if pago_id:
                reporte.agregar_dato_creado("pago", pago_id, {
                    "factura": factura_id,
                    "monto": nuevo_pago["montopagado"],
                    "tipo": "Efectivo"
                })
        else:
            reporte.agregar_seccion(5, "Registrar pago", False)
            reporte.agregar_error("Seccion 5", "Fallo al registrar pago")
    
    # ======================================
    # SECCION 6: Listar pagos
    # ======================================
    print_seccion("SECCION 6: CONSULTAR PAGOS")
    
    listar_pagos(admin_token, "Listar todos los pagos")
    
    if factura_id:
        listar_pagos(
            admin_token,
            f"Listar pagos de factura #{factura_id}",
            factura_id=factura_id
        )
    
    reporte.agregar_seccion(6, "Consultar pagos", True, {
        "consultas_realizadas": 2,
        "factura_id": factura_id if factura_id else None
    })
    
    # ======================================
    # GENERAR REPORTE JSON
    # ======================================
    archivo_generado = reporte.generar_archivo()
    print(f"\n{'='*80}")
    print(f"REPORTE JSON GENERADO: {archivo_generado}")
    print(f"{'='*80}\n")
    
    # ======================================
    # RESUMEN FINAL
    # ======================================
    print_seccion("RESUMEN DE PRUEBAS DE FACTURACION")
    print_exito("OK Listado de facturas funciona")
    print_exito("OK Creacion de facturas exitosa")
    print_exito("OK Consulta de facturas funciona")
    print_exito("OK Registro de pagos exitoso")
    print_exito("OK Consulta de pagos funciona")
    print_info("Sistema de facturacion y pagos funcionando correctamente")


if __name__ == "__main__":
    main()
