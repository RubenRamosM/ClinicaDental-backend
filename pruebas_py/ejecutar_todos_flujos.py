"""
Script maestro para ejecutar todos los flujos y generar archivos JSON
Ejecuta cada flujo en secuencia y genera salidas legibles para Copilot
"""
import subprocess
import sys
import os
from datetime import datetime

# Configuracion
FLUJOS = [
    {"numero": 1, "nombre": "Autenticacion", "archivo": "flujo_01_autenticacion.py"},
    {"numero": 2, "nombre": "Citas", "archivo": "flujo_02_citas.py"},
    {"numero": 3, "nombre": "Historiales", "archivo": "flujo_03_historiales.py"},
    {"numero": 4, "nombre": "Tratamientos", "archivo": "flujo_04_tratamientos.py"},
    {"numero": 5, "nombre": "Facturacion", "archivo": "flujo_05_facturacion.py"},
    {"numero": 7, "nombre": "Chatbot", "archivo": "flujo_07_chatbot.py"},
]

def print_separador():
    print("\n" + "=" * 80 + "\n")

def ejecutar_flujo(flujo_info):
    """Ejecuta un flujo individual"""
    numero = flujo_info["numero"]
    nombre = flujo_info["nombre"]
    archivo = flujo_info["archivo"]
    
    print_separador()
    print(f"EJECUTANDO FLUJO {numero:02d}: {nombre}")
    print_separador()
    
    try:
        # Ejecutar el script
        result = subprocess.run(
            [sys.executable, archivo],
            capture_output=False,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        if result.returncode == 0:
            print(f"\n[OK] Flujo {numero:02d} ejecutado exitosamente")
            return True
        else:
            print(f"\n[ERROR] Flujo {numero:02d} termino con errores (codigo: {result.returncode})")
            return False
            
    except Exception as e:
        print(f"\n[ERROR] No se pudo ejecutar flujo {numero:02d}: {str(e)}")
        return False

def main():
    """Funcion principal"""
    print_separador()
    print("EJECUCION AUTOMATICA DE TODOS LOS FLUJOS")
    print(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print_separador()
    
    print(f"\nSe ejecutaran {len(FLUJOS)} flujos en total")
    print("\nNOTA: Asegurate de que:")
    print("  1. El servidor Django este corriendo en http://localhost:8000")
    print("  2. La base de datos este inicializada con seed_database.py")
    print()
    
    input("Presiona ENTER para continuar...")
    
    # Ejecutar todos los flujos
    resultados = []
    for flujo in FLUJOS:
        exito = ejecutar_flujo(flujo)
        resultados.append({
            "flujo": flujo["numero"],
            "nombre": flujo["nombre"],
            "exito": exito
        })
    
    # Resumen final
    print_separador()
    print("RESUMEN DE EJECUCION")
    print_separador()
    
    exitosos = sum(1 for r in resultados if r["exito"])
    fallidos = len(resultados) - exitosos
    
    print(f"\nTotal ejecutados: {len(resultados)}")
    print(f"Exitosos: {exitosos}")
    print(f"Fallidos: {fallidos}")
    print()
    
    for resultado in resultados:
        estado = "OK" if resultado["exito"] else "ERROR"
        print(f"  [{estado}] Flujo {resultado['flujo']:02d}: {resultado['nombre']}")
    
    print_separador()
    print("Archivos JSON generados en el directorio pruebas_py/")
    print("Puedes usar estos archivos para el Copilot del frontend")
    print_separador()

if __name__ == "__main__":
    main()
