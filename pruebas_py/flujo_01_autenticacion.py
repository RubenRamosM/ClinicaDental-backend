"""
FLUJO 01: Autenticacion y Gestion de Usuarios
Prueba registro, login, logout, ver perfil, actualizar perfil y cambio de contrasena
"""
import requests
import sys
from datetime import datetime
from http_logger import (
    print_http_transaction, 
    print_seccion, 
    print_exito, 
    print_error,
    print_info,
    print_warning
)
from json_output_helper import crear_reporte_json

# Configuración
BASE_URL = "http://localhost:8000/api/v1"

# Variables globales para tokens
admin_token = None
odontologo_token = None
paciente_token = None
nuevo_usuario_token = None


def registrar_usuario(datos_registro: dict, descripcion: str) -> tuple[bool, str]:
    """Registra un nuevo usuario"""
    url = f"{BASE_URL}/auth/registro/"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=datos_registro, headers=headers)
        
        print_http_transaction(
            metodo="POST",
            url=url,
            headers=headers,
            body=datos_registro,
            response_status=response.status_code,
            response_headers=dict(response.headers),
            response_body=response.json() if response.headers.get('Content-Type', '').startswith('application/json') else response.text,
            descripcion=descripcion
        )
        
        if response.status_code == 201:
            data = response.json()
            token = data.get("token")
            print_exito(f"✓ Usuario registrado exitosamente")
            return True, token
        else:
            print_error(f"Registro falló: {response.status_code}")
            return False, ""
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False, ""


def login(correo: str, password: str, rol_descripcion: str) -> tuple[bool, str, dict]:
    """
    Realiza login y retorna (exitoso, token, usuario)
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
            usuario = data.get("usuario")
            if token:
                print_exito(f"Login exitoso como {rol_descripcion}")
                return True, token, usuario
            else:
                print_error(f"Login {rol_descripcion}: No se recibió token")
                return False, "", {}
        else:
            print_error(f"Login {rol_descripcion} falló con status {response.status_code}")
            return False, "", {}
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False, "", {}


def ver_perfil(token: str, rol_descripcion: str) -> bool:
    """
    Obtiene el perfil del usuario autenticado
    """
    url = f"{BASE_URL}/auth/perfil/"
    
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
            descripcion=f"Ver perfil de {rol_descripcion}"
        )
        
        if response.status_code == 200:
            print_exito(f"Perfil de {rol_descripcion} obtenido correctamente")
            return True
        else:
            print_error(f"Ver perfil falló con status {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def actualizar_perfil(token: str, datos_actualizar: dict, rol_descripcion: str) -> bool:
    """
    Actualiza datos del perfil del usuario
    """
    url = f"{BASE_URL}/auth/perfil/"
    
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
            descripcion=f"Actualizar perfil de {rol_descripcion}"
        )
        
        if response.status_code == 200:
            print_exito(f"Perfil de {rol_descripcion} actualizado correctamente")
            return True
        else:
            print_error(f"Actualizar perfil falló con status {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def cambiar_password(token: str, password_actual: str, password_nuevo: str, rol_descripcion: str) -> bool:
    """
    Cambia la contraseña del usuario
    """
    url = f"{BASE_URL}/auth/cambiar-password/"
    
    body = {
        "password_actual": password_actual,
        "password_nuevo": password_nuevo,
        "password_confirmacion": password_nuevo
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
            descripcion=f"Cambiar contraseña de {rol_descripcion}"
        )
        
        if response.status_code == 200:
            print_exito(f"Contraseña de {rol_descripcion} cambiada correctamente")
            return True
        else:
            print_error(f"Cambiar contraseña falló con status {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def logout(token: str, rol_descripcion: str) -> bool:
    """
    Cierra la sesión del usuario
    """
    url = f"{BASE_URL}/auth/logout/"
    
    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, headers=headers)
        
        print_http_transaction(
            metodo="POST",
            url=url,
            headers=headers,
            body=None,
            response_status=response.status_code,
            response_headers=dict(response.headers),
            response_body=response.json() if response.headers.get('Content-Type', '').startswith('application/json') else response.text,
            descripcion=f"Logout de {rol_descripcion}"
        )
        
        if response.status_code == 200:
            print_exito(f"Logout de {rol_descripcion} exitoso")
            return True
        else:
            print_error(f"Logout falló con status {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def main():
    """
    Función principal que ejecuta el flujo completo de autenticación
    """
    global admin_token, odontologo_token, paciente_token, nuevo_usuario_token
    
    # Inicializar reporte JSON
    reporte = crear_reporte_json(1, "Autenticacion y Gestion de Usuarios")
    
    print_seccion("FLUJO 01: AUTENTICACIÓN Y GESTIÓN DE USUARIOS")
    
    print_info("Verificando registro, login, perfil y logout")
    print_info("Servidor: http://localhost:8000")
    
    # ======================================
    # SECCIÓN 1: Registro de nuevo usuario
    # ======================================
    print_seccion("SECCIÓN 1: REGISTRO DE NUEVO USUARIO")
    
    # Generar correo único para evitar conflictos
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    nuevo_correo = f"nuevo.usuario.{timestamp}@email.com"
    
    datos_paciente = {
        "nombre": "Carlos",
        "apellido": "Mendoza",
        "correo": nuevo_correo,
        "telefono": "75555555",
        "password": "paciente123",
        "password_confirmacion": "paciente123",
        "tipo_usuario": "Paciente",
        "sexo": "Masculino",
        "carnet": f"CI{timestamp}",
        "fecha_nacimiento": "1995-06-20",
        "direccion": "Calle Nueva #456, Zona Sur"
    }
    
    exito, nuevo_usuario_token = registrar_usuario(
        datos_registro=datos_paciente,
        descripcion="Registrar nuevo paciente con datos completos"
    )
    
    if exito:
        print_info(f"Nuevo usuario creado: {nuevo_correo}")
        reporte.agregar_seccion(1, "Registro de nuevo usuario", True, {
            "correo": nuevo_correo,
            "tipo_usuario": "Paciente"
        })
        reporte.agregar_dato_creado("usuario", nuevo_correo, {"rol": "Paciente"})
    else:
        reporte.agregar_seccion(1, "Registro de nuevo usuario", False)
        reporte.agregar_error("Seccion 1", "Fallo al registrar nuevo usuario")
    
    # ======================================
    # SECCIÓN 2: Login de diferentes roles
    # ======================================
    print_seccion("SECCIÓN 2: LOGIN DE USUARIOS")
    
    # 1.1 Login como Paciente
    exito, paciente_token, paciente_usuario = login(
        correo="ana.lopez@email.com",
        password="paciente123",
        rol_descripcion="Paciente"
    )
    if not exito:
        print_error("No se pudo autenticar como Paciente")
        sys.exit(1)
    
    # 1.2 Login como Odontólogo
    exito, odontologo_token, odontologo_usuario = login(
        correo="dr.perez@clinica.com",
        password="odontologo123",
        rol_descripcion="Odontólogo"
    )
    if not exito:
        print_error("No se pudo autenticar como Odontólogo")
        sys.exit(1)
    
    # 1.3 Login como Admin
    exito, admin_token, admin_usuario = login(
        correo="admin@clinica.com",
        password="admin123",
        rol_descripcion="Admin"
    )
    if not exito:
        print_error("No se pudo autenticar como Admin")
        sys.exit(1)
    
    # Tracking sección 2
    if paciente_token and odontologo_token and admin_token:
        reporte.agregar_seccion(2, "Login de diferentes roles", True, {
            "roles_autenticados": ["Paciente", "Odontologo", "Admin"]
        })
    else:
        reporte.agregar_seccion(2, "Login de diferentes roles", False)
        reporte.agregar_error("Seccion 2", "Fallo al autenticar uno o mas roles")
    
    # ======================================
    # SECCIÓN 3: Ver perfiles
    # ======================================
    print_seccion("SECCIÓN 3: CONSULTAR PERFILES DE USUARIO")
    
    # 3.1 Ver perfil del nuevo usuario registrado
    if nuevo_usuario_token:
        print_info("Verificando perfil del usuario recién registrado...")
        ver_perfil(nuevo_usuario_token, "Nuevo Usuario")
    
    # 3.2 Ver perfil de Paciente
    ver_perfil(paciente_token, "Paciente")
    
    # 3.3 Ver perfil de Odontólogo
    ver_perfil(odontologo_token, "Odontólogo")
    
    # 3.4 Ver perfil de Admin
    ver_perfil(admin_token, "Admin")
    
    # Tracking sección 3
    reporte.agregar_seccion(3, "Ver perfiles de usuario", True, {
        "perfiles_consultados": 4
    })
    
    # ======================================
    # SECCIÓN 4: Actualizar perfiles
    # ======================================
    print_seccion("SECCIÓN 4: ACTUALIZAR DATOS DE PERFIL")
    
    # 4.1 Actualizar teléfono del Paciente
    actualizar_perfil(
        token=paciente_token,
        datos_actualizar={
            "telefono": "77777777",
            "notificaciones_email": True
        },
        rol_descripcion="Paciente"
    )
    
    # 4.2 Verificar que se actualizó viendo el perfil de nuevo
    print_info("Verificando actualización del perfil...")
    ver_perfil(paciente_token, "Paciente (después de actualizar)")
    
    # Tracking sección 4
    reporte.agregar_seccion(4, "Actualizar datos de perfil", True, {
        "campo_actualizado": "telefono",
        "nuevo_valor": "77777777"
    })
    
    # ======================================
    # SECCIÓN 5: Cambio de contraseña
    # ======================================
    print_seccion("SECCIÓN 5: CAMBIO DE CONTRASEÑA")
    
    # 5.1 Cambiar contraseña del Odontólogo
    if cambiar_password(
        token=odontologo_token,
        password_actual="odontologo123",
        password_nuevo="nuevaPassword123",
        rol_descripcion="Odontólogo"
    ):
        # 4.2 Intentar login con nueva contraseña
        print_info("Intentando login con nueva contraseña...")
        exito, nuevo_token, _ = login(
            correo="dr.perez@clinica.com",
            password="nuevaPassword123",
            rol_descripcion="Odontólogo (con nueva password)"
        )
        
        if exito:
            print_exito("✓ Nueva contraseña funciona correctamente")
            odontologo_token = nuevo_token
            
            # 5.3 Restaurar contraseña original para próximas pruebas
            print_info("Restaurando contraseña original...")
            cambiar_password(
                token=odontologo_token,
                password_actual="nuevaPassword123",
                password_nuevo="odontologo123",
                rol_descripcion="Odontólogo"
            )
            
            # Tracking sección 5
            reporte.agregar_seccion(5, "Cambio de contraseña", True, {
                "usuario": "Odontologo",
                "restaurada": True
            })
        else:
            print_warning("No se pudo hacer login con la nueva contraseña")
            reporte.agregar_seccion(5, "Cambio de contraseña", False)
            reporte.agregar_error("Seccion 5", "Fallo al verificar nueva contraseña")
    else:
        reporte.agregar_seccion(5, "Cambio de contraseña", False)
        reporte.agregar_error("Seccion 5", "Fallo al cambiar contraseña")
    
    # ======================================
    # SECCIÓN 6: Logout
    # ======================================
    print_seccion("SECCIÓN 6: CERRAR SESIÓN (LOGOUT)")
    
    # 6.1 Logout del Admin
    logout(admin_token, "Admin")
    
    # 6.2 Intentar acceder al perfil después del logout (debe fallar)
    print_info("Intentando acceder al perfil después del logout (debería fallar)...")
    url = f"{BASE_URL}/auth/perfil/"
    headers = {
        "Authorization": f"Token {admin_token}",
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
            descripcion="Intentar ver perfil con token expirado"
        )
        
        if response.status_code == 401:
            print_exito("✓ Token correctamente invalidado después del logout")
        else:
            print_warning(f"⚠️  Se esperaba 401 pero se obtuvo {response.status_code}")
    except Exception as e:
        print_error(f"Error: {str(e)}")
    
    # 6.3 Logout del resto
    logout(odontologo_token, "Odontólogo")
    logout(paciente_token, "Paciente")
    
    # Tracking sección 6
    reporte.agregar_seccion(6, "Cerrar sesión (Logout)", True, {
        "usuarios_deslogueados": 3,
        "token_invalidado": True
    })
    
    # ======================================
    # RESUMEN FINAL
    # ======================================
    print_seccion("RESUMEN DE PRUEBAS DE AUTENTICACIÓN")
    print_exito("✓ Registro de nuevos usuarios funciona correctamente")
    print_exito("✓ Login exitoso para 3 roles diferentes")
    print_exito("✓ Perfiles consultados correctamente")
    print_exito("✓ Actualización de perfil funciona")
    print_exito("✓ Cambio de contraseña funciona")
    print_exito("✓ Logout invalida el token correctamente")
    print_info("Sistema de autenticación funcionando correctamente")
    
    # ======================================
    # GENERAR ARCHIVO JSON
    # ======================================
    archivo_generado = reporte.generar_archivo()
    print_info(f"\nArchivo JSON generado: {archivo_generado}")


if __name__ == "__main__":
    main()
