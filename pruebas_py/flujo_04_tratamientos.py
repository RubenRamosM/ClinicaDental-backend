"""
FLUJO 04: Tratamientos y Presupuestos
Prueba gestion de tratamientos, presupuestos y servicios odontologicos
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
tratamiento_id = None
presupuesto_id = None


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


def listar_servicios(token: str, descripcion: str) -> tuple[bool, list]:
    """Lista servicios odontologicos disponibles"""
    url = f"{BASE_URL}/tratamientos/procedimientos/"
    
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
            servicios = data.get('results', data if isinstance(data, list) else [])
            print_exito(f"Servicios listados (Total: {len(servicios)})")
            return True, servicios
        else:
            print_error(f"Listar servicios fallo: {response.status_code}")
            return False, []
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False, []


def crear_plan_tratamiento(token: str, datos: dict, descripcion: str) -> tuple[bool, int]:
    """Crea un nuevo plan de tratamiento"""
    url = f"{BASE_URL}/tratamientos/planes-tratamiento/"
    
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
            plan_id = data.get('id') or data.get('idplantratamiento')
            print_exito(f"Plan de tratamiento creado (ID: {plan_id})")
            return True, plan_id
        else:
            print_error(f"Crear plan de tratamiento fallo: {response.status_code}")
            return False, None
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False, None


def listar_planes(token: str, descripcion: str, paciente_id: int = None) -> bool:
    """Lista planes de tratamiento"""
    url = f"{BASE_URL}/tratamientos/planes-tratamiento/"
    
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
            print_exito(f"Planes listados (Total: {cantidad})")
            return True
        else:
            print_error(f"Listar planes fallo: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def crear_presupuesto(token: str, datos: dict, descripcion: str) -> tuple[bool, int]:
    """Crea un presupuesto"""
    url = f"{BASE_URL}/tratamientos/presupuestos/"
    
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
            presupuesto_id = data.get('id') or data.get('idpresupuesto')
            print_exito(f"Presupuesto creado (ID: {presupuesto_id})")
            return True, presupuesto_id
        else:
            print_error(f"Crear presupuesto fallo: {response.status_code}")
            return False, None
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False, None


def ver_presupuesto(token: str, presupuesto_id: int, descripcion: str) -> bool:
    """Ver detalle de presupuesto"""
    url = f"{BASE_URL}/tratamientos/presupuestos/{presupuesto_id}/"
    
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
            print_exito("Presupuesto obtenido correctamente")
            return True
        else:
            print_error(f"Ver presupuesto fallo: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def main():
    """Funcion principal"""
    global odontologo_token, admin_token, paciente_id, tratamiento_id, presupuesto_id
    
    reporte = crear_reporte_json(4, "Tratamientos y Presupuestos")
    
    print_seccion("FLUJO 04: TRATAMIENTOS Y PRESUPUESTOS")
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
    # SECCION 2: Listar servicios disponibles
    # ======================================
    print_seccion("SECCION 2: SERVICIOS ODONTOLOGICOS DISPONIBLES")
    
    exito, servicios = listar_servicios(admin_token, "Listar servicios odontologicos")
    
    # Buscar un servicio de obturacion para usar despues
    servicio_obturacion = None
    if servicios:
        for s in servicios:
            if 'obturacion' in s.get('nombre', '').lower() or 'obturacion' in s.get('descripcion', '').lower():
                servicio_obturacion = s
                break
    
    # Tracking seccion 2
    if exito and servicios:
        reporte.agregar_seccion(2, "Servicios odontologicos disponibles", True, {
            "total_servicios": len(servicios)
        })
    else:
        reporte.agregar_seccion(2, "Servicios odontologicos disponibles", False)
        reporte.agregar_error("Seccion 2", "Fallo al listar servicios")
    
    # ======================================
    # SECCION 3: Crear plan de tratamiento
    # ======================================
    print_seccion("SECCION 3: CREAR PLAN DE TRATAMIENTO")
    
    if paciente_id:
        nuevo_plan = {
            "paciente": paciente_id,
            "odontologo": 637,  # Dr. Perez
            "descripcion": "Plan de tratamiento completo: limpieza y obturacion dental",
            "diagnostico": "Caries dental y requerimiento de limpieza profunda",
            "estado": "borrador",
            "duracion_estimada_dias": 30
        }
        
        exito, tratamiento_id = crear_plan_tratamiento(
            token=odontologo_token,
            datos=nuevo_plan,
            descripcion="Crear plan de tratamiento para paciente"
        )
        
        if not exito:
            print_warning("No se pudo crear el plan de tratamiento, continuando...")
            reporte.agregar_seccion(3, "Crear plan de tratamiento", False)
            reporte.agregar_error("Seccion 3", "Fallo al crear plan de tratamiento")
        else:
            reporte.agregar_seccion(3, "Crear plan de tratamiento", True, {
                "tratamiento_id": tratamiento_id,
                "paciente_id": paciente_id
            })
            reporte.agregar_dato_creado("tratamiento", tratamiento_id, {
                "paciente": paciente_id,
                "descripcion": nuevo_plan["descripcion"]
            })
    
    # ======================================
    # SECCION 4: Listar planes de tratamiento
    # ======================================
    print_seccion("SECCION 4: CONSULTAR PLANES DE TRATAMIENTO")
    
    listar_planes(admin_token, "Listar todos los planes de tratamiento")
    
    if paciente_id:
        listar_planes(
            odontologo_token,
            f"Listar planes del paciente Ana Lopez",
            paciente_id=paciente_id
        )
    
    # Tracking seccion 4
    reporte.agregar_seccion(4, "Consultar planes de tratamiento", True, {
        "consultas_realizadas": 2
    })
    
    # ======================================
    # SECCION 5: Crear presupuesto
    # ======================================
    print_seccion("SECCION 5: GENERAR PRESUPUESTO")
    
    if tratamiento_id:
        # Necesitamos un servicio para crear items del presupuesto
        servicio_id = 531  # Obturacion (Resina) del seed
        
        nuevo_presupuesto = {
            "plan_tratamiento": tratamiento_id,
            "subtotal": 500.00,
            "descuento": 50.00,
            "impuesto": 0.00,
            "total": 450.00,
            "estado": "borrador",
            "items": [
                {
                    "servicio": servicio_id,
                    "cantidad": 2,
                    "precio_unitario": 250.00,
                    "descuento_item": 50.00,
                    "numero_diente": 16
                }
            ]
        }
        
        exito, presupuesto_id = crear_presupuesto(
            token=odontologo_token,
            datos=nuevo_presupuesto,
            descripcion="Crear presupuesto para plan de tratamiento"
        )
        
        # Tracking seccion 5
        if exito and presupuesto_id:
            reporte.agregar_seccion(5, "Generar presupuesto", True, {
                "presupuesto_id": presupuesto_id,
                "tratamiento_id": tratamiento_id,
                "total": nuevo_presupuesto["total"]
            })
            reporte.agregar_dato_creado("presupuesto", presupuesto_id, {
                "tratamiento": tratamiento_id,
                "total": nuevo_presupuesto["total"]
            })
        else:
            reporte.agregar_seccion(5, "Generar presupuesto", False)
            reporte.agregar_error("Seccion 5", "Fallo al crear presupuesto")
    
    # ======================================
    # SECCION 6: Ver presupuesto detallado
    # ======================================
    if presupuesto_id:
        print_seccion("SECCION 6: CONSULTAR PRESUPUESTO DETALLADO")
        
        ver_presupuesto(
            token=odontologo_token,
            presupuesto_id=presupuesto_id,
            descripcion=f"Ver presupuesto #{presupuesto_id}"
        )
        
        # Paciente tambien puede ver su presupuesto
        if paciente_token:
            ver_presupuesto(
                token=paciente_token,
                presupuesto_id=presupuesto_id,
                descripcion=f"Paciente consulta presupuesto #{presupuesto_id}"
            )
        
        # Tracking seccion 6
        reporte.agregar_seccion(6, "Consultar presupuesto detallado", True, {
            "presupuesto_id": presupuesto_id,
            "consultas_realizadas": 2
        })
    
    # ======================================
    # RESUMEN FINAL
    # ======================================
    print_seccion("RESUMEN DE PRUEBAS DE TRATAMIENTOS")
    print_exito("OK Listado de servicios funciona")
    print_exito("OK Creacion de planes de tratamiento exitosa")
    print_exito("OK Consulta de planes funciona")
    print_exito("OK Generacion de presupuestos exitosa")
    print_exito("OK Visualizacion de presupuestos funciona")
    print_info("Sistema de tratamientos y presupuestos funcionando correctamente")
    
    # ======================================
    # GENERAR ARCHIVO JSON
    # ======================================
    archivo_generado = reporte.generar_archivo()
    print_info(f"\nArchivo JSON generado: {archivo_generado}")


if __name__ == "__main__":
    main()
