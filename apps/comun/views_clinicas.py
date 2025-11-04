"""
ViewSets para gestión de clínicas (SOLO TENANT PÚBLICO)
Permite crear, editar y desactivar clínicas desde el tenant público
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db import connection
from .models import Clinica, Dominio
from .serializers_clinicas import ClinicaSerializer, DominioSerializer, CrearClinicaSerializer


class ClinicaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de clínicas (SOLO desde tenant público)
    
    Endpoints:
    - GET /api/v1/clinicas/ - Listar todas las clínicas
    - POST /api/v1/clinicas/ - Crear nueva clínica
    - GET /api/v1/clinicas/{id}/ - Detalle de clínica
    - PUT /api/v1/clinicas/{id}/ - Actualizar clínica
    - PATCH /api/v1/clinicas/{id}/ - Actualizar parcial
    - DELETE /api/v1/clinicas/{id}/ - Eliminar clínica (soft delete)
    - POST /api/v1/clinicas/{id}/activar/ - Activar clínica
    - POST /api/v1/clinicas/{id}/desactivar/ - Desactivar clínica
    """
    queryset = Clinica.objects.all()
    serializer_class = ClinicaSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CrearClinicaSerializer
        return ClinicaSerializer
    
    def get_queryset(self):
        # Solo disponible en tenant público
        if connection.schema_name != 'public':
            return Clinica.objects.none()
        
        # Excluir el tenant público de la lista
        queryset = Clinica.objects.exclude(schema_name='public')
        
        # Filtros opcionales
        activa = self.request.query_params.get('activa', None)
        if activa is not None:
            queryset = queryset.filter(activa=activa.lower() == 'true')
        
        plan = self.request.query_params.get('plan', None)
        if plan:
            queryset = queryset.filter(plan=plan)
            
        return queryset.order_by('-fecha_creacion')
    
    def create(self, request, *args, **kwargs):
        """Crear nueva clínica con su dominio"""
        # Verificar que estamos en tenant público
        if connection.schema_name != 'public':
            return Response(
                {'error': 'Solo se pueden crear clínicas desde el tenant público'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            clinica = serializer.save()
            return Response(
                {
                    'message': 'Clínica creada exitosamente',
                    'clinica': ClinicaSerializer(clinica).data
                },
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {'error': f'Error al crear clínica: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def activar(self, request, pk=None):
        """Activar una clínica"""
        if connection.schema_name != 'public':
            return Response(
                {'error': 'Solo se pueden activar clínicas desde el tenant público'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        clinica = self.get_object()
        clinica.activa = True
        clinica.save()
        
        return Response({
            'message': f'Clínica {clinica.nombre} activada',
            'clinica': ClinicaSerializer(clinica).data
        })
    
    @action(detail=True, methods=['post'])
    def desactivar(self, request, pk=None):
        """Desactivar una clínica"""
        if connection.schema_name != 'public':
            return Response(
                {'error': 'Solo se pueden desactivar clínicas desde el tenant público'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        clinica = self.get_object()
        if clinica.schema_name == 'public':
            return Response(
                {'error': 'No se puede desactivar el tenant público'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        clinica.activa = False
        clinica.save()
        
        return Response({
            'message': f'Clínica {clinica.nombre} desactivada',
            'clinica': ClinicaSerializer(clinica).data
        })
    
    @action(detail=True, methods=['get'])
    def estadisticas(self, request, pk=None):
        """Obtener estadísticas de una clínica"""
        from django.contrib.auth.models import User
        
        clinica = self.get_object()
        
        # Cambiar temporalmente al schema de la clínica
        connection.set_tenant(clinica)
        
        try:
            # Contar usuarios, pacientes, etc.
            total_usuarios = User.objects.count()
            
            # Aquí puedes agregar más estadísticas según tus modelos
            stats = {
                'clinica': clinica.nombre,
                'schema': clinica.schema_name,
                'total_usuarios': total_usuarios,
                'plan': clinica.plan,
                'max_usuarios': clinica.max_usuarios,
                'max_pacientes': clinica.max_pacientes,
                'activa': clinica.activa,
            }
            
            return Response(stats)
        finally:
            # Volver al tenant público
            public_tenant = Clinica.objects.get(schema_name='public')
            connection.set_tenant(public_tenant)


class DominioViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de dominios de clínicas
    """
    queryset = Dominio.objects.all()
    serializer_class = DominioSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get_queryset(self):
        # Solo disponible en tenant público
        if connection.schema_name != 'public':
            return Dominio.objects.none()
        
        queryset = Dominio.objects.select_related('tenant')
        
        # Filtrar por clínica si se proporciona
        clinica_id = self.request.query_params.get('clinica', None)
        if clinica_id:
            queryset = queryset.filter(tenant_id=clinica_id)
            
        return queryset.order_by('tenant__nombre', '-is_primary')
