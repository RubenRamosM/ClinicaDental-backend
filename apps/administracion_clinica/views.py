"""
Views para administración clínica (servicios y combos).
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone

from .models import Servicio, ComboServicio
from .serializers import (
    ServicioSerializer,
    ServicioListaSerializer,
    ComboServicioSerializer,
    ComboServicioCrearSerializer,
    ComboServicioActualizarSerializer
)
from apps.comun.permisos import EsStaff, EsAdministrador
from apps.comun.pagination import ClienteControlablePagination


class ServicioViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de servicios.
    
    Endpoints:
    - GET /api/v1/servicios/
    - POST /api/v1/servicios/
    - GET /api/v1/servicios/{id}/
    - PUT /api/v1/servicios/{id}/
    - PATCH /api/v1/servicios/{id}/
    - DELETE /api/v1/servicios/{id}/
    - GET /api/v1/servicios/activos/
    - GET /api/v1/servicios/por_categoria/?categoria=tratamiento
    
    Filtros disponibles:
    - activo=true/false
    - search=texto (busca en nombre y descripción)
    - ordering=nombre,-nombre,costobase,-costobase,duracion,-duracion
    - costobase_min=50.00 (precio mínimo)
    - costobase_max=500.00 (precio máximo)
    - duracion_min=30 (duración mínima en minutos)
    - duracion_max=90 (duración máxima en minutos)
    
    Paginación:
    - page=1 (número de página)
    - page_size=10 (tamaño de página, max: 100)
    """
    queryset = Servicio.objects.all()
    serializer_class = ServicioSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = ClienteControlablePagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['activo']
    search_fields = ['nombre', 'descripcion']
    ordering_fields = ['nombre', 'costobase', 'duracion', 'fecha_creacion']
    ordering = ['nombre']
    
    def get_queryset(self):
        """Aplicar filtros de rango para precio y duración."""
        queryset = super().get_queryset()
        
        # Filtro de precio mínimo
        precio_min = self.request.query_params.get('costobase_min')
        if precio_min:
            try:
                queryset = queryset.filter(costobase__gte=float(precio_min))
            except (ValueError, TypeError):
                pass
        
        # Filtro de precio máximo
        precio_max = self.request.query_params.get('costobase_max')
        if precio_max:
            try:
                queryset = queryset.filter(costobase__lte=float(precio_max))
            except (ValueError, TypeError):
                pass
        
        # Filtro de duración mínima
        duracion_min = self.request.query_params.get('duracion_min')
        if duracion_min:
            try:
                queryset = queryset.filter(duracion__gte=int(duracion_min))
            except (ValueError, TypeError):
                pass
        
        # Filtro de duración máxima
        duracion_max = self.request.query_params.get('duracion_max')
        if duracion_max:
            try:
                queryset = queryset.filter(duracion__lte=int(duracion_max))
            except (ValueError, TypeError):
                pass
        
        return queryset
    
    def get_permissions(self):
        """Solo staff puede crear/editar/eliminar."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [EsStaff()]
        return super().get_permissions()
    
    def get_serializer_class(self):
        """Usar serializer simplificado para listas."""
        if self.action == 'list':
            return ServicioListaSerializer
        return ServicioSerializer
    
    @action(detail=False, methods=['get'])
    def activos(self, request):
        """Listar solo servicios activos."""
        servicios = self.queryset.filter(activo=True)
        serializer = ServicioListaSerializer(servicios, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def por_categoria(self, request):
        """Filtrar servicios por categoría."""
        categoria = request.query_params.get('categoria')
        
        if not categoria:
            return Response(
                {'error': 'Debe proporcionar el parámetro categoria'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        servicios = self.queryset.filter(
            categoria=categoria,
            activo=True
        )
        serializer = ServicioListaSerializer(servicios, many=True)
        return Response(serializer.data)


class ComboServicioViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de combos de servicios.
    
    Endpoints:
    - GET /api/v1/combos/
    - POST /api/v1/combos/
    - GET /api/v1/combos/{id}/
    - PUT /api/v1/combos/{id}/
    - PATCH /api/v1/combos/{id}/
    - DELETE /api/v1/combos/{id}/
    - GET /api/v1/combos/vigentes/
    - GET /api/v1/combos/{id}/calcular_precio/
    
    Paginación:
    - page=1 (número de página)
    - page_size=10 (tamaño de página, max: 100)
    """
    queryset = ComboServicio.objects.all()
    serializer_class = ComboServicioSerializer
    permission_classes = [IsAuthenticated, EsStaff]
    pagination_class = ClienteControlablePagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['activo']
    search_fields = ['nombre', 'descripcion']
    ordering_fields = ['nombre', 'fecha_creacion']
    ordering = ['-fecha_creacion']
    
    def get_serializer_class(self):
        """Seleccionar serializer según acción."""
        if self.action == 'create':
            return ComboServicioCrearSerializer
        elif self.action in ['update', 'partial_update']:
            return ComboServicioActualizarSerializer
        return ComboServicioSerializer
    
    @action(detail=False, methods=['get'])
    def vigentes(self, request):
        """Listar combos vigentes y activos."""
        hoy = timezone.now().date()
        
        combos = self.queryset.filter(
            activo=True
        ).filter(
            # Sin fecha de inicio o ya comenzó
            fecha_inicio__lte=hoy
        ).filter(
            # Sin fecha de fin o aún no terminó
            fecha_fin__gte=hoy
        ) | self.queryset.filter(
            activo=True,
            fecha_inicio__isnull=True,
            fecha_fin__isnull=True
        )
        
        serializer = self.get_serializer(combos, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def calcular_precio(self, request, pk=None):
        """Calcular precio total del combo."""
        combo = self.get_object()
        
        return Response({
            'combo_id': combo.id,
            'nombre': combo.nombre,
            'precio_total_sin_descuento': combo.calcular_precio_total_servicios(),
            'descuento_porcentaje': combo.descuento_porcentaje,
            'precio_final': combo.calcular_precio_final(),
            'duracion_total_minutos': combo.calcular_duracion_total(),
            'servicios_incluidos': combo.detalles.count()
        })


# ====================================================================
# ENDPOINTS ADICIONALES
# ====================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def consultorios_list(request):
    """
    Listar consultorios disponibles.
    Nota: Modelo Consultorio no existe, retornando placeholder.
    """
    return Response({
        'message': 'Módulo de consultorios en desarrollo',
        'consultorios': []
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def configuracion_general(request):
    """
    Obtener configuración general de la clínica.
    """
    from django.conf import settings
    
    config = {
        'nombre_clinica': 'Clínica Dental',
        'timezone': str(settings.TIME_ZONE),
        'servicios_activos': Servicio.objects.filter(activo=True).count(),
        'horario_atencion': {
            'inicio': '08:00',
            'fin': '18:00',
            'dias': ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado']
        }
    }
    
    return Response(config)


# Catálogo de piezas dentales según nomenclatura FDI (dígitos dobles)
PIEZAS_DENTALES_UNIVERSAL = [
    # Cuadrante 1 (Superior derecho) - Dientes 11-18
    {"codigo": 8, "numero": "11", "nombre": "Incisivo central superior derecho"},
    {"codigo": 7, "numero": "12", "nombre": "Incisivo lateral superior derecho"},
    {"codigo": 6, "numero": "13", "nombre": "Canino superior derecho"},
    {"codigo": 5, "numero": "14", "nombre": "Primer premolar superior derecho"},
    {"codigo": 4, "numero": "15", "nombre": "Segundo premolar superior derecho"},
    {"codigo": 3, "numero": "16", "nombre": "Primer molar superior derecho"},
    {"codigo": 2, "numero": "17", "nombre": "Segundo molar superior derecho"},
    {"codigo": 1, "numero": "18", "nombre": "Tercer molar superior derecho"},
    
    # Cuadrante 2 (Superior izquierdo) - Dientes 21-28
    {"codigo": 9, "numero": "21", "nombre": "Incisivo central superior izquierdo"},
    {"codigo": 10, "numero": "22", "nombre": "Incisivo lateral superior izquierdo"},
    {"codigo": 11, "numero": "23", "nombre": "Canino superior izquierdo"},
    {"codigo": 12, "numero": "24", "nombre": "Primer premolar superior izquierdo"},
    {"codigo": 13, "numero": "25", "nombre": "Segundo premolar superior izquierdo"},
    {"codigo": 14, "numero": "26", "nombre": "Primer molar superior izquierdo"},
    {"codigo": 15, "numero": "27", "nombre": "Segundo molar superior izquierdo"},
    {"codigo": 16, "numero": "28", "nombre": "Tercer molar superior izquierdo"},
    
    # Cuadrante 3 (Inferior izquierdo) - Dientes 31-38
    {"codigo": 24, "numero": "31", "nombre": "Incisivo central inferior izquierdo"},
    {"codigo": 23, "numero": "32", "nombre": "Incisivo lateral inferior izquierdo"},
    {"codigo": 22, "numero": "33", "nombre": "Canino inferior izquierdo"},
    {"codigo": 21, "numero": "34", "nombre": "Primer premolar inferior izquierdo"},
    {"codigo": 20, "numero": "35", "nombre": "Segundo premolar inferior izquierdo"},
    {"codigo": 19, "numero": "36", "nombre": "Primer molar inferior izquierdo"},
    {"codigo": 18, "numero": "37", "nombre": "Segundo molar inferior izquierdo"},
    {"codigo": 17, "numero": "38", "nombre": "Tercer molar inferior izquierdo"},
    
    # Cuadrante 4 (Inferior derecho) - Dientes 41-48
    {"codigo": 25, "numero": "41", "nombre": "Incisivo central inferior derecho"},
    {"codigo": 26, "numero": "42", "nombre": "Incisivo lateral inferior derecho"},
    {"codigo": 27, "numero": "43", "nombre": "Canino inferior derecho"},
    {"codigo": 28, "numero": "44", "nombre": "Primer premolar inferior derecho"},
    {"codigo": 29, "numero": "45", "nombre": "Segundo premolar inferior derecho"},
    {"codigo": 30, "numero": "46", "nombre": "Primer molar inferior derecho"},
    {"codigo": 31, "numero": "47", "nombre": "Segundo molar inferior derecho"},
    {"codigo": 32, "numero": "48", "nombre": "Tercer molar inferior derecho"}
]

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def piezas_dentales_list(request):
    """
    Listar piezas dentales según nomenclatura FDI (dígitos dobles).
    Sistema internacional de numeración dental.
    
    Endpoint: GET /api/v1/administracion/piezas-dentales/
    
    Query Params:
    - page_size: Número de resultados (default: 100)
    
    Response:
    {
      "count": 32,
      "results": [
        {
          "codigo": 1,
          "numero": "18",
          "nombre": "Tercer molar superior derecho"
        },
        ...
      ]
    }
    """
    page_size = request.query_params.get('page_size', 100)
    
    return Response({
        'count': len(PIEZAS_DENTALES_UNIVERSAL),
        'results': PIEZAS_DENTALES_UNIVERSAL[:int(page_size)]
    })
