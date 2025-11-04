"""
FLUJO 08: PRUEBAS DE BITACORA/AUDITORIA
========================================
Este flujo prueba el sistema de auditoria (bitacora):
1. Autenticacion como administrador
2. Listar todos los registros de bitacora
3. Filtrar registros por usuario
4. Filtrar registros por tabla afectada
5. Obtener resumen de actividad
6. Obtener actividad reciente
7. Buscar en bitacora
"""

import requests
import sys
from json_output_helper import crear_reporte_json
from http_logger import (
    print_http_transaction,
    print_seccion,
    print_exito,
    print_error,
    print_info
)

BASE_URL = "http://localhost:8000"


def autenticar_admin():
    """Autenticar como administrador para acceder a bitacora."""
    print("\n=== SECCION 1: AUTENTICACION COMO ADMINISTRADOR ===")
    
    payload = {
        "correo": "admin@clinica.com",
        "password": "admin123"
    }
    
    url = f"{BASE_URL}/api/v1/auth/login/"
    
    print_http_transaction(
        metodo="POST",
        url=url,
        body=payload,
        descripcion="Login como administrador"
    )
    
    response = requests.post(url, json=payload)
    
    print_http_transaction(
        metodo="POST",
        url=url,
        body=payload,
        response_status=response.status_code,
        response_body=response.json() if response.status_code == 200 else response.text,
        descripcion="Respuesta del login"
    )
    
    if response.status_code == 200:
        data = response.json()
        token = data.get('token')  # Cambiar de 'access' a 'token'
        usuario = data.get('usuario', {})
        nombre = usuario.get('nombre_completo', usuario.get('correo', 'Admin'))
        print(f"✓ Login exitoso. Usuario: {nombre}")
        return True, token
    else:
        print("✗ Error en autenticacion")
        return False, None


def listar_bitacora(token):
    """Listar todos los registros de bitacora."""
    print("\n=== SECCION 2: LISTAR REGISTROS DE BITACORA ===")
    
    headers = {"Authorization": f"Token {token}"}  # Cambiar de Bearer a Token
    url = f"{BASE_URL}/api/v1/auditoria/"  # Sin /bitacora/
    
    print_http_transaction(
        metodo="GET",
        url=url,
        headers=headers,
        descripcion="Listar registros de bitacora"
    )
    
    response = requests.get(url, headers=headers)
    
    print_http_transaction(
        metodo="GET",
        url=url,
        headers=headers,
        response_status=response.status_code,
        response_body=response.json() if response.status_code == 200 else response.text,
        descripcion="Respuesta - Listado de bitacora"
    )
    
    if response.status_code == 200:
        data = response.json()
        registros = data.get('results', data if isinstance(data, list) else [])
        print(f"✓ Se encontraron {len(registros)} registros en la bitacora")
        
        if registros:
            print("\nUltimos 3 registros:")
            for registro in registros[:3]:
                print(f"  - {registro.get('fecha')}: {registro.get('usuario_email')} - {registro.get('accion')} en {registro.get('tabla_afectada')}")
        
        return True, len(registros)
    else:
        print("✗ Error al listar bitacora")
        return False, 0


def filtrar_por_usuario(token):
    """Filtrar registros de bitacora por usuario."""
    print("\n=== SECCION 3: FILTRAR REGISTROS POR USUARIO ===")
    
    headers = {"Authorization": f"Token {token}"}
    url_base = f"{BASE_URL}/api/v1/auditoria/"
    
    # Primero obtener un usuario_id de un registro existente
    response = requests.get(url_base, headers=headers)
    
    if response.status_code != 200:
        print("✗ No se pudo obtener registros previos")
        return False
    
    data = response.json()
    registros = data.get('results', data if isinstance(data, list) else [])
    
    if not registros:
        print("⚠ No hay registros en la bitacora para filtrar")
        return True  # No es error, simplemente no hay datos
    
    usuario_id = registros[0].get('usuario')
    usuario_email = registros[0].get('usuario_email', 'desconocido')
    
    print(f"\nFiltrando registros del usuario: {usuario_email} (ID: {usuario_id})")
    
    url = f"{BASE_URL}/api/v1/auditoria/por_usuario/?usuario_id={usuario_id}"
    
    print_http_transaction(
        metodo="GET",
        url=url,
        headers=headers,
        descripcion=f"Filtrar por usuario {usuario_id}"
    )
    
    response = requests.get(url, headers=headers)
    
    print_http_transaction(
        metodo="GET",
        url=url,
        headers=headers,
        response_status=response.status_code,
        response_body=response.json() if response.status_code == 200 else response.text,
        descripcion="Respuesta - Filtrado por usuario"
    )
    
    if response.status_code == 200:
        registros_usuario = response.json()
        print(f"✓ Se encontraron {len(registros_usuario)} registros del usuario {usuario_email}")
        return True
    else:
        print("✗ Error al filtrar por usuario")
        return False


def filtrar_por_tabla(token):
    """Filtrar registros de bitacora por tabla afectada."""
    print("\n=== SECCION 4: FILTRAR REGISTROS POR TABLA ===")
    
    headers = {"Authorization": f"Token {token}"}
    tabla = "consulta"
    url = f"{BASE_URL}/api/v1/auditoria/por_tabla/?tabla={tabla}"
    
    print_http_transaction(
        metodo="GET",
        url=url,
        headers=headers,
        descripcion=f"Filtrar por tabla '{tabla}'"
    )
    
    response = requests.get(url, headers=headers)
    
    print_http_transaction(
        metodo="GET",
        url=url,
        headers=headers,
        response_status=response.status_code,
        response_body=response.json() if response.status_code == 200 else response.text,
        descripcion="Respuesta - Filtrado por tabla"
    )
    
    if response.status_code == 200:
        registros_tabla = response.json()
        print(f"✓ Se encontraron {len(registros_tabla)} registros de la tabla '{tabla}'")
        
        if registros_tabla:
            acciones = {}
            for registro in registros_tabla:
                accion = registro.get('accion', 'desconocido')
                acciones[accion] = acciones.get(accion, 0) + 1
            
            print("\nAcciones registradas:")
            for accion, count in acciones.items():
                print(f"  - {accion}: {count}")
        
        return True
    else:
        print("✗ Error al filtrar por tabla")
        return False


def obtener_resumen(token):
    """Obtener resumen de actividad de la bitacora."""
    print("\n=== SECCION 5: OBTENER RESUMEN DE ACTIVIDAD ===")
    
    headers = {"Authorization": f"Token {token}"}
    url = f"{BASE_URL}/api/v1/auditoria/resumen/"
    
    print_http_transaction(
        metodo="GET",
        url=url,
        headers=headers,
        descripcion="Obtener resumen de actividad"
    )
    
    response = requests.get(url, headers=headers)
    
    print_http_transaction(
        metodo="GET",
        url=url,
        headers=headers,
        response_status=response.status_code,
        response_body=response.json() if response.status_code == 200 else response.text,
        descripcion="Respuesta - Resumen de actividad"
    )
    
    if response.status_code == 200:
        resumen = response.json()
        print(f"✓ Resumen obtenido exitosamente")
        print(f"\nEstadisticas:")
        print(f"  - Total de registros: {resumen.get('total_registros', 0)}")
        print(f"  - Ultimos 7 dias: {resumen.get('ultimos_7_dias', 0)}")
        print(f"  - Ultimos 30 dias: {resumen.get('ultimos_30_dias', 0)}")
        
        por_accion = resumen.get('por_accion', [])
        if por_accion:
            print("\nActividad por accion:")
            for item in por_accion[:5]:
                print(f"  - {item.get('accion')}: {item.get('total')}")
        
        por_tabla = resumen.get('por_tabla', [])
        if por_tabla:
            print("\nTablas mas afectadas:")
            for item in por_tabla[:5]:
                print(f"  - {item.get('tabla_afectada')}: {item.get('total')}")
        
        return True
    else:
        print("✗ Error al obtener resumen")
        return False


def obtener_actividad_reciente(token):
    """Obtener actividad reciente de la bitacora."""
    print("\n=== SECCION 6: OBTENER ACTIVIDAD RECIENTE ===")
    
    headers = {"Authorization": f"Token {token}"}
    url = f"{BASE_URL}/api/v1/auditoria/actividad-reciente/?limit=10"
    
    print_http_transaction(
        metodo="GET",
        url=url,
        headers=headers,
        descripcion="Obtener ultimos 10 registros"
    )
    
    response = requests.get(url, headers=headers)
    
    print_http_transaction(
        metodo="GET",
        url=url,
        headers=headers,
        response_status=response.status_code,
        response_body=response.json() if response.status_code == 200 else response.text,
        descripcion="Respuesta - Actividad reciente"
    )
    
    if response.status_code == 200:
        registros = response.json()
        print(f"✓ Se obtuvieron {len(registros)} registros recientes")
        
        if registros:
            print("\nActividad reciente:")
            for i, registro in enumerate(registros[:5], 1):
                print(f"  {i}. {registro.get('fecha')}: {registro.get('usuario_email')} - {registro.get('accion')} en {registro.get('tabla_afectada')}")
        
        return True
    else:
        print("✗ Error al obtener actividad reciente")
        return False


def buscar_en_bitacora(token):
    """Buscar en bitacora usando filtros avanzados."""
    print("\n=== SECCION 7: BUSCAR EN BITACORA ===")
    
    headers = {"Authorization": f"Token {token}"}
    
    # Buscar registros de accion CREATE
    url1 = f"{BASE_URL}/api/v1/auditoria/?accion=CREATE"
    
    print_http_transaction(
        metodo="GET",
        url=url1,
        headers=headers,
        descripcion="Buscar registros con accion CREATE"
    )
    
    response = requests.get(url1, headers=headers)
    
    print_http_transaction(
        metodo="GET",
        url=url1,
        headers=headers,
        response_status=response.status_code,
        response_body=response.json() if response.status_code == 200 else response.text,
        descripcion="Respuesta - Busqueda por accion CREATE"
    )
    
    if response.status_code == 200:
        data = response.json()
        registros = data.get('results', data if isinstance(data, list) else [])
        print(f"✓ Se encontraron {len(registros)} registros con accion CREATE")
        
        # Buscar por texto en detalles
        url2 = f"{BASE_URL}/api/v1/auditoria/?search=consulta"
        
        print_http_transaction(
            metodo="GET",
            url=url2,
            headers=headers,
            descripcion="Buscar texto 'consulta' en bitacora"
        )
        
        response2 = requests.get(url2, headers=headers)
        
        print_http_transaction(
            metodo="GET",
            url=url2,
            headers=headers,
            response_status=response2.status_code,
            response_body=response2.json() if response2.status_code == 200 else response2.text,
            descripcion="Respuesta - Busqueda de texto"
        )
        
        if response2.status_code == 200:
            data2 = response2.json()
            registros2 = data2.get('results', data2 if isinstance(data2, list) else [])
            print(f"✓ Se encontraron {len(registros2)} registros que contienen 'consulta'")
            return True
        else:
            print("✗ Error en busqueda de texto")
            return False
    else:
        print("✗ Error al buscar por accion")
        return False


def main():
    """Ejecutar el flujo completo de pruebas de bitacora."""
    print("=" * 60)
    print("FLUJO 08: PRUEBAS DE BITACORA/AUDITORIA")
    print("=" * 60)
    
    # Inicializar reporte JSON
    reporte = crear_reporte_json(8, "Pruebas de Bitacora y Auditoria")
    
    # SECCION 1: Autenticacion
    exito_auth, token = autenticar_admin()
    reporte.agregar_seccion(
        numero=1,
        nombre="Autenticacion como Administrador",
        exito=exito_auth
    )
    
    if not exito_auth:
        print("\n✗ No se puede continuar sin autenticacion")
        reporte.agregar_error("Autenticacion", "Fallo la autenticacion como administrador")
        archivo_generado = reporte.generar_archivo()
        print(f"\n✓ Reporte JSON generado: {archivo_generado}")
        return
    
    # SECCION 2: Listar bitacora
    exito_listar, total_registros = listar_bitacora(token)
    reporte.agregar_seccion(
        numero=2,
        nombre="Listar Registros de Bitacora",
        exito=exito_listar,
        detalles={"total_registros": total_registros}
    )
    
    # SECCION 3: Filtrar por usuario
    exito_usuario = filtrar_por_usuario(token)
    reporte.agregar_seccion(
        numero=3,
        nombre="Filtrar Registros por Usuario",
        exito=exito_usuario
    )
    
    # SECCION 4: Filtrar por tabla
    exito_tabla = filtrar_por_tabla(token)
    reporte.agregar_seccion(
        numero=4,
        nombre="Filtrar Registros por Tabla",
        exito=exito_tabla
    )
    
    # SECCION 5: Resumen
    exito_resumen = obtener_resumen(token)
    reporte.agregar_seccion(
        numero=5,
        nombre="Obtener Resumen de Actividad",
        exito=exito_resumen
    )
    
    # SECCION 6: Actividad reciente
    exito_reciente = obtener_actividad_reciente(token)
    reporte.agregar_seccion(
        numero=6,
        nombre="Obtener Actividad Reciente",
        exito=exito_reciente
    )
    
    # SECCION 7: Buscar
    exito_buscar = buscar_en_bitacora(token)
    reporte.agregar_seccion(
        numero=7,
        nombre="Buscar en Bitacora",
        exito=exito_buscar
    )
    
    # Generar reporte JSON
    archivo_generado = reporte.generar_archivo()
    
    print("\n" + "=" * 60)
    print("RESUMEN DEL FLUJO 08")
    print("=" * 60)
    print(f"Total de registros en bitacora: {total_registros}")
    print(f"Autenticacion: {'✓' if exito_auth else '✗'}")
    print(f"Listar bitacora: {'✓' if exito_listar else '✗'}")
    print(f"Filtrar por usuario: {'✓' if exito_usuario else '✗'}")
    print(f"Filtrar por tabla: {'✓' if exito_tabla else '✗'}")
    print(f"Resumen de actividad: {'✓' if exito_resumen else '✗'}")
    print(f"Actividad reciente: {'✓' if exito_reciente else '✗'}")
    print(f"Buscar en bitacora: {'✓' if exito_buscar else '✗'}")
    print(f"\n✓ Reporte JSON generado: {archivo_generado}")
    print("=" * 60)


if __name__ == "__main__":
    main()
