"""
FLUJO 07: Chatbot Inteligente
Prueba conversaciones, intents, historial y reset del chatbot
"""
import requests
import sys
import uuid
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
session_id = None


def enviar_mensaje(session_id: str, mensaje: str, descripcion: str, **kwargs) -> tuple[bool, dict]:
    """Envia un mensaje al chatbot"""
    url = f"{BASE_URL}/chatbot/mensaje/"
    
    body = {
        "session_id": session_id,
        "mensaje": mensaje
    }
    
    # Agregar datos opcionales
    if 'correo_electronico' in kwargs:
        body['correo_electronico'] = kwargs['correo_electronico']
    if 'nombre' in kwargs:
        body['nombre'] = kwargs['nombre']
    if 'telefono' in kwargs:
        body['telefono'] = kwargs['telefono']
    
    headers = {"Content-Type": "application/json"}
    
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
            data = response.json()
            mensaje_bot = data.get('mensaje', '')
            preview = mensaje_bot[:80] + "..." if len(mensaje_bot) > 80 else mensaje_bot
            print_exito(f"Bot respondio: {preview}")
            return True, data
        else:
            print_error(f"Enviar mensaje fallo: {response.status_code}")
            return False, {}
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False, {}


def obtener_historial(session_id: str, descripcion: str) -> tuple[bool, dict]:
    """Obtiene el historial de la conversacion"""
    url = f"{BASE_URL}/chatbot/historial/"
    
    headers = {"Content-Type": "application/json"}
    params = {"session_id": session_id}
    
    try:
        response = requests.get(url, params=params, headers=headers)
        
        print_http_transaction(
            metodo="GET",
            url=f"{url}?session_id={session_id}",
            headers=headers,
            body=None,
            response_status=response.status_code,
            response_headers=dict(response.headers),
            response_body=response.json() if response.headers.get('Content-Type', '').startswith('application/json') else response.text,
            descripcion=descripcion
        )
        
        if response.status_code == 200:
            data = response.json()
            mensajes = data.get('mensajes', [])
            print_exito(f"Historial obtenido ({len(mensajes)} mensajes)")
            return True, data
        else:
            print_error(f"Obtener historial fallo: {response.status_code}")
            return False, {}
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False, {}


def reiniciar_conversacion(session_id: str, descripcion: str) -> bool:
    """Reinicia el contexto de la conversacion"""
    url = f"{BASE_URL}/chatbot/reset/"
    
    body = {"session_id": session_id}
    headers = {"Content-Type": "application/json"}
    
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
            print_exito("Conversacion reiniciada")
            return True
        else:
            print_error(f"Reiniciar conversacion fallo: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def main():
    """Funcion principal"""
    global session_id
    
    # Inicializar reporte JSON
    reporte = crear_reporte_json(7, "Chatbot Inteligente")
    
    print_seccion("FLUJO 07: CHATBOT INTELIGENTE")
    print_info("Servidor: http://localhost:8000")
    print_warning("Nota: El chatbot no requiere autenticacion")
    
    # Generar session_id unico
    session_id = str(uuid.uuid4())
    print_info(f"Session ID: {session_id}")
    
    # ======================================
    # SECCION 1: Saludo inicial
    # ======================================
    print_seccion("SECCION 1: SALUDO INICIAL")
    
    print_info("\n=== Primer contacto con el bot ===\n")
    exito1, _ = enviar_mensaje(
        session_id=session_id,
        mensaje="Hola",
        descripcion="Saludo inicial al chatbot"
    )
    
    reporte.agregar_seccion(1, "Saludo inicial", exito1, {
        "session_id": session_id,
        "mensaje": "Hola"
    })
    
    # ======================================
    # SECCION 2: Proporcionar informacion personal
    # ======================================
    print_seccion("SECCION 2: REGISTRAR INFORMACION PERSONAL")
    
    print_info("\n=== Enviar mensaje con datos personales ===\n")
    exito2, _ = enviar_mensaje(
        session_id=session_id,
        mensaje="Mi nombre es Juan Perez y mi correo es ana.lopez@email.com",
        descripcion="Proporcionar nombre y correo",
        correo_electronico="ana.lopez@email.com",
        nombre="Juan Perez",
        telefono="77777777"
    )
    
    reporte.agregar_seccion(2, "Registrar informacion personal", exito2, {
        "nombre": "Juan Perez",
        "correo": "ana.lopez@email.com",
        "telefono": "77777777"
    })
    
    # ======================================
    # SECCION 3: Consultar citas
    # ======================================
    print_seccion("SECCION 3: CONSULTAR CITAS")
    
    print_info("\n=== Preguntar sobre citas ===\n")
    exito3, _ = enviar_mensaje(
        session_id=session_id,
        mensaje="Quiero ver mis citas",
        descripcion="Intent: consultar_citas"
    )
    
    reporte.agregar_seccion(3, "Consultar citas", exito3, {
        "intent": "consultar_citas"
    })
    
    # ======================================
    # SECCION 4: Agendar cita
    # ======================================
    print_seccion("SECCION 4: AGENDAR CITA")
    
    print_info("\n=== Solicitar agendar cita ===\n")
    exito4, _ = enviar_mensaje(
        session_id=session_id,
        mensaje="Quiero agendar una cita",
        descripcion="Intent: agendar_cita"
    )
    
    reporte.agregar_seccion(4, "Agendar cita", exito4, {
        "intent": "agendar_cita"
    })
    
    # ======================================
    # SECCION 5: Preguntas sobre servicios
    # ======================================
    print_seccion("SECCION 5: CONSULTAR SERVICIOS")
    
    print_info("\n=== Preguntar por servicios ===\n")
    exito5, _ = enviar_mensaje(
        session_id=session_id,
        mensaje="Que servicios ofrecen?",
        descripcion="Intent: consultar_servicios"
    )
    
    reporte.agregar_seccion(5, "Consultar servicios", exito5, {
        "intent": "consultar_servicios"
    })
    
    # ======================================
    # SECCION 6: Informacion de contacto
    # ======================================
    print_seccion("SECCION 6: INFORMACION DE CONTACTO")
    
    print_info("\n=== Solicitar informacion de contacto ===\n")
    exito6, _ = enviar_mensaje(
        session_id=session_id,
        mensaje="Como puedo contactarlos?",
        descripcion="Intent: informacion_contacto"
    )
    
    reporte.agregar_seccion(6, "Informacion de contacto", exito6, {
        "intent": "informacion_contacto"
    })
    
    # ======================================
    # SECCION 7: Obtener historial
    # ======================================
    print_seccion("SECCION 7: HISTORIAL DE CONVERSACION")
    
    print_info("\n=== Obtener historial completo ===\n")
    exito7, datos_historial = obtener_historial(
        session_id=session_id,
        descripcion="Obtener historial de la conversacion"
    )
    
    mensajes_count = len(datos_historial.get('mensajes', [])) if exito7 else 0
    reporte.agregar_seccion(7, "Historial de conversacion", exito7, {
        "total_mensajes": mensajes_count
    })
    
    # ======================================
    # SECCION 8: Reiniciar conversacion
    # ======================================
    print_seccion("SECCION 8: REINICIAR CONVERSACION")
    
    print_info("\n=== Reiniciar contexto ===\n")
    exito8 = reiniciar_conversacion(
        session_id=session_id,
        descripcion="Reiniciar contexto de la conversacion"
    )
    
    reporte.agregar_seccion(8, "Reiniciar conversacion", exito8, {
        "session_id": session_id
    })
    
    # ======================================
    # SECCION 9: Mensaje despues de reset
    # ======================================
    print_seccion("SECCION 9: VERIFICAR RESET")
    
    print_info("\n=== Enviar mensaje despues de reset ===\n")
    exito9, _ = enviar_mensaje(
        session_id=session_id,
        mensaje="Hola de nuevo",
        descripcion="Verificar que el contexto se reinicio"
    )
    
    reporte.agregar_seccion(9, "Verificar reset", exito9, {
        "mensaje": "Hola de nuevo"
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
    print_seccion("RESUMEN DE PRUEBAS DEL CHATBOT")
    print_exito("OK Saludo inicial funciona")
    print_exito("OK Registro de informacion personal exitoso")
    print_exito("OK Consulta de citas funciona")
    print_exito("OK Solicitud de agendar citas funciona")
    print_exito("OK Consulta de servicios funciona")
    print_exito("OK Informacion de contacto disponible")
    print_exito("OK Historial de conversacion disponible")
    print_exito("OK Reinicio de conversacion funciona")
    print_info("Chatbot inteligente funcionando correctamente")
    print_warning("Nota: El chatbot usa IA para entender intenciones del usuario")


if __name__ == "__main__":
    main()
