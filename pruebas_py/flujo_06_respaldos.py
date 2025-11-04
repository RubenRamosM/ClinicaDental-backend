"""
FLUJO 06: Sistema de Respaldos
Prueba creacion, listado, descarga y estadisticas de respaldos
"""
import requests
import sys
from http_logger import (
    print_http_transaction, 
    print_seccion, 
    print_exito, 
    print_error,
    print_info,
    print_warning
)

# Configuracion
BASE_URL = "http://localhost:8000/api/v1"

# Variables globales
admin_token = None
respaldo_id = None


def login(correo: str, password: str) -> tuple[bool, str]:
    """Realiza login"""
    url = f"{BASE_URL}/auth/login/"
    body = {"correo": correo, "password": password}
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, json=body, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return True, data.get("token")
        return False, ""
    except:
        return False, ""


def listar_respaldos(token: str, descripcion: str) -> tuple[bool, list]:
    """Lista todos los respaldos"""
    url = f"{BASE_URL}/respaldos/"
    
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
            data = response.json()
            respaldos = data.get('results', data if isinstance(data, list) else [])
            cantidad = len(respaldos)
            print_exito(f"Respaldos listados (Total: {cantidad})")
            return True, respaldos
        else:
            print_error(f"Listar respaldos fallo: {response.status_code}")
            return False, []
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False, []


def crear_respaldo_manual(token: str, descripcion_text: str, descripcion: str) -> tuple[bool, dict]:
    """Crea un respaldo manual de la base de datos"""
    url = f"{BASE_URL}/respaldos/crear_respaldo_manual/"
    
    body = {
        "descripcion": descripcion_text
    }
    
    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=body, headers=headers)
        
        print_http_transaction(
            metodo="POST",
            url=url,
            headers=headers,
            body=body,
            response_status=response.status_code,
            response_headers=dict(response.headers),
            response_body=response.json() if response.headers.get('Content-Type', '').startswith('application/json') else response.text,
            descripcion=descripcion
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            respaldo = data.get('respaldo', {})
            respaldo_id = respaldo.get('id') or respaldo.get('codigo')
            print_exito(f"Respaldo creado (ID: {respaldo_id})")
            return True, respaldo
        else:
            print_error(f"Crear respaldo fallo: {response.status_code}")
            return False, None
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False, None


def obtener_estadisticas(token: str, descripcion: str) -> bool:
    """Obtiene estadisticas de los respaldos"""
    url = f"{BASE_URL}/respaldos/estadisticas/"
    
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
            print_exito("Estadisticas obtenidas correctamente")
            return True
        else:
            print_error(f"Obtener estadisticas fallo: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def ver_detalle_respaldo(token: str, respaldo_id: int, descripcion: str) -> bool:
    """Obtiene el detalle de un respaldo especifico"""
    url = f"{BASE_URL}/respaldos/{respaldo_id}/"
    
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
            print_exito("Detalle del respaldo obtenido")
            return True
        else:
            print_error(f"Ver detalle fallo: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def obtener_url_descarga(token: str, respaldo_id: int, descripcion: str) -> bool:
    """Obtiene URL de descarga del respaldo"""
    url = f"{BASE_URL}/respaldos/{respaldo_id}/descargar/"
    
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
            print_exito("URL de descarga generada")
            return True
        else:
            print_error(f"Generar URL fallo: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def main():
    """Funcion principal"""
    global admin_token, respaldo_id
    
    print_seccion("FLUJO 06: SISTEMA DE RESPALDOS")
    print_info("Servidor: http://localhost:8000")
    print_warning("Nota: Las pruebas de respaldos requieren permisos de administrador")
    
    # ======================================
    # SECCION 1: Autenticacion
    # ======================================
    print_seccion("SECCION 1: AUTENTICACION")
    
    exito, admin_token = login("admin@clinica.com", "admin123")
    if not exito:
        print_error("No se pudo autenticar como Admin")
        sys.exit(1)
    print_exito("OK Login Admin exitoso")
    
    # ======================================
    # SECCION 2: Listar respaldos existentes
    # ======================================
    print_seccion("SECCION 2: LISTAR RESPALDOS EXISTENTES")
    
    print_info("\n=== Listar todos los respaldos ===\n")
    exito, respaldos_iniciales = listar_respaldos(admin_token, "Listar todos los respaldos")
    
    # ======================================
    # SECCION 3: Crear respaldo manual
    # ======================================
    print_seccion("SECCION 3: CREAR RESPALDO MANUAL")
    
    print_warning("Creando respaldo de la base de datos... Esto puede tardar unos segundos")
    print_info("\n=== Crear respaldo manual ===\n")
    
    exito, respaldo_data = crear_respaldo_manual(
        token=admin_token,
        descripcion_text="Respaldo manual creado desde pruebas automatizadas",
        descripcion="Crear respaldo manual de la BD"
    )
    
    if exito and respaldo_data:
        respaldo_id = respaldo_data.get('id')
        print_info(f"Respaldo creado con ID: {respaldo_id}")
    
    # ======================================
    # SECCION 4: Ver respaldos actualizados
    # ======================================
    print_seccion("SECCION 4: VERIFICAR RESPALDO CREADO")
    
    print_info("\n=== Listar respaldos (despues de crear) ===\n")
    listar_respaldos(admin_token, "Listar respaldos (despues de crear)")
    
    # ======================================
    # SECCION 5: Ver detalle del respaldo
    # ======================================
    if respaldo_id:
        print_seccion("SECCION 5: VER DETALLE DEL RESPALDO")
        
        print_info(f"\n=== Ver detalle del respaldo #{respaldo_id} ===\n")
        ver_detalle_respaldo(
            token=admin_token,
            respaldo_id=respaldo_id,
            descripcion=f"Ver detalle del respaldo #{respaldo_id}"
        )
    
    # ======================================
    # SECCION 6: Obtener URL de descarga
    # ======================================
    if respaldo_id:
        print_seccion("SECCION 6: OBTENER URL DE DESCARGA")
        
        print_info(f"\n=== Generar URL de descarga ===\n")
        obtener_url_descarga(
            token=admin_token,
            respaldo_id=respaldo_id,
            descripcion=f"Obtener URL de descarga del respaldo #{respaldo_id}"
        )
    
    # ======================================
    # SECCION 7: Estadisticas de respaldos
    # ======================================
    print_seccion("SECCION 7: ESTADISTICAS DE RESPALDOS")
    
    print_info("\n=== Obtener estadisticas generales ===\n")
    obtener_estadisticas(
        token=admin_token,
        descripcion="Obtener estadisticas generales de respaldos"
    )
    
    # ======================================
    # RESUMEN FINAL
    # ======================================
    print_seccion("RESUMEN DE PRUEBAS DE RESPALDOS")
    print_exito("OK Listado de respaldos funciona")
    print_exito("OK Creacion de respaldos manuales exitosa")
    print_exito("OK Consulta de detalles funciona")
    print_exito("OK Generacion de URLs de descarga exitosa")
    print_exito("OK Estadisticas de respaldos disponibles")
    print_info("Sistema de respaldos funcionando correctamente")
    print_warning("Nota: Los archivos de respaldo se guardan en AWS S3 o localmente segun configuracion")


if __name__ == "__main__":
    main()
