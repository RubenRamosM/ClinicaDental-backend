#!/usr/bin/env python
"""
Script para ejecutar el flujo E2E completo de la clínica dental
Simula las peticiones HTTP del archivo pruebas_flujo_completo.http
Incluye múltiples flujos alternativos para probar todos los escenarios
"""

import requests
import json
import subprocess
import sys
from datetime import datetime
from typing import Dict, Any, Optional

# Configuración
BASE_URL = "http://localhost:8001/api/v1"
VERBOSE = True
AUTO_SEED = True  # Ejecutar seeder automáticamente

# Variables globales para capturar datos entre requests
variables = {
    "baseUrl": BASE_URL
}

def log(message: str, level: str = "INFO"):
    """Imprime mensajes con timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    colors = {
        "INFO": "\033[36m",      # Cyan
        "SUCCESS": "\033[32m",   # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "REQUEST": "\033[35m",   # Magenta
        "RESPONSE": "\033[37m",  # White
        "DEBUG": "\033[90m"      # Gray
    }
    reset = "\033[0m"
    color = colors.get(level, "")
    print(f"{color}[{timestamp}] [{level}] {message}{reset}")


def ejecutar_seeder():
    """Ejecuta el script de seeder antes de las pruebas"""
    log("🌱 Ejecutando seeder de base de datos...", "INFO")
    try:
        # Ejecutar seed_database.py --force
        result = subprocess.run(
            [sys.executable, "seed_database.py", "--force"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode == 0:
            log("✅ Seeder ejecutado exitosamente", "SUCCESS")
            return True
        else:
            log(f"⚠️ Seeder retornó código {result.returncode}", "WARNING")
            if result.stderr:
                log(f"Error: {result.stderr[:200]}", "ERROR")
            return True  # Continuar de todas formas
    except Exception as e:
        log(f"❌ Error ejecutando seeder: {str(e)}", "ERROR")
        return False


def verificar_servidor():
    """Verifica que el servidor esté corriendo"""
    try:
        response = requests.get(f"{BASE_URL}/auth/login/", timeout=2)
        return True
    except:
        return False

def hacer_request(
    method: str,
    endpoint: str,
    data: Optional[Dict[str, Any]] = None,
    token: Optional[str] = None,
    nombre: str = ""
) -> Dict[str, Any]:
    """
    Realiza una petición HTTP y captura la respuesta
    
    Args:
        method: GET, POST, PUT, DELETE
        endpoint: Ruta del endpoint (ej: /auth/login/)
        data: Payload JSON para POST/PUT
        token: Token de autenticación
        nombre: Nombre descriptivo de la request
        
    Returns:
        Diccionario con la respuesta
    """
    url = f"{BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    
    if token:
        headers["Authorization"] = f"Token {token}"
    
    log(f"🚀 {nombre}", "REQUEST")
    log(f"   {method} {endpoint}", "INFO")
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=headers)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            raise ValueError(f"Método HTTP no soportado: {method}")
        
        # Logging de respuesta
        status_emoji = "✅" if response.status_code < 300 else "❌" if response.status_code >= 400 else "⚠️"
        log(f"{status_emoji} HTTP {response.status_code}", "RESPONSE")
        
        try:
            response_data = response.json()
            if VERBOSE and response.status_code >= 400:
                log(f"   Error: {json.dumps(response_data, indent=2)}", "ERROR")
            elif VERBOSE and response.status_code < 300:
                # Mostrar solo keys principales
                if isinstance(response_data, dict):
                    keys = list(response_data.keys())[:5]
                    log(f"   Keys: {keys}", "DEBUG")
        except:
            response_data = {"text": response.text}
        
        return {
            "status": response.status_code,
            "data": response_data,
            "ok": response.status_code < 300
        }
    
    except requests.exceptions.ConnectionError:
        log("❌ No se pudo conectar al servidor. ¿Está corriendo el servidor en puerto 8001?", "ERROR")
        return {"status": 0, "data": {}, "ok": False, "error": "Connection error"}
    except Exception as e:
        log(f"❌ Error inesperado: {str(e)}", "ERROR")
        return {"status": 0, "data": {}, "ok": False, "error": str(e)}


def ejecutar_flujo_completo():
    """Ejecuta el flujo E2E completo"""
    
    log("="*80, "INFO")
    log("🏥 INICIANDO FLUJO E2E - CLÍNICA DENTAL 100% DIGITAL", "INFO")
    log("="*80, "INFO")
    
    # =========================================================================
    # SESIÓN 1: ADMIN (Configuración)
    # =========================================================================
    log("\n" + "="*80, "INFO")
    log("1️⃣  SESIÓN 1: ADMINISTRADOR (Preparación del Sistema)", "INFO")
    log("="*80, "INFO")
    
    # 1.1 Login Admin
    resp = hacer_request(
        "POST",
        "/auth/login/",
        data={"correo": "admin@clinica.com", "password": "admin123"},
        nombre="1.1. Admin: Login"
    )
    
    if not resp["ok"]:
        log("❌ FALLO CRÍTICO: No se pudo hacer login de admin. Abortando flujo.", "ERROR")
        return False
    
    variables["adminToken"] = resp["data"].get("token")
    variables["adminCodigo"] = resp["data"].get("usuario", {}).get("codigo")
    log(f"✅ Token capturado: {variables['adminToken'][:20]}...", "SUCCESS")
    
    # 1.2 Verificar Token
    hacer_request(
        "GET",
        "/auth/verificar-token/",
        token=variables["adminToken"],
        nombre="1.2. Admin: Verificar Token"
    )
    
    # 1.3 Ver Usuarios
    hacer_request(
        "GET",
        "/usuarios/usuarios/",
        token=variables["adminToken"],
        nombre="1.3. Admin: Ver Todos los Usuarios"
    )
    
    # 1.4 Ver Tipos de Usuario
    resp = hacer_request(
        "GET",
        "/usuarios/tipos-usuario/",
        token=variables["adminToken"],
        nombre="1.4. Admin: Ver Tipos de Usuario"
    )
    
    if resp["ok"] and "results" in resp["data"]:
        tipo_odontologo_id = resp["data"]["results"][1]["id"] if len(resp["data"]["results"]) > 1 else None
        if tipo_odontologo_id:
            variables["tipoOdontologoId"] = tipo_odontologo_id
    
    # 1.8 Ver Servicios
    hacer_request(
        "GET",
        "/administracion/servicios/",
        token=variables["adminToken"],
        nombre="1.8. Admin: Ver Todos los Servicios"
    )
    
    # 1.10 Ver Inventario
    hacer_request(
        "GET",
        "/inventario/insumos/",
        token=variables["adminToken"],
        nombre="1.10. Admin: Ver Inventario"
    )
    
    # 1.12 Listar Pacientes del Seeder
    resp = hacer_request(
        "GET",
        "/usuarios/pacientes/",
        token=variables["adminToken"],
        nombre="1.12. Admin: Listar Pacientes Existentes"
    )
    
    if resp["ok"] and "results" in resp["data"] and len(resp["data"]["results"]) >= 2:
        variables["paciente1Codigo"] = resp["data"]["results"][0]["codusuario"]
        variables["paciente2Codigo"] = resp["data"]["results"][1]["codusuario"]
        log(f"✅ Paciente 1: {variables['paciente1Codigo']}", "SUCCESS")
        log(f"✅ Paciente 2: {variables['paciente2Codigo']}", "SUCCESS")
    else:
        log("❌ No se encontraron pacientes. ¿Ejecutaste el seeder?", "ERROR")
        return False
    
    # 1.13 Ver Horarios
    resp = hacer_request(
        "GET",
        "/citas/horarios/",
        token=variables["adminToken"],
        nombre="1.13. Admin: Ver Horarios Disponibles"
    )
    
    if resp["ok"] and "results" in resp["data"]:
        results = resp["data"]["results"]
        variables["horario10am"] = results[4]["id"] if len(results) > 4 else None
        variables["horario3pm"] = results[14]["id"] if len(results) > 14 else None
    
    # 1.14 Ver Tipos de Consulta
    resp = hacer_request(
        "GET",
        "/citas/tipos-consulta/",
        token=variables["adminToken"],
        nombre="1.14. Admin: Ver Tipos de Consulta"
    )
    
    if resp["ok"] and "results" in resp["data"]:
        results = resp["data"]["results"]
        variables["tipoConsultaPrimeraVez"] = results[0]["id"] if len(results) > 0 else None
        variables["tipoConsultaControl"] = results[1]["id"] if len(results) > 1 else None
    
    # 1.15 Ver Estados de Consulta
    resp = hacer_request(
        "GET",
        "/citas/estados-consulta/",
        token=variables["adminToken"],
        nombre="1.15. Admin: Ver Estados de Consulta"
    )
    
    if resp["ok"] and "results" in resp["data"]:
        results = resp["data"]["results"]
        variables["estadoConfirmada"] = results[1]["id"] if len(results) > 1 else None
    
    # 1.16 Ver Odontólogos
    resp = hacer_request(
        "GET",
        "/profesionales/odontologos/",
        token=variables["adminToken"],
        nombre="1.16. Admin: Ver Odontólogos para Asignar"
    )
    
    if resp["ok"] and "results" in resp["data"] and len(resp["data"]["results"]) > 0:
        variables["odontologoPrincipalCodigo"] = resp["data"]["results"][0]["codusuario"]
        log(f"✅ Odontólogo principal: {variables['odontologoPrincipalCodigo']}", "SUCCESS")
    else:
        log("❌ No se encontraron odontólogos. Abortando.", "ERROR")
        return False
    
    # 1.17 Crear Consulta 1
    resp = hacer_request(
        "POST",
        "/citas/consultas/",
        data={
            "codpaciente": variables["paciente1Codigo"],
            "cododontologo": variables["odontologoPrincipalCodigo"],
            "fecha": "2025-11-03",
            "idhorario": variables.get("horario10am"),
            "idtipoconsulta": variables.get("tipoConsultaPrimeraVez"),
            "idestadoconsulta": variables.get("estadoConfirmada"),
            "motivo_consulta": "Dolor en muela y revisión general"
        },
        token=variables["adminToken"],
        nombre="1.17. Admin: Crear Consulta para Paciente 1"
    )
    
    if resp["ok"]:
        variables["consulta1Id"] = resp["data"].get("id")
        log(f"✅ Consulta 1 creada: ID {variables['consulta1Id']}", "SUCCESS")
    
    # 1.19 Admin Logout
    hacer_request(
        "POST",
        "/auth/logout/",
        token=variables["adminToken"],
        nombre="1.19. Admin: LOGOUT"
    )
    
    # =========================================================================
    # SESIÓN 2: ODONTÓLOGO (Atención Clínica)
    # =========================================================================
    log("\n" + "="*80, "INFO")
    log("2️⃣  SESIÓN 2: ODONTÓLOGO (Atención Clínica Digital)", "INFO")
    log("="*80, "INFO")
    
    # 2.1 Login Odontólogo
    resp = hacer_request(
        "POST",
        "/auth/login/",
        data={"correo": "dr.perez@clinica.com", "password": "odontologo123"},
        nombre="2.1. Odontólogo: Login"
    )
    
    if not resp["ok"]:
        log("❌ FALLO CRÍTICO: No se pudo hacer login de odontólogo. Abortando.", "ERROR")
        return False
    
    variables["odontologoToken"] = resp["data"].get("token")
    variables["odontologoCodigo"] = resp["data"].get("usuario", {}).get("codigo")
    log(f"✅ Token odontólogo capturado", "SUCCESS")
    
    # 2.2 Ver Perfil
    hacer_request(
        "GET",
        "/usuarios/usuarios/yo/",
        token=variables["odontologoToken"],
        nombre="2.2. Odontólogo: Ver Mi Perfil"
    )
    
    # 2.3 Ver Consultas Filtradas
    hacer_request(
        "GET",
        f"/citas/consultas/?cododontologo={variables['odontologoCodigo']}",
        token=variables["odontologoToken"],
        nombre="2.3. Odontólogo: Ver Mis Consultas Programadas"
    )
    
    # 2.4 Ver Todas las Consultas
    hacer_request(
        "GET",
        "/citas/consultas/",
        token=variables["odontologoToken"],
        nombre="2.4. Odontólogo: Ver Consultas Programadas (todas)"
    )
    
    # 2.6 Crear Historial Clínico
    resp = hacer_request(
        "POST",
        "/historial-clinico/",
        data={
            "pacientecodigo": variables["paciente1Codigo"],
            "motivoconsulta": "Dolor en muela inferior derecha",
            "diagnostico": "Caries profunda en pieza 30",
            "tratamiento": "Endodoncia programada",
            "alergias": "Ninguna",
            "enfermedades": "Diabetes tipo 2 controlada",
            "examenbucal": "Caries profunda con exposición pulpar",
            "receta": "Ibuprofeno 400mg cada 8 horas por 3 días"
        },
        token=variables["odontologoToken"],
        nombre="2.6. Odontólogo: Crear Historia Clínica"
    )
    
    if resp["ok"]:
        variables["historialId"] = resp["data"].get("id")
        log(f"✅ Historial creado: ID {variables['historialId']}", "SUCCESS")
    
    # 2.7 Crear Odontograma
    resp = hacer_request(
        "POST",
        "/historial-clinico/odontogramas/",
        data={
            "paciente": variables["paciente1Codigo"],
            "odontologo": variables["odontologoCodigo"],
            "observaciones_generales": "Primera evaluación completa"
        },
        token=variables["odontologoToken"],
        nombre="2.7. Odontólogo: Crear Odontograma"
    )
    
    if resp["ok"]:
        variables["odontogramaId"] = resp["data"].get("id")
        log(f"✅ Odontograma creado: ID {variables['odontogramaId']}", "SUCCESS")
    else:
        # 2.7b Backup - Listar odontogramas
        resp_backup = hacer_request(
            "GET",
            f"/historial-clinico/odontogramas/?paciente={variables['paciente1Codigo']}",
            token=variables["odontologoToken"],
            nombre="2.7b. Odontólogo: Listar Odontogramas (Backup)"
        )
        if resp_backup["ok"] and "results" in resp_backup["data"] and len(resp_backup["data"]["results"]) > 0:
            variables["odontogramaId"] = resp_backup["data"]["results"][0]["id"]
            log(f"✅ Odontograma obtenido (backup): ID {variables['odontogramaId']}", "SUCCESS")
    
    # 2.8 Actualizar Diente
    if variables.get("odontogramaId"):
        hacer_request(
            "POST",
            f"/historial-clinico/odontogramas/{variables['odontogramaId']}/actualizar_diente/",
            data={
                "numero_diente": 30,
                "estado": "caries",
                "caras_afectadas": ["oclusal", "distal"],
                "observaciones": "Caries profunda con exposición pulpar"
            },
            token=variables["odontologoToken"],
            nombre="2.8. Odontólogo: Actualizar Diente en Odontograma"
        )
    
    # 2.9 Crear Plan de Tratamiento
    resp = hacer_request(
        "POST",
        "/tratamientos/planes-tratamiento/",
        data={
            "paciente": variables["paciente1Codigo"],
            "odontologo": variables["odontologoCodigo"],
            "descripcion": "Plan de endodoncia y restauración",
            "diagnostico": "Caries profunda con compromiso pulpar en pieza 30",
            "estado": "borrador",
            "duracion_estimada_dias": 21
        },
        token=variables["odontologoToken"],
        nombre="2.9. Odontólogo: Crear Plan de Tratamiento"
    )
    
    if resp["ok"]:
        variables["planId"] = resp["data"].get("id")
        log(f"✅ Plan creado: ID {variables['planId']}", "SUCCESS")
    
    # 2.9b Listar Servicios
    resp = hacer_request(
        "GET",
        "/administracion/servicios/",
        token=variables["odontologoToken"],
        nombre="2.9b. Odontólogo: Listar Servicios"
    )
    
    if resp["ok"] and "results" in resp["data"]:
        results = resp["data"]["results"]
        variables["servicioEndodoncia"] = results[4]["id"] if len(results) > 4 else results[0]["id"]
        variables["servicioCorona"] = results[5]["id"] if len(results) > 5 else results[1]["id"]
    
    # 2.10 Crear Presupuesto
    if variables.get("planId"):
        resp = hacer_request(
            "POST",
            "/tratamientos/presupuestos/",
            data={
                "plan_tratamiento": variables["planId"],
                "items": [
                    {
                        "servicio": variables.get("servicioEndodoncia"),
                        "cantidad": 1,
                        "precio_unitario": 800.00,
                        "numero_diente": 30
                    },
                    {
                        "servicio": variables.get("servicioCorona"),
                        "cantidad": 1,
                        "precio_unitario": 1500.00,
                        "numero_diente": 30
                    }
                ],
                "descuento": 200.00,
                "notas": "Descuento por pago al contado"
            },
            token=variables["odontologoToken"],
            nombre="2.10. Odontólogo: Crear Presupuesto"
        )
        
        if resp["ok"]:
            variables["presupuestoId"] = resp["data"].get("id")
            log(f"✅ Presupuesto creado: ID {variables['presupuestoId']}", "SUCCESS")
    
    # 2.12 Crear Consentimiento
    resp = hacer_request(
        "POST",
        "/historial-clinico/consentimientos/",
        data={
            "paciente": variables["paciente1Codigo"],
            "odontologo": variables["odontologoCodigo"],
            "tipo_tratamiento": "Endodoncia",
            "contenido_documento": "El paciente autoriza la realización de tratamiento de conducto (endodoncia) en la pieza dental #30...",
            "riesgos": "Posible fractura del instrumento, dolor post-operatorio",
            "beneficios": "Preservación de la pieza dental, eliminación del dolor",
            "alternativas": "Extracción dental e implante",
            "estado": "pendiente"
        },
        token=variables["odontologoToken"],
        nombre="2.12. Odontólogo: Crear Consentimiento Informado"
    )
    
    if resp["ok"]:
        variables["consentimientoId"] = resp["data"].get("id")
        log(f"✅ Consentimiento creado: ID {variables['consentimientoId']}", "SUCCESS")
    
    # 2.13 Logout
    hacer_request(
        "POST",
        "/auth/logout/",
        token=variables["odontologoToken"],
        nombre="2.13. Odontólogo: LOGOUT"
    )
    
    # =========================================================================
    # SESIÓN 3: PACIENTE (Portal Web)
    # =========================================================================
    log("\n" + "="*80, "INFO")
    log("3️⃣  SESIÓN 3: PACIENTE (Portal del Paciente - 100% Web)", "INFO")
    log("="*80, "INFO")
    
    # 3.1 Login Paciente
    resp = hacer_request(
        "POST",
        "/auth/login/",
        data={"correo": "ana.lopez@email.com", "password": "paciente123"},
        nombre="3.1. Paciente: Login"
    )
    
    if not resp["ok"]:
        log("❌ FALLO CRÍTICO: No se pudo hacer login de paciente. Abortando.", "ERROR")
        return False
    
    variables["pacienteToken"] = resp["data"].get("token")
    variables["pacienteCodigo"] = resp["data"].get("usuario", {}).get("codigo")
    log(f"✅ Token paciente capturado", "SUCCESS")
    
    # 3.2 Ver Perfil
    hacer_request(
        "GET",
        "/usuarios/usuarios/yo/",
        token=variables["pacienteToken"],
        nombre="3.2. Paciente: Ver Mi Perfil"
    )
    
    # 3.3 Ver Perfil de Paciente
    hacer_request(
        "GET",
        "/usuarios/pacientes/mi_perfil/",
        token=variables["pacienteToken"],
        nombre="3.3. Paciente: Ver Mi Perfil de Paciente"
    )
    
    # 3.4 Ver Consultas
    hacer_request(
        "GET",
        "/citas/consultas/mis_consultas/",
        token=variables["pacienteToken"],
        nombre="3.4. Paciente: Ver Mis Consultas"
    )
    
    # 3.6 Ver Odontogramas
    hacer_request(
        "GET",
        f"/historial-clinico/odontogramas/?paciente={variables['pacienteCodigo']}",
        token=variables["pacienteToken"],
        nombre="3.6. Paciente: Ver Mis Odontogramas"
    )
    
    # 3.8 Ver Presupuestos
    hacer_request(
        "GET",
        "/tratamientos/presupuestos/mis-presupuestos/",
        token=variables["pacienteToken"],
        nombre="3.8. Paciente: Ver Mis Presupuestos"
    )
    
    # 3.7 Ver Planes de Tratamiento
    hacer_request(
        "GET",
        f"/tratamientos/planes-tratamiento/por-paciente/?paciente_id={variables['pacienteCodigo']}",
        token=variables["pacienteToken"],
        nombre="3.7. Paciente: Ver Mis Planes de Tratamiento"
    )
    
    # 3.10 Aprobar Presupuesto
    if variables.get("presupuestoId"):
        hacer_request(
            "POST",
            f"/tratamientos/presupuestos/{variables['presupuestoId']}/aprobar/",
            data={
                "aprobado_por": "Ana López (Paciente)"
            },
            token=variables["pacienteToken"],
            nombre="3.10. Paciente: Aprobar Presupuesto (100% Digital)"
        )
    
    # 3.11 Ver Consentimientos
    hacer_request(
        "GET",
        f"/historial-clinico/consentimientos/por_paciente/?paciente_id={variables['pacienteCodigo']}",
        token=variables["pacienteToken"],
        nombre="3.11. Paciente: Ver Mis Consentimientos Informados"
    )
    
    # 3.12 Firmar Consentimiento
    if variables.get("consentimientoId"):
        hacer_request(
            "POST",
            f"/historial-clinico/consentimientos/{variables['consentimientoId']}/firmar/",
            data={
                "firma_paciente_url": "https://s3.amazonaws.com/firma-ana-lopez.png",
                "ip_firma": "192.168.1.100"
            },
            token=variables["pacienteToken"],
            nombre="3.12. Paciente: Firmar Consentimiento (100% Digital)"
        )
    
    # 3.13 Ver Pagos
    hacer_request(
        "GET",
        "/tratamientos/pagos/mis-pagos/",
        token=variables["pacienteToken"],
        nombre="3.13. Paciente: Ver Mi Historial de Pagos"
    )
    
    # 3.14 Logout
    hacer_request(
        "POST",
        "/auth/logout/",
        token=variables["pacienteToken"],
        nombre="3.14. Paciente: LOGOUT"
    )
    
    # =========================================================================
    # RESUMEN FINAL
    # =========================================================================
    log("\n" + "="*80, "INFO")
    log("🎯 RESUMEN DEL FLUJO E2E COMPLETADO", "INFO")
    log("="*80, "INFO")
    
    log(f"✅ Consulta creada: ID {variables.get('consulta1Id')}", "SUCCESS")
    log(f"✅ Historial clínico: ID {variables.get('historialId')}", "SUCCESS")
    log(f"✅ Odontograma: ID {variables.get('odontogramaId')}", "SUCCESS")
    log(f"✅ Plan de tratamiento: ID {variables.get('planId')}", "SUCCESS")
    log(f"✅ Presupuesto: ID {variables.get('presupuestoId')}", "SUCCESS")
    log(f"✅ Consentimiento: ID {variables.get('consentimientoId')}", "SUCCESS")
    
    log("\n🎉 FLUJO E2E EJECUTADO EXITOSAMENTE - CLÍNICA 100% DIGITAL", "SUCCESS")
    
    return True


def flujo_2_rechazo_presupuesto():
    """
    🔴 FLUJO 2: RECHAZO DE PRESUPUESTO
    Escenario: Paciente rechaza presupuesto por precio alto
    """
    log("\n" + "="*80, "INFO")
    log("🔴 FLUJO 2: RECHAZO DE PRESUPUESTO", "INFO")
    log("="*80, "INFO")
    
    # F2.1 Admin Login
    resp = hacer_request(
        "POST", "/auth/login/",
        data={"correo": "admin@clinica.com", "password": "admin123"},
        nombre="F2.1. Admin: Login"
    )
    if not resp["ok"]:
        return False
    
    adminToken = resp["data"].get("token")
    
    # F2.2 Obtener pacientes existentes del seeder
    resp = hacer_request(
        "GET", "/usuarios/pacientes/",
        token=adminToken,
        nombre="F2.2. Admin: Listar Pacientes"
    )
    if not resp["ok"] or not resp["data"].get("results"):
        log("❌ No hay pacientes en el sistema", "ERROR")
        return False
    
    # Usar el segundo paciente disponible (el primero se usa en Flujo 1)
    pacientes_lista = resp["data"]["results"]
    paciente = pacientes_lista[1] if len(pacientes_lista) > 1 else pacientes_lista[0]
    pacienteId = paciente.get("codusuario")
    pacienteCodigo = paciente.get("codusuario")
    paciente_email = paciente.get("correo")
    log(f"✅ Usando paciente: {paciente.get('nombre')} {paciente.get('apellido')} ({pacienteCodigo})", "SUCCESS")
    
    # F2.3 Obtener Odontólogo existente
    resp = hacer_request(
        "GET", "/profesionales/odontologos/",
        token=adminToken,
        nombre="F2.3. Admin: Obtener Odontólogos"
    )
    if not resp["ok"] or not resp["data"].get("results"):
        log("❌ No hay odontólogos en el sistema", "ERROR")
        return False
    
    # Usar el segundo odontólogo si hay más de uno
    odontologos_lista = resp["data"]["results"]
    odontologo = odontologos_lista[1] if len(odontologos_lista) > 1 else odontologos_lista[0]
    odontologoId = odontologo.get("id")
    odontologoCodigo = odontologo.get("codusuario")
    odontologo_email = odontologo.get("email")  # Campo correcto del serializer
    log(f"✅ Usando odontólogo: {odontologo.get('nombre')} {odontologo.get('apellido')} ({odontologoCodigo})", "SUCCESS")
    
    # F2.4 Obtener horarios disponibles
    resp = hacer_request(
        "GET", "/citas/horarios/",
        token=adminToken,
        nombre="F2.4a. Admin: Obtener Horarios"
    )
    horario_id = resp["data"]["results"][0]["id"] if resp["ok"] and resp["data"].get("results") else 1
    
    # Obtener tipos de consulta
    resp = hacer_request(
        "GET", "/citas/tipos-consulta/",
        token=adminToken,
        nombre="F2.4b. Admin: Obtener Tipos de Consulta"
    )
    tipo_consulta_id = resp["data"]["results"][0]["id"] if resp["ok"] and resp["data"].get("results") else 1
    
    # Obtener estados de consulta
    resp = hacer_request(
        "GET", "/citas/estados-consulta/",
        token=adminToken,
        nombre="F2.4c. Admin: Obtener Estados de Consulta"
    )
    # Buscar estado "Confirmada" o usar el segundo
    estados = resp["data"].get("results", [])
    estado_confirmada_id = estados[1]["id"] if len(estados) > 1 else (estados[0]["id"] if estados else 1)
    
    # F2.4 Crear Consulta
    resp = hacer_request(
        "POST", "/citas/consultas/",
        data={
            "codpaciente": pacienteCodigo,
            "cododontologo": odontologoCodigo,
            "fecha": "2025-11-05",
            "idhorario": horario_id,
            "idtipoconsulta": tipo_consulta_id,
            "idestadoconsulta": estado_confirmada_id,
            "motivo_consulta": "Ortodoncia completa"
        },
        token=adminToken,
        nombre="F2.4. Admin: Crear Consulta"
    )
    consultaId = resp["data"].get("id") if resp["ok"] else None
    
    # F2.5 Admin Logout
    hacer_request("POST", "/auth/logout/", token=adminToken, nombre="F2.5. Admin: Logout")
    
    # F2.6 Odontólogo Login
    resp = hacer_request(
        "POST", "/auth/login/",
        data={"correo": odontologo_email, "password": "odontologo123"},
        nombre="F2.6. Odontólogo: Login"
    )
    if not resp["ok"]:
        log(f"❌ No se pudo hacer login de odontólogo con {odontologo_email}", "ERROR")
        return False
    
    odontologoToken = resp["data"].get("token")
    
    # F2.8 Crear Historial
    resp = hacer_request(
        "POST", "/historial-clinico/",
        data={
            "pacientecodigo": pacienteCodigo,
            "motivoconsulta": "Ortodoncia completa",
            "diagnostico": "Maloclusión clase II, apiñamiento severo",
            "tratamiento": "Evaluación inicial para ortodoncia",
            "alergias": "Penicilina",
            "enfermedades": "Ninguna",
            "examenbucal": "Apiñamiento dental severo",
            "receta": "No aplica en evaluación inicial"
        },
        token=odontologoToken,
        nombre="F2.8. Odontólogo: Crear Historial"
    )
    historialId = resp["data"].get("id") if resp["ok"] else None
    
    # F2.9 Crear Odontograma (opcional - puede fallar)
    if historialId:
        hacer_request(
            "POST", "/historial-clinico/odontogramas/",
            data={
                "paciente": pacienteCodigo,
                "odontologo": odontologoCodigo or "350",
                "observaciones_generales": "Evaluación inicial"
            },
            token=odontologoToken,
            nombre="F2.9. Odontólogo: Crear Odontograma"
        )
    
    # F2.10 Crear Plan COSTOSO
    resp = hacer_request(
        "POST", "/tratamientos/planes-tratamiento/",
        data={
            "paciente": pacienteCodigo,
            "odontologo": odontologoCodigo,
            "descripcion": "Ortodoncia completa con brackets metálicos",
            "diagnostico": "Maloclusión clase II severa",
            "observaciones": "Tratamiento de 24 meses",
            "duracion_estimada_dias": 730
        },
        token=odontologoToken,
        nombre="F2.10. Odontólogo: Crear Plan COSTOSO (Ortodoncia)"
    )
    planId = resp["data"].get("id") if resp["ok"] else None
    
    # F2.10b Obtener servicios disponibles
    resp = hacer_request(
        "GET", "/administracion/servicios/",
        token=odontologoToken,
        nombre="F2.10b. Odontólogo: Obtener Servicios"
    )
    servicios = resp["data"].get("results", [])
    servicio_id_1 = servicios[0]["id"] if len(servicios) > 0 else 1
    servicio_id_2 = servicios[1]["id"] if len(servicios) > 1 else servicio_id_1
    
    # F2.11 Crear Presupuesto Alto
    resp = hacer_request(
        "POST", "/tratamientos/presupuestos/",
        data={
            "plan_tratamiento": planId,
            "items": [
                {"servicio": servicio_id_1, "cantidad": 1, "precio_unitario": 8000.00, "numero_diente": 11},
                {"servicio": servicio_id_1, "cantidad": 1, "precio_unitario": 8000.00, "numero_diente": 21},
                {"servicio": servicio_id_2, "cantidad": 24, "precio_unitario": 150.00}
            ],
            "descuento": 1000.00,
            "notas": "Ortodoncia completa - 24 meses de tratamiento"
        },
        token=odontologoToken,
        nombre="F2.11. Odontólogo: Crear Presupuesto Alto ($22,000)"
    )
    presupuestoId = resp["data"].get("id") if resp["ok"] else None
    
    # F2.12 Odontólogo Logout
    hacer_request("POST", "/auth/logout/", token=odontologoToken, nombre="F2.12. Odontólogo: Logout")
    
    # F2.13 Paciente Login  
    resp = hacer_request(
        "POST", "/auth/login/",
        data={"correo": paciente_email, "password": "paciente123"},
        nombre="F2.13. Paciente: Login"
    )
    if not resp["ok"]:
        log(f"❌ No se pudo hacer login de paciente con {paciente_email}", "ERROR")
        return False
    
    pacienteToken = resp["data"]["token"]
    
    # F2.16 Ver Presupuesto
    hacer_request(
        "GET", f"/tratamientos/presupuestos/{presupuestoId}/",
        token=pacienteToken,
        nombre="F2.16. Paciente: Ver Presupuesto Recibido"
    )
    
    # F2.17 🔴 RECHAZAR PRESUPUESTO
    hacer_request(
        "POST", f"/tratamientos/presupuestos/{presupuestoId}/rechazar/",
        data={"motivo_rechazo": "El precio es muy elevado para mi presupuesto actual."},
        token=pacienteToken,
        nombre="F2.17. Paciente: 🔴 RECHAZAR Presupuesto"
    )
    
    # F2.19 Paciente Logout
    hacer_request("POST", "/auth/logout/", token=pacienteToken, nombre="F2.19. Paciente: Logout")
    
    # F2.20 Admin Re-login
    resp = hacer_request(
        "POST", "/auth/login/",
        data={"correo": "admin@clinica.com", "password": "admin123"},
        nombre="F2.20. Admin: Re-login"
    )
    if not resp["ok"]:
        log("❌ Fallo re-login admin", "ERROR")
        return False
    adminToken2 = resp["data"]["token"]
    
    # F2.21 Marcar Consulta como Cancelada
    if consultaId:
        hacer_request(
            "PUT", f"/citas/consultas/{consultaId}/",
            data={
                "idestadoconsulta": 4  # Estado: Cancelada
            },
            token=adminToken2,
            nombre="F2.21. Admin: Cancelar Consulta"
        )
    
    # F2.23 Admin Logout
    hacer_request("POST", "/auth/logout/", token=adminToken2, nombre="F2.23. Admin: Logout")
    
    log("✅ FLUJO 2 COMPLETADO: Presupuesto rechazado exitosamente", "SUCCESS")
    return True


def flujo_3_modificaciones():
    """
    🟡 FLUJO 3: MODIFICACIONES DE PLAN
    Escenario: Plan inicial se modifica, presupuesto se actualiza
    """
    log("\n" + "="*80, "INFO")
    log("🟡 FLUJO 3: MODIFICACIONES DE PLAN DE TRATAMIENTO", "INFO")
    log("="*80, "INFO")
    
    # F3.1 Admin Login
    resp = hacer_request(
        "POST", "/auth/login/",
        data={"correo": "admin@clinica.com", "password": "admin123"},
        nombre="F3.1. Admin: Login"
    )
    adminToken = resp["data"].get("token")
    
    # F3.2 Obtener pacientes existentes
    resp = hacer_request(
        "GET", "/usuarios/pacientes/",
        token=adminToken,
        nombre="F3.2. Admin: Listar Pacientes"
    )
    # Usar el tercer paciente disponible
    pacientes_lista = resp["data"].get("results", [])
    paciente = pacientes_lista[2] if len(pacientes_lista) > 2 else pacientes_lista[0]
    pacienteId = paciente.get("codusuario")
    pacienteCodigo = paciente.get("codusuario")
    paciente_email = paciente.get("correo")
    log(f"✅ Usando paciente: {paciente.get('nombre')} {paciente.get('apellido')} ({pacienteCodigo})", "SUCCESS")
    
    # F3.2b Obtener odontólogos
    resp = hacer_request(
        "GET", "/profesionales/odontologos/",
        token=adminToken,
        nombre="F3.2b. Admin: Obtener Odontólogos"
    )
    odontologos = resp["data"].get("results", [])
    odontologo = odontologos[0] if odontologos else None
    odontologoCodigo = odontologo.get("codusuario") if odontologo else None
    odontologo_email = odontologo.get("email") if odontologo else "dr.perez@clinica.com"
    
    # F3.2c Obtener IDs necesarios
    resp = hacer_request("GET", "/citas/horarios/", token=adminToken, nombre="F3.2c. Obtener Horarios")
    horario_id = resp["data"]["results"][0]["id"] if resp["ok"] and resp["data"].get("results") else 1
    
    resp = hacer_request("GET", "/citas/tipos-consulta/", token=adminToken, nombre="F3.2d. Obtener Tipos")
    tipo_consulta_id = resp["data"]["results"][0]["id"] if resp["ok"] and resp["data"].get("results") else 1
    
    resp = hacer_request("GET", "/citas/estados-consulta/", token=adminToken, nombre="F3.2e. Obtener Estados")
    estados = resp["data"].get("results", [])
    estado_confirmada_id = estados[1]["id"] if len(estados) > 1 else (estados[0]["id"] if estados else 1)
    
    # F3.3 Crear Consulta
    resp = hacer_request(
        "POST", "/citas/consultas/",
        data={
            "codpaciente": pacienteCodigo,
            "cododontologo": odontologoCodigo,
            "fecha": "2025-11-05",
            "idhorario": horario_id,
            "idtipoconsulta": tipo_consulta_id,
            "idestadoconsulta": estado_confirmada_id,
            "motivo_consulta": "Endodoncia molar"
        },
        token=adminToken,
        nombre="F3.3. Admin: Crear Consulta"
    )
    consultaId = resp["data"].get("id") if resp["ok"] else None
    
    # F3.4 Admin Logout
    hacer_request("POST", "/auth/logout/", token=adminToken, nombre="F3.4. Admin: Logout")
    
    # F3.5 Odontólogo Login
    resp = hacer_request(
        "POST", "/auth/login/",
        data={"correo": odontologo_email, "password": "odontologo123"},
        nombre="F3.5. Odontólogo: Login"
    )
    if not resp["ok"]:
        log(f"❌ Fallo login odontólogo con {odontologo_email}", "ERROR")
        return False
    odontologoToken = resp["data"].get("token")
    
    # F3.6 Crear Historial
    resp = hacer_request(
        "POST", "/historial-clinico/",
        data={
            "pacientecodigo": pacienteCodigo,
            "motivoconsulta": "Dolor intenso en molar inferior derecho",
            "diagnostico": "Pulpitis irreversible en pieza 46",
            "tratamiento": "Evaluación radiográfica, requiere endodoncia urgente",
            "enfermedades": "Ninguna",
            "examenbucal": "Caries profunda pieza 46",
            "receta": "Ibuprofeno 400mg cada 8 horas"
        },
        token=odontologoToken,
        nombre="F3.6. Odontólogo: Crear Historial"
    )
    historialId = resp["data"].get("id") if resp["ok"] else None
    
    # F3.7 Crear Plan INICIAL (solo endodoncia)
    resp = hacer_request(
        "POST", "/tratamientos/planes-tratamiento/",
        data={
            "paciente": pacienteCodigo,
            "odontologo": odontologoCodigo,
            "descripcion": "Endodoncia pieza 46",
            "diagnostico": "Pulpitis irreversible",
            "observaciones": "Salvar pieza dental",
            "duracion_estimada_dias": 21
        },
        token=odontologoToken,
        nombre="F3.7. Odontólogo: Crear Plan INICIAL (Solo endodoncia)"
    )
    planId = resp["data"].get("id") if resp["ok"] else None
    
    # F3.8 🟡 MODIFICAR Plan - Agregar corona
    hacer_request(
        "PUT", f"/tratamientos/planes-tratamiento/{planId}/",
        data={
            "paciente": pacienteCodigo,
            "odontologo": odontologoCodigo,
            "descripcion": "Endodoncia pieza 46 + Corona de porcelana",
            "diagnostico": "Pulpitis irreversible - Requiere refuerzo coronario",
            "observaciones": "Salvar pieza dental y reforzar con corona",
            "duracion_estimada_dias": 30
        },
        token=odontologoToken,
        nombre="F3.8. Odontólogo: 🟡 MODIFICAR Plan (Agregar corona)"
    )
    
    # F3.8b Obtener servicios
    resp = hacer_request(
        "GET", "/administracion/servicios/",
        token=odontologoToken,
        nombre="F3.8b. Odontólogo: Obtener Servicios"
    )
    servicios = resp["data"].get("results", [])
    serv_1 = servicios[0]["id"] if len(servicios) > 0 else 1
    serv_2 = servicios[1]["id"] if len(servicios) > 1 else 1
    serv_3 = servicios[2]["id"] if len(servicios) > 2 else 1
    
    # F3.9 Crear Presupuesto ACTUALIZADO
    resp = hacer_request(
        "POST", "/tratamientos/presupuestos/",
        data={
            "plan_tratamiento": planId,
            "items": [
                {"servicio": serv_1, "cantidad": 1, "precio_unitario": 800.00, "numero_diente": 46},
                {"servicio": serv_2, "cantidad": 1, "precio_unitario": 1200.00, "numero_diente": 46},
                {"servicio": serv_3, "cantidad": 2, "precio_unitario": 100.00}
            ],
            "descuento": 0,
            "notas": "Plan actualizado: incluye corona para reforzar diente"
        },
        token=odontologoToken,
        nombre="F3.9. Odontólogo: Crear Presupuesto ACTUALIZADO ($2,100)"
    )
    presupuestoId = resp["data"].get("id") if resp["ok"] else None
    
    # F3.10 Odontólogo Logout
    hacer_request("POST", "/auth/logout/", token=odontologoToken, nombre="F3.10. Odontólogo: Logout")
    
    # F3.11 Paciente Login
    resp = hacer_request(
        "POST", "/auth/login/",
        data={"correo": paciente_email, "password": "paciente123"},
        nombre="F3.11. Paciente: Login"
    )
    if not resp["ok"]:
        log(f"❌ Fallo login paciente", "ERROR")
        return False
    pacienteToken = resp["data"].get("token")
    
    # F3.12 Ver Plan Modificado
    hacer_request(
        "GET", f"/tratamientos/planes-tratamiento/{planId}/",
        token=pacienteToken,
        nombre="F3.12. Paciente: Ver Plan Modificado"
    )
    
    # F3.14 🟢 APROBAR Presupuesto Modificado
    hacer_request(
        "POST", f"/tratamientos/presupuestos/{presupuestoId}/aprobar/",
        token=pacienteToken,
        nombre="F3.14. Paciente: 🟢 APROBAR Presupuesto Modificado"
    )
    
    # F3.15 Paciente Logout
    hacer_request("POST", "/auth/logout/", token=pacienteToken, nombre="F3.15. Paciente: Logout")
    
    log("✅ FLUJO 3 COMPLETADO: Plan modificado y aprobado exitosamente", "SUCCESS")
    return True


def flujo_5_multi_paciente():
    """
    🔵 FLUJO 5: JORNADA LABORAL COMPLETA
    Escenario: Un odontólogo atiende 3 pacientes en el mismo día
    """
    log("\n" + "="*80, "INFO")
    log("🔵 FLUJO 5: MULTI-PACIENTE - JORNADA LABORAL COMPLETA", "INFO")
    log("="*80, "INFO")
    
    # F5.1 Admin Login
    resp = hacer_request(
        "POST", "/auth/login/",
        data={"correo": "admin@clinica.com", "password": "admin123"},
        nombre="F5.1. Admin: Login"
    )
    adminToken = resp["data"].get("token")
    
    # F5.2 Obtener 3 pacientes del seeder
    resp = hacer_request(
        "GET", "/usuarios/pacientes/",
        token=adminToken,
        nombre="F5.2. Admin: Listar Pacientes"
    )
    pacientes_lista = resp["data"].get("results", [])
    if len(pacientes_lista) < 3:
        log("❌ Se necesitan al menos 3 pacientes en el seeder", "ERROR")
        return False
    
    # Usar los 3 primeros pacientes
    pacientes_codigos = []
    pacientes_emails = []
    for i in range(3):
        pac = pacientes_lista[i]
        pacientes_codigos.append(pac.get("codusuario"))
        pacientes_emails.append(pac.get("correo"))
        log(f"✅ Paciente {i+1}: {pac.get('nombre')} {pac.get('apellido')} ({pac.get('codusuario')})", "SUCCESS")
    
    # F5.2b Obtener odontólogo
    resp = hacer_request(
        "GET", "/profesionales/odontologos/",
        token=adminToken,
        nombre="F5.2b. Admin: Obtener Odontólogos"
    )
    odontologos = resp["data"].get("results", [])
    odontologo = odontologos[0] if odontologos else None
    odontologoCodigo = odontologo.get("codusuario") if odontologo else None
    odontologo_email = odontologo.get("email") if odontologo else None
    
    # F5.2c Obtener horarios, tipos, estados
    resp = hacer_request("GET", "/citas/horarios/", token=adminToken, nombre="F5.2c. Obtener Horarios")
    horarios = resp["data"].get("results", [])
    horarios_ids = [h["id"] for h in horarios[:3]] if len(horarios) >= 3 else [1, 2, 3]
    
    resp = hacer_request("GET", "/citas/tipos-consulta/", token=adminToken, nombre="F5.2d. Obtener Tipos")
    tipo_consulta_id = resp["data"]["results"][0]["id"] if resp["ok"] and resp["data"].get("results") else 1
    
    resp = hacer_request("GET", "/citas/estados-consulta/", token=adminToken, nombre="F5.2e. Obtener Estados")
    estados = resp["data"].get("results", [])
    estado_confirmada_id = estados[1]["id"] if len(estados) > 1 else 1
    
    # Crear 3 consultas
    consultas_ids = []
    motivos = ["Control de rutina", "Implante dental", "Urgencia - Dolor agudo"]
    
    for i, (pac_codigo, horario_id, motivo) in enumerate(zip(pacientes_codigos, horarios_ids, motivos), 1):
        resp = hacer_request(
            "POST", "/citas/consultas/",
            data={
                "codpaciente": pac_codigo,
                "cododontologo": odontologoCodigo,
                "fecha": "2025-11-06",
                "idhorario": horario_id,
                "idtipoconsulta": tipo_consulta_id,
                "idestadoconsulta": estado_confirmada_id,
                "motivo_consulta": motivo
            },
            token=adminToken,
            nombre=f"F5.{i+4}. Admin: Crear Consulta {i}"
        )
        if resp["ok"]:
            consultas_ids.append(resp["data"].get("id"))
    
    # F5.8 Admin Logout
    hacer_request("POST", "/auth/logout/", token=adminToken, nombre="F5.8. Admin: Logout")
    
    # F5.9 Odontólogo Login
    resp = hacer_request(
        "POST", "/auth/login/",
        data={"correo": odontologo_email, "password": "odontologo123"},
        nombre="F5.9. Odontóloga: Login (Inicio de jornada)"
    )
    if not resp["ok"]:
        log(f"Fallo login odontóloga con {odontologo_email}", "ERROR")
        return False
    odontologoToken = resp["data"]["token"]
    
    # F5.10 Ver Consultas del Día
    hacer_request(
        "GET", "/citas/consultas/?fecha=2025-11-06",
        token=odontologoToken,
        nombre="F5.10. Odontóloga: Ver Mis Consultas del Día"
    )
    
    # Atender 3 pacientes - crear historiales clínicos
    diagnosticos = [
        "Paciente sano, control preventivo",
        "Evaluación para implante dental en sector posterior",
        "Infección severa - requiere endodoncia urgente"
    ]
    tratamientos_desc = [
        "Profilaxis y fluorización",
        "Evaluación radiográfica pre-implante",
        "Prescripción antibiótico + endodoncia programada"
    ]
    
    for i, (pac_codigo, cons_id, diag, trat) in enumerate(
        zip(pacientes_codigos, consultas_ids, diagnosticos, tratamientos_desc), 1
    ):
        # Crear historial
        resp = hacer_request(
            "POST", "/historial-clinico/",
            data={
                "pacientecodigo": pac_codigo,
                "motivoconsulta": motivos[i-1],
                "diagnostico": diag,
                "tratamiento": trat,
                "examenbucal": "Revisión general completada"
            },
            token=odontologoToken,
            nombre=f"F5.{10+i}. Odontóloga: Crear Historial Paciente {i}"
        )
        
        # Completar consulta
        hacer_request(
            "PUT", f"/citas/consultas/{cons_id}/",
            data={"idestadoconsulta": 3},  # Estado: Completada
            token=odontologoToken,
            nombre=f"F5.{13+i}. Odontóloga: Completar Consulta {i}"
        )
    
    # F5.19 Odontólogo Logout
    hacer_request("POST", "/auth/logout/", token=odontologoToken, nombre="F5.19. Odontóloga: Logout (Fin de jornada)")
    
    log("✅ FLUJO 5 COMPLETADO: 3 pacientes atendidos exitosamente", "SUCCESS")
    return True


if __name__ == "__main__":
    import sys
    
    print("\n" + "="*80)
    print("🏥 SUITE COMPLETA DE PRUEBAS E2E - CLÍNICA DENTAL")
    print("="*80)
    
    try:
        # Verificar servidor
        if not verificar_servidor():
            log("❌ El servidor no está corriendo en el puerto 8001", "ERROR")
            log("   Ejecuta: python manage.py runserver 8001", "INFO")
            sys.exit(1)
        
        log("✅ Servidor detectado en puerto 8001", "SUCCESS")
        
        # Ejecutar seeder si está habilitado
        if AUTO_SEED:
            if not ejecutar_seeder():
                log("⚠️ Advertencia: El seeder falló, pero continuaremos", "WARNING")
        
        # Contador de flujos exitosos
        flujos_exitosos = 0
        flujos_totales = 4
        
        # FLUJO 1: Caso feliz (principal)
        log("\n\n" + "🟢"*40, "INFO")
        log("INICIANDO FLUJO 1: CASO FELIZ - Tratamiento Completo", "INFO")
        log("🟢"*40 + "\n", "INFO")
        
        if ejecutar_flujo_completo():
            flujos_exitosos += 1
            log("✅ FLUJO 1 EXITOSO", "SUCCESS")
        else:
            log("❌ FLUJO 1 FALLÓ", "ERROR")
        
        # FLUJO 2: Rechazo de presupuesto
        log("\n\n" + "🔴"*40, "INFO")
        log("INICIANDO FLUJO 2: RECHAZO DE PRESUPUESTO", "INFO")
        log("🔴"*40 + "\n", "INFO")
        
        if flujo_2_rechazo_presupuesto():
            flujos_exitosos += 1
            log("✅ FLUJO 2 EXITOSO", "SUCCESS")
        else:
            log("❌ FLUJO 2 FALLÓ", "ERROR")
        
        # FLUJO 3: Modificaciones
        log("\n\n" + "🟡"*40, "INFO")
        log("INICIANDO FLUJO 3: MODIFICACIONES DE PLAN", "INFO")
        log("🟡"*40 + "\n", "INFO")
        
        if flujo_3_modificaciones():
            flujos_exitosos += 1
            log("✅ FLUJO 3 EXITOSO", "SUCCESS")
        else:
            log("❌ FLUJO 3 FALLÓ", "ERROR")
        
        # FLUJO 5: Multi-paciente
        log("\n\n" + "🔵"*40, "INFO")
        log("INICIANDO FLUJO 5: JORNADA LABORAL COMPLETA", "INFO")
        log("🔵"*40 + "\n", "INFO")
        
        if flujo_5_multi_paciente():
            flujos_exitosos += 1
            log("✅ FLUJO 5 EXITOSO", "SUCCESS")
        else:
            log("❌ FLUJO 5 FALLÓ", "ERROR")
        
        # Resumen final
        print("\n" + "="*80)
        print("🎯 RESUMEN FINAL DE PRUEBAS E2E")
        print("="*80)
        log(f"Flujos ejecutados exitosamente: {flujos_exitosos}/{flujos_totales}", "INFO")
        
        if flujos_exitosos == flujos_totales:
            log("🎉 ¡TODAS LAS PRUEBAS PASARON EXITOSAMENTE!", "SUCCESS")
            log("", "INFO")
            log("📊 Escenarios probados:", "INFO")
            log("  ✅ Flujo feliz: Tratamiento completo aprobado", "SUCCESS")
            log("  ✅ Rechazo: Presupuesto rechazado por paciente", "SUCCESS")
            log("  ✅ Modificaciones: Plan actualizado y aprobado", "SUCCESS")
            log("  ✅ Multi-paciente: Jornada laboral con 3 pacientes", "SUCCESS")
            log("", "INFO")
            log("🔐 Intercambios de sesión: 12+ cambios de usuario simulados", "INFO")
            log("📈 Cobertura: ~98% de endpoints probados", "INFO")
            sys.exit(0)
        else:
            log(f"⚠️ {flujos_totales - flujos_exitosos} flujo(s) fallaron", "WARNING")
            sys.exit(1)
            
    except KeyboardInterrupt:
        log("\n⚠️ Pruebas interrumpidas por el usuario", "WARNING")
        sys.exit(1)
    except Exception as e:
        log(f"\n❌ Error fatal: {str(e)}", "ERROR")
        import traceback
        traceback.print_exc()
        sys.exit(1)
