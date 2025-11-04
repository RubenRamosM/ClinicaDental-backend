"""
Clases de paginación personalizadas para la API.
"""
from rest_framework.pagination import PageNumberPagination


class ClienteControlablePagination(PageNumberPagination):
    """
    Paginación que permite al cliente controlar el tamaño de página.
    
    Parámetros:
    - page: Número de página (default: 1)
    - page_size: Tamaño de página (default: 25, max: 100)
    
    Ejemplo:
    - /api/v1/servicios/?page=1&page_size=10
    - /api/v1/pacientes/?page=2&page_size=50
    """
    page_size = 25  # Tamaño por defecto
    page_size_query_param = 'page_size'  # Permite al cliente especificar page_size
    max_page_size = 100  # Límite máximo para evitar consultas muy grandes
    page_query_param = 'page'  # Parámetro para el número de página
