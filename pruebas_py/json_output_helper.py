"""
Helper para generar salidas JSON de los flujos de prueba
Formato legible para Copilot del frontend
"""
import json
from datetime import datetime
from typing import Any, Dict, List


class JSONOutputHelper:
    """Clase para generar archivos JSON con los resultados de las pruebas"""
    
    def __init__(self, flujo_nombre: str, flujo_numero: int):
        self.flujo_nombre = flujo_nombre
        self.flujo_numero = flujo_numero
        self.inicio = datetime.now()
        self.secciones = []
        self.datos_creados = {}
        self.errores = []
        
    def agregar_seccion(self, numero: int, nombre: str, exito: bool, detalles: Dict[str, Any] = None):
        """Agrega una seccion al reporte"""
        seccion = {
            "numero": numero,
            "nombre": nombre,
            "exito": exito,
            "timestamp": datetime.now().isoformat(),
            "detalles": detalles or {}
        }
        self.secciones.append(seccion)
        
    def agregar_dato_creado(self, tipo: str, id_valor: Any, datos: Dict[str, Any] = None):
        """Registra un dato creado durante las pruebas"""
        if tipo not in self.datos_creados:
            self.datos_creados[tipo] = []
        
        self.datos_creados[tipo].append({
            "id": id_valor,
            "datos": datos or {},
            "timestamp": datetime.now().isoformat()
        })
        
    def agregar_error(self, seccion: str, mensaje: str, detalles: Dict[str, Any] = None):
        """Registra un error"""
        self.errores.append({
            "seccion": seccion,
            "mensaje": mensaje,
            "detalles": detalles or {},
            "timestamp": datetime.now().isoformat()
        })
        
    def generar_archivo(self, ruta_salida: str = None):
        """Genera el archivo JSON con los resultados"""
        fin = datetime.now()
        duracion = (fin - self.inicio).total_seconds()
        
        # Calcular estadisticas
        total_secciones = len(self.secciones)
        secciones_exitosas = sum(1 for s in self.secciones if s["exito"])
        secciones_fallidas = total_secciones - secciones_exitosas
        tasa_exito = (secciones_exitosas / total_secciones * 100) if total_secciones > 0 else 0
        
        resultado = {
            "flujo": {
                "numero": self.flujo_numero,
                "nombre": self.flujo_nombre,
                "descripcion": f"Resultados de la ejecucion del flujo {self.flujo_numero:02d}"
            },
            "ejecucion": {
                "inicio": self.inicio.isoformat(),
                "fin": fin.isoformat(),
                "duracion_segundos": round(duracion, 2),
                "fecha_legible": self.inicio.strftime("%d/%m/%Y %H:%M:%S")
            },
            "estadisticas": {
                "total_secciones": total_secciones,
                "secciones_exitosas": secciones_exitosas,
                "secciones_fallidas": secciones_fallidas,
                "tasa_exito_porcentaje": round(tasa_exito, 2),
                "total_errores": len(self.errores),
                "total_datos_creados": sum(len(v) for v in self.datos_creados.values())
            },
            "secciones": self.secciones,
            "datos_creados": self.datos_creados,
            "errores": self.errores,
            "resumen": {
                "estado": "EXITOSO" if secciones_fallidas == 0 else "CON_ERRORES",
                "mensaje": self._generar_mensaje_resumen(secciones_exitosas, secciones_fallidas)
            }
        }
        
        # Guardar archivo
        if ruta_salida is None:
            ruta_salida = f"salida_flujo{self.flujo_numero:02d}.json"
        
        with open(ruta_salida, 'w', encoding='utf-8') as f:
            json.dump(resultado, f, indent=2, ensure_ascii=False)
            
        return ruta_salida
        
    def _generar_mensaje_resumen(self, exitosas: int, fallidas: int) -> str:
        """Genera un mensaje de resumen legible"""
        if fallidas == 0:
            return f"Todas las {exitosas} secciones ejecutadas exitosamente"
        else:
            return f"{exitosas} secciones exitosas, {fallidas} con errores"


# Funcion de conveniencia
def crear_reporte_json(flujo_numero: int, flujo_nombre: str) -> JSONOutputHelper:
    """Crea un nuevo helper para generar reporte JSON"""
    return JSONOutputHelper(flujo_nombre, flujo_numero)
