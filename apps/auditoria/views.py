"""
Views para auditoría (bitácora).
"""
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Count

from .models import Bitacora
from .serializers import BitacoraSerializer
from apps.comun.permisos import EsAdministrador


class BitacoraViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para bitácora de auditoría.
    Solo administradores pueden ver los registros.
    
    Endpoints:
    - GET /api/v1/auditoria/bitacora/
    - GET /api/v1/auditoria/bitacora/{id}/
    - GET /api/v1/auditoria/bitacora/por_usuario/?usuario_id=1
    - GET /api/v1/auditoria/bitacora/por_tabla/?tabla=consulta
    - GET /api/v1/auditoria/bitacora/resumen/
    """
    queryset = Bitacora.objects.all()
    serializer_class = BitacoraSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['usuario', 'accion', 'tabla_afectada']
    search_fields = ['tabla_afectada', 'detalles', 'ip_address']
    ordering_fields = ['fecha']
    ordering = ['-fecha']
    
    @action(detail=False, methods=['get'])
    def por_usuario(self, request):
        """Filtrar registros por usuario."""
        usuario_id = request.query_params.get('usuario_id')
        
        if not usuario_id:
            return Response(
                {'error': 'Debe proporcionar usuario_id'},
                status=400
            )
        
        registros = self.queryset.filter(usuario_id=usuario_id)
        serializer = self.get_serializer(registros, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def por_tabla(self, request):
        """Filtrar registros por tabla afectada."""
        tabla = request.query_params.get('tabla')
        
        if not tabla:
            return Response(
                {'error': 'Debe proporcionar el parámetro tabla'},
                status=400
            )
        
        registros = self.queryset.filter(tabla_afectada__icontains=tabla)
        serializer = self.get_serializer(registros, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def resumen(self, request):
        """Resumen de actividad en la bitácora."""
        from django.utils import timezone
        from datetime import timedelta
        
        hoy = timezone.now().date()
        hace_7_dias = hoy - timedelta(days=7)
        hace_30_dias = hoy - timedelta(days=30)
        
        # Actividad por acción
        por_accion = self.queryset.values('accion').annotate(
            total=Count('id')
        ).order_by('-total')
        
        # Actividad por tabla
        por_tabla = self.queryset.values('tabla_afectada').annotate(
            total=Count('id')
        ).order_by('-total')[:10]
        
        # Actividad reciente
        ultimos_7_dias = self.queryset.filter(
            fecha__gte=hace_7_dias
        ).count()
        
        ultimos_30_dias = self.queryset.filter(
            fecha__gte=hace_30_dias
        ).count()
        
        return Response({
            'por_accion': list(por_accion),
            'por_tabla': list(por_tabla),
            'ultimos_7_dias': ultimos_7_dias,
            'ultimos_30_dias': ultimos_30_dias,
            'total_registros': self.queryset.count()
        })
    
    @action(detail=False, methods=['get'])
    def logs(self, request):
        """Alias para listar todos los logs (igual que list)."""
        return self.list(request)
    
    @action(detail=False, methods=['get'], url_path='actividad-reciente')
    def actividad_reciente(self, request):
        """Obtener actividad reciente (últimos 50 registros)."""
        limit = int(request.query_params.get('limit', 50))
        registros = self.queryset.order_by('-fecha')[:limit]
        serializer = self.get_serializer(registros, many=True)
        return Response(serializer.data)

