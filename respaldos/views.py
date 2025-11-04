"""
Vistas (API endpoints) para gestión de respaldos.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from .models import Respaldo
from .serializers import (
    RespaldoSerializer,
    RespaldoDetailSerializer,
    CrearRespaldoSerializer
)
from .services import BackupService


class RespaldoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para gestionar respaldos.
    
    Endpoints:
    - GET /api/v1/respaldos/ - Listar respaldos de la clínica
    - GET /api/v1/respaldos/{id}/ - Ver detalles de un respaldo
    - POST /api/v1/respaldos/crear_respaldo_manual/ - Crear respaldo manual
    - GET /api/v1/respaldos/{id}/descargar/ - Obtener URL de descarga
    - DELETE /api/v1/respaldos/{id}/ - Eliminar respaldo (soft delete)
    - GET /api/v1/respaldos/estadisticas/ - Obtener estadísticas
    """
    
    permission_classes = [IsAuthenticated]
    serializer_class = RespaldoSerializer
    
    def get_queryset(self):
        """
        Filtrar respaldos por clínica del usuario autenticado.
        Implementación de multitenancy.
        """
        user = self.request.user
        return Respaldo.objects.filter(
            clinica_id=user.clinica_id,
            fecha_eliminacion__isnull=True
        ).order_by('-fecha_respaldo')
    
    def get_serializer_class(self):
        """Usar serializador detallado para retrieve."""
        if self.action == 'retrieve':
            return RespaldoDetailSerializer
        elif self.action == 'crear_respaldo_manual':
            return CrearRespaldoSerializer
        return RespaldoSerializer
    
    @action(detail=False, methods=['post'])
    def crear_respaldo_manual(self, request):
        """
        Crear respaldo manual/por demanda desde la API.
        
        POST /api/v1/respaldos/crear_respaldo_manual/
        {
            "descripcion": "Respaldo antes de actualización importante"
        }
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            respaldo = serializer.save()
            
            # Retornar detalles del respaldo creado
            detail_serializer = RespaldoDetailSerializer(respaldo)
            
            return Response({
                'mensaje': 'Respaldo creado exitosamente',
                'respaldo': detail_serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'error': 'Error al crear respaldo',
                'detalle': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'])
    def descargar(self, request, pk=None):
        """
        Generar URL prefirmada para descargar el respaldo.
        
        GET /api/v1/respaldos/{id}/descargar/
        
        Retorna URL válida por 1 hora.
        """
        respaldo = self.get_object()
        
        # Verificar que el respaldo está disponible
        if not respaldo.is_disponible():
            return Response({
                'error': 'Respaldo no disponible para descarga',
                'estado': respaldo.estado
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            backup_service = BackupService()
            url = backup_service.s3_client.generate_presigned_url(
                respaldo.archivo_s3,
                expiration=3600  # 1 hora
            )
            
            return Response({
                'url': url,
                'expira_en_segundos': 3600,
                'archivo': respaldo.archivo_s3,
                'tamaño_mb': round(respaldo.tamaño_bytes / (1024 * 1024), 2)
            })
            
        except Exception as e:
            return Response({
                'error': 'Error al generar URL de descarga',
                'detalle': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """
        Obtener estadísticas de respaldos de la clínica.
        
        GET /api/v1/respaldos/estadisticas/
        """
        user = request.user
        
        try:
            backup_service = BackupService()
            stats = backup_service.obtener_estadisticas(user.clinica_id)
            
            return Response(stats)
            
        except Exception as e:
            return Response({
                'error': 'Error al obtener estadísticas',
                'detalle': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def destroy(self, request, pk=None):
        """
        Soft delete de un respaldo.
        
        DELETE /api/v1/respaldos/{id}/
        """
        respaldo = self.get_object()
        
        try:
            # Eliminar archivo de S3
            backup_service = BackupService()
            if backup_service.s3_client.file_exists(respaldo.archivo_s3):
                backup_service.s3_client.delete_file(respaldo.archivo_s3)
            
            # Soft delete del registro
            respaldo.fecha_eliminacion = timezone.now()
            respaldo.save()
            
            return Response({
                'mensaje': 'Respaldo eliminado correctamente'
            }, status=status.HTTP_204_NO_CONTENT)
            
        except Exception as e:
            return Response({
                'error': 'Error al eliminar respaldo',
                'detalle': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
