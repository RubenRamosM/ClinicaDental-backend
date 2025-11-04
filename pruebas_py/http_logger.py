"""
Helper module para imprimir transacciones HTTP de manera descriptiva
Similar al formato de DevTools Network tab del navegador
"""
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich import box
import json
import sys
from typing import Any, Dict, Optional

# Detectar Windows y usar configuración compatible
IS_WINDOWS = sys.platform == 'win32'
if IS_WINDOWS:
    console = Console(legacy_windows=False, force_terminal=True, width=80, no_color=False)
else:
    console = Console()


def analizar_tipo(data: Any) -> str:
    """Analiza y retorna el tipo de dato en formato descriptivo"""
    if isinstance(data, dict):
        return f"object ({len(data)} propiedades)"
    elif isinstance(data, list):
        return f"array ({len(data)} elementos)"
    elif isinstance(data, str):
        return f"string (longitud: {len(data)})"
    elif isinstance(data, int):
        return "integer"
    elif isinstance(data, float):
        return "float"
    elif isinstance(data, bool):
        return "boolean"
    elif data is None:
        return "null"
    else:
        return type(data).__name__


def analizar_estructura(data: Any, nivel: int = 0, max_nivel: int = 5) -> str:
    """
    Analiza recursivamente la estructura de datos y retorna un string formateado
    mostrando tipos de datos de cada campo. MUESTRA TODOS LOS ELEMENTOS.
    """
    indent = "  " * nivel
    resultado = []
    
    if nivel > max_nivel:
        return f"{indent}..."
    
    if isinstance(data, dict):
        for key, value in data.items():
            tipo = analizar_tipo(value)
            
            if isinstance(value, dict):
                resultado.append(f"{indent}[OBJ] {key}: {tipo}")
                resultado.append(analizar_estructura(value, nivel + 1, max_nivel))
            elif isinstance(value, list):
                resultado.append(f"{indent}[ARR] {key}: {tipo}")
                if len(value) > 0 and nivel < max_nivel:
                    # MOSTRAR TODOS LOS ELEMENTOS
                    for idx, item in enumerate(value):
                        resultado.append(f"{indent}  +- Elemento {idx + 1}:")
                        resultado.append(analizar_estructura(item, nivel + 2, max_nivel))
            elif isinstance(value, str):
                preview = value[:50] + "..." if len(value) > 50 else value
                resultado.append(f"{indent}[STR] {key}: {tipo} = \"{preview}\"")
            elif isinstance(value, (int, float)):
                resultado.append(f"{indent}[NUM] {key}: {tipo} = {value}")
            elif isinstance(value, bool):
                resultado.append(f"{indent}[BOOL] {key}: {tipo} = {value}")
            elif value is None:
                resultado.append(f"{indent}[NULL] {key}: null")
            else:
                resultado.append(f"{indent}- {key}: {tipo}")
                
    elif isinstance(data, list):
        if len(data) > 0:
            # MOSTRAR TODOS LOS ELEMENTOS DEL ARRAY
            for idx, item in enumerate(data):
                resultado.append(f"{indent}[Elemento {idx + 1} de {len(data)}]")
                resultado.append(analizar_estructura(item, nivel, max_nivel))
    else:
        tipo = analizar_tipo(data)
        resultado.append(f"{indent}{tipo}: {data}")
    
    return "\n".join(resultado)


def formatear_json(data: Any) -> str:
    """Formatea datos a JSON indentado para mejor lectura"""
    if isinstance(data, (dict, list)):
        return json.dumps(data, indent=2, ensure_ascii=False)
    return str(data)


def print_http_transaction(
    metodo: str,
    url: str,
    headers: Optional[Dict[str, str]] = None,
    body: Any = None,
    response_status: Optional[int] = None,
    response_headers: Optional[Dict[str, str]] = None,
    response_body: Any = None,
    descripcion: str = ""
):
    """
    Imprime una transacción HTTP completa en formato detallado
    
    Args:
        metodo: Método HTTP (GET, POST, PUT, DELETE, etc.)
        url: URL completa del endpoint
        headers: Diccionario de headers de la petición
        body: Cuerpo de la petición (dict, list, str, etc.)
        response_status: Código de estado HTTP de la respuesta
        response_headers: Diccionario de headers de la respuesta
        response_body: Cuerpo de la respuesta
        descripcion: Descripción opcional de la operación
    """
    
    # Título de la transacción
    if descripcion:
        console.print(f"\n[bold cyan]═══ {descripcion} ═══[/bold cyan]")
    
    # ========================
    # SECCIÓN: REQUEST
    # ========================
    console.print("\n[bold yellow][REQ] REQUEST[/bold yellow]")
    
    # Método y URL
    console.print(f"[bold]{metodo}[/bold] {url}")
    
    # Headers de petición
    if headers:
        console.print("\n[dim]Headers:[/dim]")
        headers_table = Table(show_header=False, box=box.SIMPLE, padding=(0, 1))
        headers_table.add_column("Key", style="cyan")
        headers_table.add_column("Value", style="white")
        for key, value in headers.items():
            # Ocultar tokens largos parcialmente
            if key.lower() == "authorization" and len(str(value)) > 20:
                display_value = f"{str(value)[:15]}...{str(value)[-5:]}"
            else:
                display_value = str(value)
            headers_table.add_row(key, display_value)
        console.print(headers_table)
    
    # Body de petición
    if body is not None:
        tipo_body = analizar_tipo(body)
        console.print(f"\n[dim]Body Type:[/dim] [green]{tipo_body}[/green]")
        
        # Mostrar estructura de tipos
        if isinstance(body, (dict, list)):
            console.print("\n[dim]Estructura de datos:[/dim]")
            estructura = analizar_estructura(body)
            console.print(estructura)
        
        # Formatear body como JSON si es dict o list
        if isinstance(body, (dict, list)):
            console.print(f"\n[dim]JSON:[/dim]")
            body_str = formatear_json(body)
            # Imprimir JSON completo sin Panel
            console.print(body_str)
    
    # ========================
    # SECCIÓN: RESPONSE
    # ========================
    if response_status is not None:
        console.print("\n[bold green][RESP] RESPONSE[/bold green]")
        
        # Status Code con colores
        if 200 <= response_status < 300:
            status_color = "green"
            status_emoji = "✅"
        elif 400 <= response_status < 500:
            status_color = "red"
            status_emoji = "❌"
        elif 500 <= response_status:
            status_color = "bright_red"
            status_emoji = "💥"
        else:
            status_color = "yellow"
            status_emoji = "⚠️"
        
        console.print(f"[{status_color}]{status_emoji} Status: {response_status}[/{status_color}]")
        
        # Headers de respuesta
        if response_headers:
            console.print("\n[dim]Headers:[/dim]")
            response_headers_table = Table(show_header=False, box=box.SIMPLE, padding=(0, 1))
            response_headers_table.add_column("Key", style="cyan")
            response_headers_table.add_column("Value", style="white")
            for key, value in response_headers.items():
                response_headers_table.add_row(key, str(value))
            console.print(response_headers_table)
        
        # Body de respuesta
        if response_body is not None:
            tipo_response = analizar_tipo(response_body)
            console.print(f"\n[dim]Body Type:[/dim] [green]{tipo_response}[/green]")
            
            # Mostrar estructura de tipos
            if isinstance(response_body, (dict, list)):
                console.print("\n[dim]Estructura de datos:[/dim]")
                estructura = analizar_estructura(response_body)
                console.print(estructura)
            
            # Formatear response como JSON si es dict o list
            if isinstance(response_body, (dict, list)):
                console.print(f"\n[dim]JSON:[/dim]")
                response_str = formatear_json(response_body)
                # Imprimir JSON completo sin Panel
                console.print(response_str)
    
    # Separador entre transacciones
    console.print("\n" + "-" * 80 + "\n")


def print_seccion(titulo: str):
    """Imprime un título de sección destacado"""
    if IS_WINDOWS:
        console.print(f"\n[bold magenta]{'=' * 80}[/bold magenta]")
        console.print(f"[bold magenta]{titulo.center(80)}[/bold magenta]")
        console.print(f"[bold magenta]{'=' * 80}[/bold magenta]\n")
    else:
        console.print(f"\n[bold magenta]{'═' * 80}[/bold magenta]")
        console.print(f"[bold magenta]{titulo.center(80)}[/bold magenta]")
        console.print(f"[bold magenta]{'═' * 80}[/bold magenta]\n")


def print_exito(mensaje: str):
    """Imprime un mensaje de éxito"""
    if IS_WINDOWS:
        console.print(f"[bold green]OK {mensaje}[/bold green]")
    else:
        console.print(f"[bold green]✅ {mensaje}[/bold green]")


def print_error(mensaje: str):
    """Imprime un mensaje de error"""
    if IS_WINDOWS:
        console.print(f"[bold red]ERROR {mensaje}[/bold red]")
    else:
        console.print(f"[bold red]❌ {mensaje}[/bold red]")


def print_warning(mensaje: str):
    """Imprime un mensaje de advertencia"""
    if IS_WINDOWS:
        console.print(f"[bold yellow]ADVERTENCIA {mensaje}[/bold yellow]")


def print_info(mensaje: str):
    """Imprime un mensaje informativo"""
    console.print(f"[bold cyan][INFO]  {mensaje}[/bold cyan]")
