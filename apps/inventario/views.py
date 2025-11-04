"""
Views para gestión de inventario.
CU27: Gestión de Inventario
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from datetime import timedelta

from apps.historial_clinico.models_inventario import CategoriaInsumo, Proveedor, Insumo, MovimientoInventario, AlertaInventario
from .serializers import (
    CategoriaInsumoSerializer, ProveedorSerializer,
    InsumoListSerializer, InsumoDetailSerializer, InsumoCreateUpdateSerializer,
    MovimientoInventarioListSerializer, MovimientoInventarioCreateSerializer,
    AlertaInventarioSerializer, ReporteInventarioSerializer
)


class CategoriaInsumoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para categorías de insumos.
    
    list: Listar todas las categorías
    create: Crear nueva categoría
    retrieve: Obtener detalle de categoría
    update: Actualizar categoría
    partial_update: Actualizar parcialmente
    destroy: Eliminar categoría (soft delete)
    """
    queryset = CategoriaInsumo.objects.all()
    serializer_class = CategoriaInsumoSerializer
    permission_classes = [IsAuthenticated]  # TODO: Cambiar a IsAuthenticated cuando login genere tokens
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['nombre', 'descripcion']
    ordering_fields = ['nombre', 'fecha_creacion']
    ordering = ['nombre']


class ProveedorViewSet(viewsets.ModelViewSet):
    """
    ViewSet para proveedores.
    
    list: Listar todos los proveedores
    create: Crear nuevo proveedor
    retrieve: Obtener detalle de proveedor
    update: Actualizar proveedor
    partial_update: Actualizar parcialmente
    destroy: Eliminar proveedor (soft delete)
    """
    queryset = Proveedor.objects.all()
    serializer_class = ProveedorSerializer
    permission_classes = [IsAuthenticated]  # TODO: Cambiar a IsAuthenticated
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['activo']
    search_fields = ['nombre', 'ruc', 'email', 'contacto_nombre']
    ordering_fields = ['nombre', 'fecha_registro']
    ordering = ['nombre']


class InsumoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para insumos del inventario.
    
    list: Listar todos los insumos
    create: Crear nuevo insumo
    retrieve: Obtener detalle completo de insumo
    update: Actualizar insumo
    partial_update: Actualizar parcialmente
    destroy: Eliminar insumo (soft delete)
    
    Acciones adicionales:
    - stock_bajo: Insumos con stock por debajo del mínimo
    - proximos_vencer: Insumos próximos a vencer
    - historial_movimientos: Historial de movimientos de un insumo
    """
    queryset = Insumo.objects.select_related(
        'categoria', 'proveedor_principal'
    ).all()
    permission_classes = [IsAuthenticated]  # TODO: Cambiar a IsAuthenticated
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['categoria', 'proveedor_principal', 'activo']
    search_fields = ['codigo', 'nombre', 'descripcion']
    ordering_fields = ['nombre', 'stock_actual', 'precio_compra', 'fecha_creacion']
    ordering = ['nombre']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return InsumoListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return InsumoCreateUpdateSerializer
        return InsumoDetailSerializer
    
    @action(detail=False, methods=['get'])
    def stock_bajo(self, request):
        """
        Lista insumos con stock por debajo del mínimo.
        
        GET /api/v1/inventario/insumos/stock_bajo/
        """
        insumos_bajo = self.queryset.filter(
            stock_actual__lte=F('stock_minimo'),
            activo=True
        ).order_by('stock_actual')
        
        serializer = InsumoListSerializer(insumos_bajo, many=True)
        return Response({
            'total': insumos_bajo.count(),
            'insumos': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def proximos_vencer(self, request):
        """
        Lista insumos próximos a vencer (30 días).
        
        GET /api/v1/inventario/insumos/proximos_vencer/
        """
        dias = int(request.query_params.get('dias', 30))
        fecha_limite = timezone.now().date() + timedelta(days=dias)
        
        insumos_vencer = self.queryset.filter(
            requiere_vencimiento=True,
            fecha_vencimiento__lte=fecha_limite,
            fecha_vencimiento__gte=timezone.now().date(),
            activo=True
        ).order_by('fecha_vencimiento')
        
        serializer = InsumoListSerializer(insumos_vencer, many=True)
        return Response({
            'total': insumos_vencer.count(),
            'insumos': serializer.data
        })
    
    @action(detail=True, methods=['get'])
    def historial_movimientos(self, request, pk=None):
        """
        Historial completo de movimientos de un insumo.
        
        GET /api/v1/inventario/insumos/{id}/historial_movimientos/
        """
        insumo = self.get_object()
        movimientos = insumo.movimientos.all()
        
        serializer = MovimientoInventarioListSerializer(movimientos, many=True)
        return Response({
            'insumo': InsumoDetailSerializer(insumo).data,
            'movimientos': serializer.data
        })


class MovimientoInventarioViewSet(viewsets.ModelViewSet):
    """
    ViewSet para movimientos de inventario.
    
    list: Listar todos los movimientos
    create: Registrar nuevo movimiento (actualiza stock automáticamente)
    retrieve: Obtener detalle de movimiento
    
    No se permite update/delete para mantener integridad del historial.
    """
    queryset = MovimientoInventario.objects.select_related(
        'insumo', 'proveedor', 'realizado_por'
    ).all()
    permission_classes = [IsAuthenticated]  # TODO: Cambiar a IsAuthenticated
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['insumo', 'tipo_movimiento', 'proveedor']
    search_fields = ['insumo__nombre', 'insumo__codigo', 'motivo', 'numero_factura']
    ordering_fields = ['fecha_movimiento', 'costo_total']
    ordering = ['-fecha_movimiento']
    http_method_names = ['get', 'post', 'head', 'options']  # No permitir update/delete
    
    def get_serializer_class(self):
        if self.action == 'create':
            return MovimientoInventarioCreateSerializer
        return MovimientoInventarioListSerializer
    
    @action(detail=False, methods=['get'])
    def resumen_periodo(self, request):
        """
        Resumen de movimientos en un periodo.
        
        GET /api/v1/inventario/movimientos/resumen_periodo/?fecha_inicio=YYYY-MM-DD&fecha_fin=YYYY-MM-DD
        """
        from datetime import datetime
        
        fecha_inicio = request.query_params.get('fecha_inicio')
        fecha_fin = request.query_params.get('fecha_fin')
        
        if not fecha_inicio or not fecha_fin:
            hoy = timezone.now().date()
            fecha_fin = hoy
            fecha_inicio = hoy.replace(day=1)
        else:
            fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
            fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
        
        movimientos = self.queryset.filter(
            fecha_movimiento__date__range=[fecha_inicio, fecha_fin]
        )
        
        resumen = {
            'periodo': {
                'inicio': fecha_inicio.isoformat(),
                'fin': fecha_fin.isoformat()
            },
            'total_movimientos': movimientos.count(),
            'por_tipo': list(
                movimientos.values('tipo_movimiento')
                .annotate(cantidad=Count('id'), costo_total=Sum('costo_total'))
                .order_by('tipo_movimiento')
            ),
            'costo_total_entradas': float(
                movimientos.filter(tipo_movimiento='entrada')
                .aggregate(total=Sum('costo_total'))['total'] or 0
            ),
            'top_movimientos': MovimientoInventarioListSerializer(
                movimientos.order_by('-costo_total')[:10],
                many=True
            ).data
        }
        
        return Response(resumen)


class AlertaInventarioViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para alertas de inventario (solo lectura).
    
    list: Listar todas las alertas
    retrieve: Obtener detalle de alerta
    
    Acciones adicionales:
    - pendientes: Alertas no resueltas
    - resolver: Marcar alerta como resuelta
    - generar: Generar alertas automáticas
    """
    queryset = AlertaInventario.objects.select_related('insumo').all()
    serializer_class = AlertaInventarioSerializer
    permission_classes = [IsAuthenticated]  # TODO: Cambiar a IsAuthenticated
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['tipo_alerta', 'prioridad', 'resuelta']
    ordering_fields = ['fecha_creacion', 'prioridad']
    ordering = ['-fecha_creacion']
    
    @action(detail=False, methods=['get'])
    def pendientes(self, request):
        """
        Lista solo alertas pendientes.
        
        GET /api/v1/inventario/alertas/pendientes/
        """
        alertas = self.queryset.filter(resuelta=False)
        
        por_prioridad = {
            'critica': alertas.filter(prioridad='critica').count(),
            'alta': alertas.filter(prioridad='alta').count(),
            'media': alertas.filter(prioridad='media').count(),
            'baja': alertas.filter(prioridad='baja').count(),
        }
        
        serializer = self.get_serializer(alertas, many=True)
        return Response({
            'total': alertas.count(),
            'por_prioridad': por_prioridad,
            'alertas': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def resolver(self, request, pk=None):
        """
        Marca una alerta como resuelta.
        
        POST /api/v1/inventario/alertas/{id}/resolver/
        """
        alerta = self.get_object()
        alerta.resuelta = True
        alerta.fecha_resolucion = timezone.now()
        alerta.save()
        
        serializer = self.get_serializer(alerta)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def generar(self, request):
        """
        Genera alertas automáticas basadas en el estado actual del inventario.
        
        POST /api/v1/inventario/alertas/generar/
        """
        alertas_creadas = 0
        
        # Alertas de stock bajo
        insumos_stock_bajo = Insumo.objects.filter(
            stock_actual__lte=F('stock_minimo'),
            stock_actual__gt=0,
            activo=True
        )
        
        for insumo in insumos_stock_bajo:
            # Verificar que no exista alerta pendiente
            if not AlertaInventario.objects.filter(
                insumo=insumo,
                tipo_alerta='stock_bajo',
                resuelta=False
            ).exists():
                AlertaInventario.objects.create(
                    insumo=insumo,
                    tipo_alerta='stock_bajo',
                    mensaje=f"Stock bajo: {insumo.stock_actual} {insumo.unidad_medida}. Mínimo: {insumo.stock_minimo}",
                    prioridad='alta'
                )
                alertas_creadas += 1
        
        # Alertas de stock agotado
        insumos_agotados = Insumo.objects.filter(
            stock_actual=0,
            activo=True
        )
        
        for insumo in insumos_agotados:
            if not AlertaInventario.objects.filter(
                insumo=insumo,
                tipo_alerta='stock_agotado',
                resuelta=False
            ).exists():
                AlertaInventario.objects.create(
                    insumo=insumo,
                    tipo_alerta='stock_agotado',
                    mensaje=f"Stock agotado de {insumo.nombre}",
                    prioridad='critica'
                )
                alertas_creadas += 1
        
        # Alertas de próximos a vencer
        fecha_limite = timezone.now().date() + timedelta(days=30)
        insumos_vencer = Insumo.objects.filter(
            requiere_vencimiento=True,
            fecha_vencimiento__lte=fecha_limite,
            fecha_vencimiento__gte=timezone.now().date(),
            activo=True
        )
        
        for insumo in insumos_vencer:
            if not AlertaInventario.objects.filter(
                insumo=insumo,
                tipo_alerta='proximo_vencer',
                resuelta=False
            ).exists():
                dias_restantes = (insumo.fecha_vencimiento - timezone.now().date()).days
                AlertaInventario.objects.create(
                    insumo=insumo,
                    tipo_alerta='proximo_vencer',
                    mensaje=f"Vence en {dias_restantes} días (fecha: {insumo.fecha_vencimiento})",
                    prioridad='media'
                )
                alertas_creadas += 1
        
        return Response({
            'mensaje': f'Se generaron {alertas_creadas} nuevas alertas',
            'alertas_creadas': alertas_creadas
        }, status=status.HTTP_201_CREATED)


@action(detail=False, methods=['get'])
def reporte_general(request):
    """
    Reporte general del inventario.
    
    GET /api/v1/inventario/reporte/
    """
    insumos_activos = Insumo.objects.filter(activo=True)
    
    # Estadísticas generales
    reporte = {
        'total_insumos': Insumo.objects.count(),
        'insumos_activos': insumos_activos.count(),
        'insumos_stock_bajo': insumos_activos.filter(
            stock_actual__lte=F('stock_minimo')
        ).count(),
        'insumos_agotados': insumos_activos.filter(stock_actual=0).count(),
        'valor_total_inventario': float(
            sum(insumo.valor_inventario for insumo in insumos_activos)
        ),
        'categorias': list(
            CategoriaInsumo.objects.annotate(
                total=Count('insumos', filter=Q(insumos__activo=True))
            ).values('id', 'nombre', 'total')
        ),
        'alertas_pendientes': AlertaInventario.objects.filter(resuelta=False).count(),
    }
    
    serializer = ReporteInventarioSerializer(reporte)
    return Response(serializer.data)
