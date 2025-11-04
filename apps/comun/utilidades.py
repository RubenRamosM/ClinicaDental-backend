"""
Utilidades y funciones helper reutilizables.
"""
from django.utils.text import slugify
import random
import string


def generar_codigo_unico(prefijo='', longitud=8):
    """
    Genera un código único alfanumérico.
    
    Args:
        prefijo (str): Prefijo opcional para el código
        longitud (int): Longitud de la parte aleatoria
    
    Returns:
        str: Código único generado
    
    Ejemplo:
        >>> generar_codigo_unico('PAC', 6)
        'PAC-A3F7G9'
    """
    caracteres = string.ascii_uppercase + string.digits
    codigo_aleatorio = ''.join(random.choices(caracteres, k=longitud))
    
    if prefijo:
        return f"{prefijo}-{codigo_aleatorio}"
    return codigo_aleatorio


def formatear_telefono(telefono):
    """
    Formatea un número de teléfono de forma consistente.
    
    Args:
        telefono (str): Teléfono sin formatear
    
    Returns:
        str: Teléfono formateado
    """
    # Remover todo excepto dígitos
    digitos = ''.join(filter(str.isdigit, telefono))
    
    if len(digitos) == 8:
        # Formato: 7123-4567
        return f"{digitos[:4]}-{digitos[4:]}"
    elif len(digitos) == 11:
        # Formato celular: 591 7123-4567
        return f"{digitos[:3]} {digitos[3:7]}-{digitos[7:]}"
    
    return telefono


def calcular_edad(fecha_nacimiento):
    """
    Calcula la edad a partir de una fecha de nacimiento.
    
    Args:
        fecha_nacimiento (date): Fecha de nacimiento
    
    Returns:
        int: Edad en años
    """
    from datetime import date
    hoy = date.today()
    edad = hoy.year - fecha_nacimiento.year
    
    # Ajustar si aún no cumplió años este año
    if (hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day):
        edad -= 1
    
    return edad


def formato_moneda(monto, moneda='Bs.'):
    """
    Formatea un monto como moneda.
    
    Args:
        monto (Decimal/float): Monto a formatear
        moneda (str): Símbolo de moneda
    
    Returns:
        str: Monto formateado
    
    Ejemplo:
        >>> formato_moneda(1234.56)
        'Bs. 1,234.56'
    """
    return f"{moneda} {monto:,.2f}"


def generar_slug_unico(modelo, texto, campo_slug='slug'):
    """
    Genera un slug único para un modelo.
    
    Args:
        modelo: Clase del modelo Django
        texto (str): Texto base para el slug
        campo_slug (str): Nombre del campo slug en el modelo
    
    Returns:
        str: Slug único
    """
    slug_base = slugify(texto)
    slug_final = slug_base
    contador = 1
    
    filtro = {campo_slug: slug_final}
    while modelo.objects.filter(**filtro).exists():
        slug_final = f"{slug_base}-{contador}"
        filtro = {campo_slug: slug_final}
        contador += 1
    
    return slug_final


def dividir_lista_en_chunks(lista, tamano_chunk):
    """
    Divide una lista en chunks de tamaño específico.
    Útil para procesamiento por lotes.
    
    Args:
        lista (list): Lista a dividir
        tamano_chunk (int): Tamaño de cada chunk
    
    Yields:
        list: Chunks de la lista
    
    Ejemplo:
        >>> lista = [1, 2, 3, 4, 5, 6, 7]
        >>> list(dividir_lista_en_chunks(lista, 3))
        [[1, 2, 3], [4, 5, 6], [7]]
    """
    for i in range(0, len(lista), tamano_chunk):
        yield lista[i:i + tamano_chunk]


def limpiar_ruc(ruc):
    """
    Limpia y valida un RUC/NIT.
    
    Args:
        ruc (str): RUC/NIT sin limpiar
    
    Returns:
        str: RUC/NIT limpio o None si es inválido
    """
    if not ruc:
        return None
    
    # Remover todo excepto dígitos
    digitos = ''.join(filter(str.isdigit, ruc))
    
    if len(digitos) >= 7:
        return digitos
    
    return None


def obtener_iniciales(nombre_completo):
    """
    Obtiene las iniciales de un nombre.
    
    Args:
        nombre_completo (str): Nombre completo
    
    Returns:
        str: Iniciales en mayúsculas
    
    Ejemplo:
        >>> obtener_iniciales('Juan Pablo Pérez')
        'JPP'
    """
    palabras = nombre_completo.strip().split()
    iniciales = ''.join([palabra[0].upper() for palabra in palabras if palabra])
    return iniciales


def es_email_valido(email):
    """
    Valida formato de email de forma simple.
    
    Args:
        email (str): Email a validar
    
    Returns:
        bool: True si es válido
    """
    import re
    patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(patron, email))
