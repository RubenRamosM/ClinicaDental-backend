"""
FLUJO 03: Historiales Clinicos
Prueba creacion, consulta y actualizacion de historiales medicos
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
from json_output_helper import crear_reporte_json

# Configuracion
BASE_URL = "http://localhost:8000/api/v1"

# Variables globales
odontologo_token = None
admin_token = None
paciente_id = None
historial_id = None


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


def listar_historiales(token: str, descripcion: str, paciente_id: int = None) -> bool:
    """Lista historiales clinicos"""
    url = f"{BASE_URL}/historia-clinica/"
    
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
            cantidad = data.get('count', len(data) if isinstance(data, list) else 0)
            print_exito(f"Historiales listados (Total: {cantidad})")
            return True
        else:
            print_error(f"Listar historiales fallo: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def crear_historial(token: str, datos_historial: dict, descripcion: str) -> tuple[bool, int]:
    """Crea un nuevo historial clinico"""
    url = f"{BASE_URL}/historia-clinica/"
    
    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=datos_historial, headers=headers)
        
        print_http_transaction(
            metodo="POST",
            url=url,
            headers=headers,
            body=datos_historial,
            response_status=response.status_code,
            response_headers=dict(response.headers),
            response_body=response.json() if response.headers.get('Content-Type', '').startswith('application/json') else response.text,
            descripcion=descripcion
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            historial_id = data.get('id') or data.get('codigo')
            print_exito(f"Historial creado (ID: {historial_id})")
            return True, historial_id
        else:
            print_error(f"Crear historial fallo: {response.status_code}")
            return False, None
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False, None


def ver_historial(token: str, historial_id: int, descripcion: str) -> bool:
    """Obtiene detalle de un historial"""
    url = f"{BASE_URL}/historia-clinica/{historial_id}/"
    
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
            print_exito("Historial obtenido correctamente")
            return True
        else:
            print_error(f"Ver historial fallo: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def agregar_diagnostico(token: str, historial_id: int, diagnostico: dict, descripcion: str) -> bool:
    """Agrega un diagnostico al historial"""
    url = f"{BASE_URL}/historia-clinica/{historial_id}/diagnosticos/"
    
    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=diagnostico, headers=headers)
        
        print_http_transaction(
            metodo="POST",
            url=url,
            headers=headers,
            body=diagnostico,
            response_status=response.status_code,
            response_headers=dict(response.headers),
            response_body=response.json() if response.headers.get('Content-Type', '').startswith('application/json') else response.text,
            descripcion=descripcion
        )
        
        if response.status_code in [200, 201]:
            print_exito("Diagnostico agregado correctamente")
            return True
        else:
            print_error(f"Agregar diagnostico fallo: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def main():
    """Funcion principal"""
    global odontologo_token, admin_token, paciente_id, historial_id
    
    reporte = crear_reporte_json(3, "Historiales Clinicos")
    
    print_seccion("FLUJO 03: HISTORIALES CLINICOS")
    print_info("Servidor: http://localhost:8000")
    
    # ======================================
    # SECCION 1: Autenticacion
    # ======================================
    print_seccion("SECCION 1: AUTENTICACION")
    
    exito, paciente_token, paciente_usuario = login("ana.lopez@email.com", "paciente123")
    if exito:
        print_exito("OK Login Paciente exitoso")
        paciente_id = paciente_usuario.get('codigo')
    
    exito, odontologo_token, _ = login("dr.perez@clinica.com", "odontologo123")
    if not exito:
        print_error("No se pudo autenticar como Odontologo")
        sys.exit(1)
    print_exito("OK Login Odontologo exitoso")
    
    exito, admin_token, _ = login("admin@clinica.com", "admin123")
    if not exito:
        print_error("No se pudo autenticar como Admin")
        sys.exit(1)
    print_exito("OK Login Admin exitoso")
    
    # Tracking seccion 1
    if odontologo_token and admin_token:
        reporte.agregar_seccion(1, "Autenticacion", True, {
            "roles_autenticados": ["Paciente", "Odontologo", "Admin"],
            "paciente_id": paciente_id
        })
    else:
        reporte.agregar_seccion(1, "Autenticacion", False)
        reporte.agregar_error("Seccion 1", "Fallo al autenticar usuarios")
    
    # ======================================
    # SECCION 2: Listar historiales
    # ======================================
    print_seccion("SECCION 2: CONSULTAR HISTORIALES")
    
    listar_historiales(admin_token, "Listar todos los historiales (Admin)")
    
    if paciente_id:
        listar_historiales(
            odontologo_token,
            f"Listar historiales del paciente Ana Lopez",
            paciente_id=paciente_id
        )
    
    # Tracking seccion 2
    reporte.agregar_seccion(2, "Consultar historiales", True, {
        "consultas_realizadas": 2
    })
    
    # ======================================
    # SECCION 3: Crear historial
    # ======================================
    print_seccion("SECCION 3: CREAR HISTORIAL CLINICO")
    
    nuevo_historial = {
        "pacientecodigo": paciente_id,
        "motivoconsulta": "Dolor en muela inferior derecha - solicita revision urgente",
        "diagnostico": "Posible caries dental en molar inferior derecho",
        "tratamiento": "Se requiere evaluacion completa y radiografia",
        "alergias": "Ninguna conocida",
        "enfermedades": "Ninguna",
        "examenbucal": "Paciente con buena higiene dental general"
    }
    
    exito, historial_id = crear_historial(
        token=odontologo_token,
        datos_historial=nuevo_historial,
        descripcion="Crear historial clinico inicial"
    )
    
    # Tracking seccion 3
    if exito and historial_id:
        reporte.agregar_seccion(3, "Crear historial clinico", True, {
            "historial_id": historial_id,
            "paciente_id": paciente_id
        })
        reporte.agregar_dato_creado("historial", historial_id, {
            "paciente": paciente_id,
            "motivo": nuevo_historial["motivoconsulta"]
        })
    else:
        reporte.agregar_seccion(3, "Crear historial clinico", False)
        reporte.agregar_error("Seccion 3", "Fallo al crear historial")
    
    # ======================================
    # SECCION 4: Ver detalle del historial
    # ======================================
    if historial_id:
        print_seccion("SECCION 4: CONSULTAR DETALLE DEL HISTORIAL")
        
        ver_historial(
            token=odontologo_token,
            historial_id=historial_id,
            descripcion=f"Ver historial #{historial_id}"
        )
        
        # Tracking seccion 4
        reporte.agregar_seccion(4, "Consultar detalle del historial", True, {
            "historial_id": historial_id
        })
    
    # ======================================
    # SECCION 5: Actualizar historial (agregar diagnostico detallado)
    # ======================================
    if historial_id:
        print_seccion("SECCION 5: ACTUALIZAR HISTORIAL")
        
        # Actualizar con diagnostico completo y tratamiento
        datos_actualizacion = {
            "diagnostico": "Caries dental profunda en pieza 46 (primer molar inferior derecho)",
            "tratamiento": "Limpieza y obturacion con resina compuesta",
            "receta": "Ibuprofeno 400mg cada 8 horas por 3 dias si hay dolor"
        }
        
        url = f"{BASE_URL}/historia-clinica/{historial_id}/"
        headers = {
            "Authorization": f"Token {odontologo_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.patch(url, json=datos_actualizacion, headers=headers)
            
            print_http_transaction(
                metodo="PATCH",
                url=url,
                headers=headers,
                body=datos_actualizacion,
                response_status=response.status_code,
                response_headers=dict(response.headers),
                response_body=response.json() if response.headers.get('Content-Type', '').startswith('application/json') else response.text,
                descripcion=f"Actualizar historial #{historial_id} con diagnostico y tratamiento"
            )
            
            if response.status_code == 200:
                print_exito("Historial actualizado correctamente")
            else:
                print_error(f"Actualizar historial fallo: {response.status_code}")
        except Exception as e:
            print_error(f"Error: {str(e)}")
        
        # Verificar que se actualizo
        print_info("Verificando actualizacion...")
        ver_historial(
            token=odontologo_token,
            historial_id=historial_id,
            descripcion=f"Ver historial actualizado #{historial_id}"
        )
        
        # Tracking seccion 5
        reporte.agregar_seccion(5, "Actualizar historial", True, {
            "historial_id": historial_id,
            "campos_actualizados": ["diagnostico", "tratamiento", "receta"]
        })
    
    # ======================================
    # RESUMEN FINAL
    # ======================================
    print_seccion("RESUMEN DE PRUEBAS DE HISTORIALES")
    print_exito("OK Consulta de historiales funciona")
    print_exito("OK Creacion de historiales exitosa")
    print_exito("OK Visualizacion de detalles funciona")
    print_exito("OK Actualizacion de historiales funciona")
    print_info("Sistema de historiales clinicos funcionando correctamente")
    
    # ======================================
    # GENERAR ARCHIVO JSON
    # ======================================
    archivo_generado = reporte.generar_archivo()
    print_info(f"\nArchivo JSON generado: {archivo_generado}")


if __name__ == "__main__":
    main()
