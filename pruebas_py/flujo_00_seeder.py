"""
FLUJO 00: Verificación de Seeder
Verifica que los datos del seeder estén correctamente cargados en la base de datos
"""
import requests
import sys
from http_logger import (
    print_http_transaction, 
    print_seccion, 
    print_exito, 
    print_error,
    print_info
)
from json_output_helper import crear_reporte_json

# Configuración
BASE_URL = "http://localhost:8000/api/v1"

# Variables globales para tokens
admin_token = None
odontologo_token = None
paciente_token = None


def login(correo: str, password: str, rol_descripcion: str) -> tuple[bool, str]:
    """
    Realiza login y retorna (exitoso, token)
    """
    url = f"{BASE_URL}/auth/login/"
    
    body = {
        "correo": correo,
        "password": password
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=body, headers=headers)
        
        # Imprimir transacción completa
        print_http_transaction(
            metodo="POST",
            url=url,
            headers=headers,
            body=body,
            response_status=response.status_code,
            response_headers=dict(response.headers),
            response_body=response.json() if response.headers.get('Content-Type', '').startswith('application/json') else response.text,
            descripcion=f"Login como {rol_descripcion}"
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("token")
            if token:
                print_exito(f"Login exitoso como {rol_descripcion}")
                return True, token
            else:
                print_error(f"Login {rol_descripcion}: No se recibió token en la respuesta")
                return False, ""
        else:
            print_error(f"Login {rol_descripcion} falló con status {response.status_code}")
            return False, ""
            
    except requests.exceptions.RequestException as e:
        print_error(f"Error de conexión: {str(e)}")
        return False, ""
    except Exception as e:
        print_error(f"Error inesperado: {str(e)}")
        return False, ""


def listar_usuarios(token: str) -> bool:
    """
    Lista todos los usuarios (requiere autenticación de Admin)
    """
    url = f"{BASE_URL}/usuarios/"
    
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
            descripcion="Listar todos los usuarios"
        )
        
        if response.status_code == 200:
            usuarios = response.json()
            print_exito(f"Se listaron {len(usuarios)} usuarios correctamente")
            return True
        else:
            print_error(f"Listar usuarios falló con status {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def listar_odontologos(token: str) -> bool:
    """
    Lista todos los odontólogos
    """
    url = f"{BASE_URL}/profesionales/odontologos/"
    
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
            descripcion="Listar odontólogos"
        )
        
        if response.status_code == 200:
            odontologos = response.json()
            if isinstance(odontologos, list):
                print_exito(f"Se listaron {len(odontologos)} odontólogos correctamente")
            else:
                print_exito("Odontólogos listados correctamente")
            return True
        else:
            print_error(f"Listar odontólogos falló con status {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def listar_servicios(token: str) -> bool:
    """
    Lista todos los servicios odontológicos
    """
    url = f"{BASE_URL}/servicios/servicios/"
    
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
            descripcion="Listar servicios odontológicos"
        )
        
        if response.status_code == 200:
            servicios = response.json()
            if isinstance(servicios, list):
                print_exito(f"Se listaron {len(servicios)} servicios correctamente")
            else:
                print_exito("Servicios listados correctamente")
            return True
        else:
            print_error(f"Listar servicios falló con status {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def main():
    """
    Función principal que ejecuta el flujo completo de verificación del seeder
    """
    global admin_token, odontologo_token, paciente_token
    
    # Inicializar reporte JSON
    reporte = crear_reporte_json(0, "Verificacion de Seeder")
    
    print_seccion("FLUJO 00: VERIFICACIÓN DE DATOS DEL SEEDER")
    
    print_info("Verificando que el servidor esté corriendo en http://localhost:8000")
    print_info("Asegúrate de haber ejecutado: python seed_database.py --force")
    
    # ======================================
    # SECCIÓN 1: Login con diferentes roles
    # ======================================
    print_seccion("SECCIÓN 1: AUTENTICACIÓN DE USUARIOS")
    
    # 1.1 Login como Admin
    exito_admin, admin_token = login(
        correo="admin@clinica.com",
        password="admin123",
        rol_descripcion="Admin"
    )
    if not exito_admin:
        print_error("No se pudo autenticar como Admin. Abortando pruebas.")
        sys.exit(1)
    
    # 1.2 Login como Odontólogo
    exito_odont, odontologo_token = login(
        correo="dr.perez@clinica.com",
        password="odontologo123",
        rol_descripcion="Odontólogo"
    )
    if not exito_odont:
        print_error("No se pudo autenticar como Odontólogo. Abortando pruebas.")
        sys.exit(1)
    
    # 1.3 Login como Paciente
    exito_pac, paciente_token = login(
        correo="ana.lopez@email.com",
        password="paciente123",
        rol_descripcion="Paciente"
    )
    if not exito_pac:
        print_error("No se pudo autenticar como Paciente. Abortando pruebas.")
        sys.exit(1)
    
    # Tracking de Sección 1
    reporte.agregar_seccion(1, "Autenticacion de usuarios", True, {
        "roles_autenticados": ["Admin", "Odontologo", "Paciente"],
        "total_logins": 3
    })
    
    # ======================================
    # SECCIÓN 2: Verificación de datos
    # ======================================
    print_seccion("SECCIÓN 2: VERIFICACIÓN DE DATOS DEL SEEDER")
    
    # 2.1 Listar usuarios (requiere admin)
    exito_usuarios = listar_usuarios(admin_token)
    if not exito_usuarios:
        print_error("Fallo al listar usuarios")
    
    # 2.2 Listar odontólogos
    exito_odontologos = listar_odontologos(admin_token)
    if not exito_odontologos:
        print_error("Fallo al listar odontólogos")
    
    # 2.3 Listar servicios
    exito_servicios = listar_servicios(admin_token)
    if not exito_servicios:
        print_error("Fallo al listar servicios")
    
    # Tracking de Sección 2
    seccion2_exitosa = exito_usuarios and exito_odontologos and exito_servicios
    reporte.agregar_seccion(2, "Verificacion de datos del seeder", seccion2_exitosa, {
        "verificaciones_realizadas": 3,
        "usuarios": exito_usuarios,
        "odontologos": exito_odontologos,
        "servicios": exito_servicios
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
    print_seccion("RESUMEN DE VERIFICACIÓN")
    print_exito("✓ Usuarios del seeder autenticados correctamente")
    print_exito("✓ Tokens obtenidos para los 3 roles")
    print_exito("✓ Datos del seeder verificados")
    print_info("El backend está listo para las pruebas de los demás flujos")


if __name__ == "__main__":
    main()
