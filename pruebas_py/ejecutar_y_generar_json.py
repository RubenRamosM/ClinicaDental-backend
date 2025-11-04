"""
Script para ejecutar todos los flujos y generar archivos JSON con los resultados
Captura la salida de cada flujo y la guarda en formato legible para Copilot
"""
import subprocess
import sys
import os
import json
from datetime import datetime
import re

# Configuracion
FLUJOS = [
    {"numero": 1, "nombre": "Autenticacion", "archivo": "flujo_01_autenticacion.py", "descripcion": "Login, logout, perfiles"},
    {"numero": 2, "nombre": "Citas", "archivo": "flujo_02_citas.py", "descripcion": "CRUD de citas"},
    {"numero": 3, "nombre": "Historiales", "archivo": "flujo_03_historiales.py", "descripcion": "Historiales clinicos"},
    {"numero": 4, "nombre": "Tratamientos", "archivo": "flujo_04_tratamientos.py", "descripcion": "Tratamientos y presupuestos"},
    {"numero": 5, "nombre": "Facturacion", "archivo": "flujo_05_facturacion.py", "descripcion": "Facturas y pagos"},
    {"numero": 7, "nombre": "Chatbot", "archivo": "flujo_07_chatbot.py", "descripcion": "Chatbot inteligente"},
]

def extraer_secciones(salida_texto):
    """Extrae las secciones de la salida del flujo"""
    secciones = []
    
    # Buscar secciones (SECCION X: NOMBRE)
    patron_seccion = r'SECCION\s+(\d+):\s+([^\n]+)'
    matches = re.finditer(patron_seccion, salida_texto, re.MULTILINE | re.IGNORECASE)
    
    for match in matches:
        numero = int(match.group(1))
        nombre = match.group(2).strip()
        
        # Intentar determinar si fue exitosa buscando OK/ERROR despues
        posicion = match.end()
        siguiente_texto = salida_texto[posicion:posicion+2000]
        
        # Contar OK vs ERROR en esta seccion
        ok_count = len(re.findall(r'\[?OK\]?', siguiente_texto))
        error_count = len(re.findall(r'\[?ERROR\]?', siguiente_texto))
        
        exito = ok_count > error_count
        
        secciones.append({
            "numero": numero,
            "nombre": nombre,
            "exito": exito,
            "ok_count": ok_count,
            "error_count": error_count
        })
    
    return secciones

def extraer_datos_creados(salida_texto):
    """Extrae IDs creados de la salida"""
    datos = {}
    
    # Buscar patrones como "ID: 123", "creado (ID: 456)", etc.
    patron_id = r'(?:ID[:\s]+|id[:\s]+)(\d+)'
    matches = re.finditer(patron_id, salida_texto)
    
    ids_encontrados = []
    for match in matches:
        ids_encontrados.append(int(match.group(1)))
    
    if ids_encontrados:
        datos["ids_creados"] = list(set(ids_encontrados))  # Unicos
    
    return datos

def ejecutar_flujo(flujo_info):
    """Ejecuta un flujo y captura su salida"""
    numero = flujo_info["numero"]
    nombre = flujo_info["nombre"]
    archivo = flujo_info["archivo"]
    descripcion = flujo_info["descripcion"]
    
    print(f"\n{'='*80}")
    print(f"EJECUTANDO FLUJO {numero:02d}: {nombre}")
    print(f"{'='*80}\n")
    
    inicio = datetime.now()
    
    try:
        # Ejecutar el script y capturar salida
        result = subprocess.run(
            [sys.executable, archivo],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)),
            encoding='utf-8',
            errors='replace'
        )
        
        fin = datetime.now()
        duracion = (fin - inicio).total_seconds()
        
        # Mostrar salida en consola
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        # Analizar salida
        salida_completa = result.stdout + result.stderr
        secciones = extraer_secciones(salida_completa)
        datos_creados = extraer_datos_creados(salida_completa)
        
        # Calcular estadisticas
        total_secciones = len(secciones)
        secciones_exitosas = sum(1 for s in secciones if s["exito"])
        secciones_fallidas = total_secciones - secciones_exitosas
        tasa_exito = (secciones_exitosas / total_secciones * 100) if total_secciones > 0 else 0
        
        exito_general = result.returncode == 0
        
        # Crear estructura JSON
        resultado_json = {
            "flujo": {
                "numero": numero,
                "nombre": nombre,
                "archivo": archivo,
                "descripcion": descripcion
            },
            "ejecucion": {
                "inicio": inicio.isoformat(),
                "fin": fin.isoformat(),
                "duracion_segundos": round(duracion, 2),
                "fecha_legible": inicio.strftime("%d/%m/%Y %H:%M:%S"),
                "exit_code": result.returncode
            },
            "estadisticas": {
                "total_secciones": total_secciones,
                "secciones_exitosas": secciones_exitosas,
                "secciones_fallidas": secciones_fallidas,
                "tasa_exito_porcentaje": round(tasa_exito, 2)
            },
            "secciones": secciones,
            "datos_creados": datos_creados,
            "resumen": {
                "estado": "EXITOSO" if exito_general and secciones_fallidas == 0 else "CON_ERRORES",
                "mensaje": f"{secciones_exitosas} de {total_secciones} secciones exitosas" if total_secciones > 0 else "No se detectaron secciones"
            },
            "salida_completa": salida_completa
        }
        
        # Guardar JSON
        archivo_json = f"salida_flujo{numero:02d}.json"
        with open(archivo_json, 'w', encoding='utf-8') as f:
            json.dump(resultado_json, f, indent=2, ensure_ascii=False)
        
        print(f"\n[OK] Archivo JSON generado: {archivo_json}")
        
        return exito_general, resultado_json
        
    except Exception as e:
        print(f"\n[ERROR] No se pudo ejecutar flujo {numero:02d}: {str(e)}")
        return False, None

def main():
    """Funcion principal"""
    print(f"\n{'='*80}")
    print("EJECUCION AUTOMATICA DE TODOS LOS FLUJOS")
    print(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"{'='*80}\n")
    
    print(f"Se ejecutaran {len(FLUJOS)} flujos en total\n")
    print("NOTA: Asegurate de que:")
    print("  1. El servidor Django este corriendo en http://localhost:8000")
    print("  2. La base de datos este inicializada con seed_database.py")
    print()
    
    input("Presiona ENTER para continuar...")
    
    # Ejecutar todos los flujos
    resultados = []
    inicio_total = datetime.now()
    
    for flujo in FLUJOS:
        exito, resultado_json = ejecutar_flujo(flujo)
        resultados.append({
            "flujo": flujo["numero"],
            "nombre": flujo["nombre"],
            "exito": exito,
            "resultado": resultado_json
        })
    
    fin_total = datetime.now()
    duracion_total = (fin_total - inicio_total).total_seconds()
    
    # Resumen final
    print(f"\n{'='*80}")
    print("RESUMEN DE EJECUCION")
    print(f"{'='*80}\n")
    
    exitosos = sum(1 for r in resultados if r["exito"])
    fallidos = len(resultados) - exitosos
    
    print(f"Duracion total: {duracion_total:.2f} segundos")
    print(f"Total ejecutados: {len(resultados)}")
    print(f"Exitosos: {exitosos}")
    print(f"Fallidos: {fallidos}\n")
    
    for resultado in resultados:
        estado = "OK" if resultado["exito"] else "ERROR"
        print(f"  [{estado}] Flujo {resultado['flujo']:02d}: {resultado['nombre']}")
    
    # Crear resumen general JSON
    resumen_general = {
        "ejecucion": {
            "fecha": datetime.now().isoformat(),
            "fecha_legible": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "duracion_total_segundos": round(duracion_total, 2)
        },
        "estadisticas": {
            "total_flujos": len(resultados),
            "flujos_exitosos": exitosos,
            "flujos_fallidos": fallidos,
            "tasa_exito_porcentaje": round((exitosos / len(resultados) * 100), 2)
        },
        "flujos": [
            {
                "numero": r["flujo"],
                "nombre": r["nombre"],
                "exito": r["exito"],
                "archivo_salida": f"salida_flujo{r['flujo']:02d}.json"
            }
            for r in resultados
        ]
    }
    
    with open("resumen_ejecucion.json", 'w', encoding='utf-8') as f:
        json.dump(resumen_general, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*80}")
    print("Archivos JSON generados:")
    print(f"  - resumen_ejecucion.json (resumen general)")
    for r in resultados:
        print(f"  - salida_flujo{r['flujo']:02d}.json")
    print(f"{'='*80}\n")
    print("Puedes usar estos archivos para el Copilot del frontend")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()
