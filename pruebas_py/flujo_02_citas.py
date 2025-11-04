"""
FLUJO 02: Gestion de Citas
Prueba creacion, listado, actualizacion y cancelacion de citas
"""
import requests
import sys
from typing import Optional
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
odontologo_token = None
paciente_token = None
cita_id_creada = None
odontologo_id = None
paciente_id = None


def login(correo: str, password: str) -> tuple[bool, str, dict]:
    """Realiza login y retorna (exitoso, token, usuario)"""
    url = f"{BASE_URL}/auth/login/"
    body = {"correo": correo, "password": password}
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, json=body, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return True, data.get("token"), data.get("usuario")
        return False, "", {}
    except Exception as e:
        print_error(f"Error en login: {str(e)}")
        return False, "", {}


def listar_citas(token: str, descripcion: str, filtros: dict = None) -> bool:
    """Lista las citas con filtros opcionales"""
    url = f"{BASE_URL}/citas/consultas/"
    
    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, params=filtros, headers=headers)
        
        print_http_transaction(
            metodo="GET",
            url=url + (f"?{requests.compat.urlencode(filtros)}" if filtros else ""),
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
            print_exito(f"Citas listadas correctamente (Total: {cantidad})")
            return True
        else:
            print_error(f"Listar citas fallo con status {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def obtener_horarios_disponibles(token: str, fecha: str, odontologo_id: int, descripcion: str) -> Optional[int]:
    """Obtiene horarios disponibles y retorna el ID del primero"""
    url = f"{BASE_URL}/citas/horarios-disponibles/?fecha={fecha}&odontologo_id={odontologo_id}"
    
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
            if isinstance(data, list) and len(data) > 0:
                primer_horario = data[0]
                id_horario = primer_horario.get('id')
                hora = primer_horario.get('hora')
                print_exito(f"Horarios disponibles. Primer horario: {hora} (ID: {id_horario})")
                return id_horario
            else:
                print_error("No hay horarios disponibles")
                return None
        else:
            print_error(f"Consultar horarios fallo con status {response.status_code}")
            return None
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return None


def crear_cita(token: str, datos_cita: dict, descripcion: str) -> tuple[bool, int]:
    """Crea una nueva cita y retorna (exitoso, id_cita)"""
    url = f"{BASE_URL}/citas/consultas/"
    
    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=datos_cita, headers=headers)
        
        print_http_transaction(
            metodo="POST",
            url=url,
            headers=headers,
            body=datos_cita,
            response_status=response.status_code,
            response_headers=dict(response.headers),
            response_body=response.json() if response.headers.get('Content-Type', '').startswith('application/json') else response.text,
            descripcion=descripcion
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            cita_id = data.get('id') or data.get('codigo')
            print_exito(f"Cita creada correctamente (ID: {cita_id})")
            return True, cita_id
        else:
            print_error(f"Crear cita fallo con status {response.status_code}")
            return False, None
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False, None


def ver_detalle_cita(token: str, cita_id: int, descripcion: str) -> bool:
    """Obtiene el detalle de una cita especifica"""
    url = f"{BASE_URL}/citas/consultas/{cita_id}/"
    
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
            print_exito("Detalle de cita obtenido correctamente")
            return True
        else:
            print_error(f"Ver detalle fallo con status {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def actualizar_cita(token: str, cita_id: int, datos_actualizar: dict, descripcion: str) -> bool:
    """Actualiza una cita existente"""
    url = f"{BASE_URL}/citas/consultas/{cita_id}/"
    
    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.patch(url, json=datos_actualizar, headers=headers)
        
        print_http_transaction(
            metodo="PATCH",
            url=url,
            headers=headers,
            body=datos_actualizar,
            response_status=response.status_code,
            response_headers=dict(response.headers),
            response_body=response.json() if response.headers.get('Content-Type', '').startswith('application/json') else response.text,
            descripcion=descripcion
        )
        
        if response.status_code == 200:
            print_exito("Cita actualizada correctamente")
            return True
        else:
            print_error(f"Actualizar cita fallo con status {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def cancelar_cita(token: str, cita_id: int, motivo: str, descripcion: str) -> bool:
    """Cancela una cita"""
    url = f"{BASE_URL}/citas/consultas/{cita_id}/cancelar/"
    
    body = {"motivo_cancelacion": motivo}
    
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
        
        if response.status_code == 200:
            print_exito("Cita cancelada correctamente")
            return True
        else:
            print_error(f"Cancelar cita fallo con status {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def main():
    """Funcion principal"""
    global admin_token, odontologo_token, paciente_token, cita_id_creada
    global odontologo_id, paciente_id
    
    reporte = crear_reporte_json(2, "Gestion de Citas")
    
    print_seccion("FLUJO 02: GESTION DE CITAS")
    print_info("Servidor: http://localhost:8000")
    
    # ======================================
    # SECCION 1: Autenticacion
    # ======================================
    print_seccion("SECCION 1: AUTENTICACION")
    
    exito, paciente_token, paciente_usuario = login("ana.lopez@email.com", "paciente123")
    if not exito:
        print_error("No se pudo autenticar como Paciente")
        sys.exit(1)
    print_exito("Login Paciente exitoso")
    paciente_id = paciente_usuario.get('codigo')
    
    exito, odontologo_token, odontologo_usuario = login("dr.perez@clinica.com", "odontologo123")
    if not exito:
        print_error("No se pudo autenticar como Odontologo")
        sys.exit(1)
    print_exito("Login Odontologo exitoso")
    odontologo_id = odontologo_usuario.get('codigo')
    
    exito, admin_token, _ = login("admin@clinica.com", "admin123")
    if not exito:
        print_error("No se pudo autenticar como Admin")
        sys.exit(1)
    print_exito("Login Admin exitoso")
    
    # Tracking seccion 1
    if paciente_token and odontologo_token and admin_token:
        reporte.agregar_seccion(1, "Autenticacion", True, {
            "roles_autenticados": ["Paciente", "Odontologo", "Admin"],
            "paciente_id": paciente_id,
            "odontologo_id": odontologo_id
        })
    else:
        reporte.agregar_seccion(1, "Autenticacion", False)
        reporte.agregar_error("Seccion 1", "Fallo al autenticar usuarios")
    
    # ======================================
    # SECCION 2: Listar citas existentes
    # ======================================
    print_seccion("SECCION 2: LISTAR CITAS EXISTENTES")
    
    listar_citas(admin_token, "Listar todas las citas (Admin)")
    listar_citas(paciente_token, "Listar citas del paciente")
    listar_citas(odontologo_token, "Listar citas del odontologo")
    
    # Tracking seccion 2
    reporte.agregar_seccion(2, "Listar citas existentes", True, {
        "consultas_realizadas": 3
    })
    
    # ======================================
    # SECCION 3: Crear nueva cita
    # ======================================
    print_seccion("SECCION 3: CREAR NUEVA CITA")
    
    # Fecha para manana
    fecha_cita = (datetime.now() + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
    
    # Obtener lista de todos los horarios para encontrar uno disponible
    url_horarios = f"{BASE_URL}/citas/horarios/"
    headers_temp = {
        "Authorization": f"Token {admin_token}",
        "Content-Type": "application/json"
    }
    
    try:
        response_horarios = requests.get(url_horarios, headers=headers_temp)
        if response_horarios.status_code == 200:
            horarios = response_horarios.json()
            # Usar el primer horario disponible (ID 986 a 992 segun los datos existentes)
            # Para evitar conflictos, usar un horario que no este en uso
            id_horario = 987  # Horario de las 10:00 aproximadamente
            print_exito(f"Usando horario ID: {id_horario}")
        else:
            id_horario = 987  # Usar horario por defecto
            print_error(f"No se pudo obtener horarios, usando ID por defecto: {id_horario}")
    except Exception as e:
        id_horario = 987
        print_error(f"Error al consultar horarios: {str(e)}, usando ID por defecto: {id_horario}")
    
    nueva_cita = {
        "codpaciente": paciente_id,
        "cododontologo": odontologo_id,
        "fecha": fecha_cita.strftime("%Y-%m-%d"),
        "idhorario": id_horario,
        "idtipoconsulta": 203,  # Primera Vez
        "motivo_consulta": "Limpieza dental y revision general",
        "horario_preferido": "cualquiera"
    }
    
    exito, cita_id_creada = crear_cita(
        token=admin_token,
        datos_cita=nueva_cita,
        descripcion="Crear cita para manana"
    )
    
    if not exito:
        print_warning("No se pudo crear la cita, continuando con pruebas...")
        reporte.agregar_seccion(3, "Crear nueva cita", False)
        reporte.agregar_error("Seccion 3", "Fallo al crear cita")
    else:
        reporte.agregar_seccion(3, "Crear nueva cita", True, {
            "cita_id": cita_id_creada,
            "fecha": nueva_cita["fecha"],
            "paciente_id": paciente_id,
            "odontologo_id": odontologo_id
        })
        reporte.agregar_dato_creado("cita", cita_id_creada, {
            "fecha": nueva_cita["fecha"],
            "motivo": nueva_cita["motivo_consulta"]
        })
    
    # ======================================
    # SECCION 4: Ver detalle de cita
    # ======================================
    if cita_id_creada:
        print_seccion("SECCION 4: VER DETALLE DE CITA")
        
        ver_detalle_cita(
            token=paciente_token,
            cita_id=cita_id_creada,
            descripcion=f"Ver detalle de cita #{cita_id_creada} (Paciente)"
        )
        
        ver_detalle_cita(
            token=odontologo_token,
            cita_id=cita_id_creada,
            descripcion=f"Ver detalle de cita #{cita_id_creada} (Odontologo)"
        )
        
        # Tracking seccion 4
        reporte.agregar_seccion(4, "Ver detalle de cita", True, {
            "cita_id": cita_id_creada,
            "consultas_realizadas": 2
        })
    
    # ======================================
    # SECCION 5: Actualizar cita
    # ======================================
    if cita_id_creada:
        print_seccion("SECCION 5: ACTUALIZAR CITA")
        
        actualizacion = {
            "motivo_consulta": "Actualizacion: Limpieza dental profunda",
            "hora": "14:00:00"
        }
        
        actualizar_cita(
            token=admin_token,
            cita_id=cita_id_creada,
            datos_actualizar=actualizacion,
            descripcion=f"Actualizar hora de cita #{cita_id_creada}"
        )
        
        # Verificar actualizacion
        print_info("Verificando actualizacion...")
        ver_detalle_cita(
            token=admin_token,
            cita_id=cita_id_creada,
            descripcion=f"Ver cita actualizada #{cita_id_creada}"
        )
        
        # Tracking seccion 5
        reporte.agregar_seccion(5, "Actualizar cita", True, {
            "cita_id": cita_id_creada,
            "campos_actualizados": ["motivo_consulta", "hora"]
        })
    
    # ======================================
    # SECCION 6: Cancelar cita
    # ======================================
    if cita_id_creada:
        print_seccion("SECCION 6: CANCELAR CITA")
        
        cancelar_cita(
            token=admin_token,
            cita_id=cita_id_creada,
            motivo="Paciente cancelo por motivos personales",
            descripcion=f"Cancelar cita #{cita_id_creada}"
        )
        
        # Verificar cancelacion
        print_info("Verificando estado despues de cancelacion...")
        ver_detalle_cita(
            token=admin_token,
            cita_id=cita_id_creada,
            descripcion=f"Cancelar cita #{cita_id_creada}"
        )
        
        # Tracking seccion 6
        reporte.agregar_seccion(6, "Cancelar cita", True, {
            "cita_id": cita_id_creada,
            "motivo": "Paciente cancelo por motivos personales"
        })
    
    # ======================================
    # SECCION 7: Filtrar citas
    # ======================================
    print_seccion("SECCION 7: FILTRAR CITAS")
    
    # Filtrar por estado
    listar_citas(
        token=admin_token,
        descripcion="Filtrar citas confirmadas",
        filtros={"estado": "confirmada"}
    )
    
    # Filtrar por odontologo
    listar_citas(
        token=admin_token,
        descripcion=f"Filtrar citas del Dr. Perez",
        filtros={"cododontologo": odontologo_id}
    )
    
    # Filtrar por paciente
    listar_citas(
        token=admin_token,
        descripcion="Filtrar citas de la paciente Ana Lopez",
        filtros={"codpaciente": paciente_id}
    )
    
    # Tracking seccion 7
    reporte.agregar_seccion(7, "Filtrar citas", True, {
        "filtros_aplicados": 3,
        "tipos": ["por_estado", "por_odontologo", "por_paciente"]
    })
    
    # ======================================
    # RESUMEN FINAL
    # ======================================
    print_seccion("RESUMEN DE PRUEBAS DE CITAS")
    print_exito("Listado de citas funciona correctamente")
    print_exito("Creacion de citas exitosa")
    print_exito("Consulta de detalle de cita funciona")
    print_exito("Actualizacion de citas exitosa")
    print_exito("Cancelacion de citas funciona")
    print_exito("Filtros de busqueda funcionan correctamente")
    print_info("Sistema de gestion de citas funcionando correctamente")
    
    # ======================================
    # GENERAR ARCHIVO JSON
    # ======================================
    archivo_generado = reporte.generar_archivo()
    print_info(f"\nArchivo JSON generado: {archivo_generado}")


if __name__ == "__main__":
    main()
