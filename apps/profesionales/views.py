"""
Views para el módulo de profesionales.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Odontologo, Recepcionista
from .serializers import OdontologoSerializer, RecepcionistaSerializer
from apps.comun.permisos import EsAdministrador


class ProfesionalViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para consultar profesionales (odontólogos).
    """
    queryset = Odontologo.objects.select_related('codusuario').all()
    serializer_class = OdontologoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['codusuario__nombre', 'codusuario__apellido', 'especialidad']
    ordering_fields = ['codusuario__nombre']
    ordering = ['codusuario__nombre']
    
    @action(detail=False, methods=['get'])
    def especialidades(self, request):
        """Listar especialidades únicas de odontólogos."""
        especialidades = self.queryset.values_list('especialidad', flat=True).distinct()
        especialidades_list = [{'nombre': esp} for esp in especialidades if esp]
        return Response(especialidades_list)


class OdontologoViewSet(viewsets.ModelViewSet):
    """
    ViewSet dedicado para odontólogos con acciones detail.
    
    - GET /api/v1/profesionales/odontologos/ → lista
    - POST /api/v1/profesionales/odontologos/ → crear
    - GET /api/v1/profesionales/odontologos/{id}/ → detalle
    - PUT/PATCH /api/v1/profesionales/odontologos/{id}/ → actualizar
    - DELETE /api/v1/profesionales/odontologos/{id}/ → eliminar
    - GET /api/v1/profesionales/odontologos/{id}/horarios/ → horarios del odontólogo
    - GET /api/v1/profesionales/odontologos/{id}/disponibilidad/ → disponibilidad por fecha
    """
    queryset = Odontologo.objects.select_related('codusuario').all()
    serializer_class = OdontologoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['codusuario__nombre', 'codusuario__apellido', 'especialidad']
    ordering_fields = ['codusuario__nombre']
    ordering = ['codusuario__nombre']
    lookup_field = 'codusuario'  # Usar codusuario como PK en la URL
    
    def get_permissions(self):
        if self.action in ['create', 'destroy', 'update', 'partial_update']:
            return [IsAuthenticated(), EsAdministrador()]
        return super().get_permissions()
    
    @action(detail=True, methods=['get'])
    def horarios(self, request, codusuario=None):
        """Obtener horarios del odontólogo."""
        # NOTA: El modelo Horario actual solo tiene 'hora' e 'id', no tiene relación con odontólogos
        # Retornamos horarios genéricos de trabajo (lunes a viernes 8am-5pm)
        odontologo = self.get_object()
        
        horarios_default = [
            {'dia': 'Lunes', 'horainicio': '08:00', 'horafin': '17:00'},
            {'dia': 'Martes', 'horainicio': '08:00', 'horafin': '17:00'},
            {'dia': 'Miércoles', 'horainicio': '08:00', 'horafin': '17:00'},
            {'dia': 'Jueves', 'horainicio': '08:00', 'horafin': '17:00'},
            {'dia': 'Viernes', 'horainicio': '08:00', 'horafin': '17:00'},
        ]
        
        return Response({
            'odontologo_id': odontologo.codusuario.codigo,
            'horarios': horarios_default
        })
    
    @action(detail=True, methods=['get'])
    def disponibilidad(self, request, codusuario=None):
        """
        Verificar disponibilidad del odontólogo para una fecha específica.
        Query params: fecha (YYYY-MM-DD)
        """
        from datetime import datetime, timedelta
        from apps.citas.models import Consulta
        
        odontologo = self.get_object()
        fecha_str = request.query_params.get('fecha')
        
        if not fecha_str:
            return Response({'error': 'Parámetro "fecha" requerido'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': 'Formato de fecha inválido (YYYY-MM-DD)'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Obtener citas del día - Corregido: usar campos correctos del modelo Consulta
        citas = Consulta.objects.filter(
            cododontologo=odontologo,
            fecha=fecha
        ).values('hora_inicio_consulta', 'hora_fin_consulta')  # Corregido: nombres de campos
        
        # Obtener horario del día
        dia_semana = fecha.strftime('%A').lower()  # monday, tuesday, etc
        dias_map = {
            'monday': 'Lunes',
            'tuesday': 'Martes',
            'wednesday': 'Miércoles',
            'thursday': 'Jueves',
            'friday': 'Viernes',
            'saturday': 'Sábado',
            'sunday': 'Domingo'
        }
        dia_espanol = dias_map.get(dia_semana)
        
        # NOTA: El modelo Horario actual no tiene relación con odontólogos
        # Usamos horario por defecto: lunes a viernes 8am-5pm
        dias_laborales = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']
        
        if dia_espanol not in dias_laborales:
            return Response({
                'disponible': False,
                'mensaje': f'El odontólogo no trabaja los {dia_espanol}'
            })
        
        return Response({
            'disponible': True,
            'fecha': fecha_str,
            'dia': dia_espanol,
            'horario_trabajo': {
                'inicio': '08:00:00',
                'fin': '17:00:00'
            },
            'citas_ocupadas': list(citas),
            'total_citas': citas.count()
        })
