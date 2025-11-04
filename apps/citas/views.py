"""
Views para la app de citas.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from datetime import datetime, timedelta

from .models import Horario, Estadodeconsulta, Tipodeconsulta, Consulta
from .serializers import (
    HorarioSerializer,
    EstadodeconsultaSerializer,
    TipodeconsultaSerializer,
    ConsultaSerializer,
    ConsultaDetalleSerializer,
    ConsultaCrearSerializer,
    ConsultaActualizarEstadoSerializer,
    ConsultaDiagnosticoSerializer
)
from apps.comun.permisos import EsStaff, EsOdontologo, EsPaciente, EsPropietarioOStaff


class HorarioViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para horarios.
    """
    queryset = Horario.objects.all()
    serializer_class = HorarioSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def disponibles(self, request):
        """
        Obtener horarios disponibles para una fecha.
        Query params: fecha (YYYY-MM-DD), odontologo_id (opcional)
        """
        fecha = request.query_params.get('fecha')
        odontologo_id = request.query_params.get('odontologo_id')
        
        if not fecha:
            return Response(
                {'error': 'Debe proporcionar una fecha'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obtener horarios ocupados para esa fecha (y odontólogo si se especifica)
        filtros = {'fecha': fecha}
        if odontologo_id:
            filtros['cododontologo_id'] = odontologo_id
        
        # IDs de horarios ya ocupados
        horarios_ocupados = Consulta.objects.filter(**filtros).values_list('idhorario_id', flat=True)
        
        # Solo devolver horarios NO ocupados
        horarios = Horario.objects.exclude(id__in=horarios_ocupados).order_by('hora')
        serializer = self.get_serializer(horarios, many=True)
        return Response(serializer.data)


class EstadodeconsultaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para estados de consulta.
    """
    queryset = Estadodeconsulta.objects.all()
    serializer_class = EstadodeconsultaSerializer
    permission_classes = [IsAuthenticated]


class TipodeconsultaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para tipos de consulta.
    """
    queryset = Tipodeconsulta.objects.all()
    serializer_class = TipodeconsultaSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def agendamiento_web(self, request):
        """
        Obtener tipos de consulta disponibles para agendamiento web.
        """
        tipos = Tipodeconsulta.objects.filter(permite_agendamiento_web=True)
        serializer = self.get_serializer(tipos, many=True)
        return Response(serializer.data)


class ConsultaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de consultas/citas.
    """
    queryset = Consulta.objects.select_related(
        'codpaciente__codusuario',
        'cododontologo__codusuario',
        'codrecepcionista__codusuario',
        'idhorario',
        'idtipoconsulta',
        'idestadoconsulta'
    ).all()
    permission_classes = [IsAuthenticated]  # Corregido: solo autenticación, permisos por acción
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['estado', 'idtipoconsulta', 'cododontologo', 'codpaciente', 'fecha']
    search_fields = [
        'codpaciente__codusuario__nombre',
        'codpaciente__codusuario__apellido',
        'motivo_consulta'
    ]
    ordering_fields = ['fecha', 'hora_consulta']
    ordering = ['-fecha']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ConsultaCrearSerializer
        elif self.action == 'retrieve':
            return ConsultaDetalleSerializer
        elif self.action == 'actualizar_estado':
            return ConsultaActualizarEstadoSerializer
        elif self.action == 'agregar_diagnostico':
            return ConsultaDiagnosticoSerializer
        return ConsultaSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            # Permitir a pacientes crear consultas (agendamiento web)
            return [IsAuthenticated()]
        return super().get_permissions()
    
    def create(self, request, *args, **kwargs):
        """
        Crear consulta con validación opcional de pago.
        """
        pago_id = request.data.get('pago_id')  # ID del PagoEnLinea (opcional)
        
        # Si se proporciona pago_id, validar que esté aprobado
        if pago_id:
            from apps.sistema_pagos.models import PagoEnLinea
            try:
                pago = PagoEnLinea.objects.get(id=pago_id)
                
                if pago.estado != 'aprobado':
                    return Response({
                        'error': f'El pago está en estado "{pago.estado}". Debe estar aprobado para crear la cita.',
                        'pago_estado': pago.estado
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Verificar que el pago no esté ya vinculado a otra consulta
                if pago.consulta:
                    return Response({
                        'error': 'Este pago ya está vinculado a otra consulta',
                        'consulta_id': pago.consulta.id
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
            except PagoEnLinea.DoesNotExist:
                return Response({
                    'error': 'Pago no encontrado'
                }, status=status.HTTP_404_NOT_FOUND)
        
        # Crear consulta normalmente
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        consulta = serializer.save()
        
        # Vincular pago a consulta si existe
        if pago_id:
            pago.consulta = consulta
            pago.save()
        
        headers = self.get_success_headers(serializer.data)
        response_data = serializer.data
        
        if pago_id:
            response_data['pago_vinculado'] = True
            response_data['codigo_pago'] = pago.codigo_pago
        
        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)
    
    @action(detail=False, methods=['get'])
    def mis_consultas(self, request):
        """
        Obtener consultas del paciente autenticado.
        """
        try:
            from apps.usuarios.models import Paciente, Usuario
            # Lookup en dos pasos: User.email -> Usuario -> Paciente
            usuario = Usuario.objects.get(correoelectronico=request.user.email)
            paciente = Paciente.objects.get(codusuario=usuario)
            consultas = self.get_queryset().filter(codpaciente=paciente)
            
            page = self.paginate_queryset(consultas)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = self.get_serializer(consultas, many=True)
            return Response(serializer.data)
        except Usuario.DoesNotExist:
            return Response(
                {'error': 'Usuario no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Paciente.DoesNotExist:
            return Response(
                {'error': 'El usuario no es un paciente'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def hoy(self, request):
        """
        Obtener consultas de hoy.
        """
        fecha_hoy = datetime.now().date()
        consultas = self.get_queryset().filter(fecha=fecha_hoy)
        serializer = self.get_serializer(consultas, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pendientes(self, request):
        """
        Obtener consultas pendientes de confirmación.
        """
        consultas = self.get_queryset().filter(estado='pendiente')
        serializer = self.get_serializer(consultas, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='por-fecha')
    def por_fecha(self, request):
        """
        Obtener consultas por fecha específica.
        Query params: fecha (YYYY-MM-DD)
        """
        fecha = request.query_params.get('fecha')
        if not fecha:
            return Response(
                {'error': 'Debe proporcionar el parámetro fecha'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        consultas = self.get_queryset().filter(fecha=fecha)
        serializer = self.get_serializer(consultas, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def disponibilidad(self, request):
        """
        Verificar disponibilidad de horarios para una fecha y odontólogo.
        Query params: fecha (YYYY-MM-DD), odontologo_id (opcional)
        """
        fecha = request.query_params.get('fecha')
        odontologo_id = request.query_params.get('odontologo_id')
        
        if not fecha:
            return Response(
                {'error': 'Debe proporcionar el parámetro fecha'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obtener horarios ocupados
        filtros = {'fecha': fecha}
        if odontologo_id:
            filtros['cododontologo_id'] = odontologo_id
        
        consultas_ocupadas = self.get_queryset().filter(**filtros).values_list('idhorario_id', flat=True)
        
        # Obtener horarios disponibles
        horarios_disponibles = Horario.objects.exclude(id__in=consultas_ocupadas)
        
        return Response({
            'fecha': fecha,
            'odontologo_id': odontologo_id,
            'horarios_disponibles': HorarioSerializer(horarios_disponibles, many=True).data,
            'horarios_ocupados': list(consultas_ocupadas)
        })
    
    @action(detail=True, methods=['patch'])
    def actualizar_estado(self, request, pk=None):
        """
        Actualizar estado de una consulta.
        """
        consulta = self.get_object()
        serializer = ConsultaActualizarEstadoSerializer(
            consulta, data=request.data, partial=True
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated, EsOdontologo])
    def agregar_diagnostico(self, request, pk=None):
        """
        Agregar diagnóstico y tratamiento (solo odontólogos).
        """
        consulta = self.get_object()
        serializer = ConsultaDiagnosticoSerializer(
            consulta, data=request.data, partial=True
        )
        
        if serializer.is_valid():
            serializer.save()
            # Actualizar estado a "diagnosticada"
            consulta.estado = 'diagnosticada'
            consulta.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def confirmar(self, request, pk=None):
        """
        Confirmar una consulta pendiente.
        """
        consulta = self.get_object()
        
        if consulta.estado != 'pendiente':
            return Response(
                {'error': 'Solo se pueden confirmar consultas pendientes'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        consulta.estado = 'confirmada'
        estado_confirmada = Estadodeconsulta.objects.get(estado='Confirmada')
        consulta.idestadoconsulta = estado_confirmada
        consulta.save()
        
        serializer = self.get_serializer(consulta)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        """
        Cancelar una consulta.
        """
        consulta = self.get_object()
        motivo = request.data.get('motivo_cancelacion')
        
        if not motivo:
            return Response(
                {'error': 'Debe proporcionar un motivo de cancelación'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        consulta.estado = 'cancelada'
        estado_cancelada = Estadodeconsulta.objects.get(estado='Cancelada')
        consulta.idestadoconsulta = estado_cancelada
        consulta.motivo_cancelacion = motivo
        consulta.save()
        
        serializer = self.get_serializer(consulta)
        return Response(serializer.data)
    
    @action(detail=True, methods=['patch'])
    def reprogramar(self, request, pk=None):
        """
        Reprogramar una consulta existente.
        Body: { "fecha": "YYYY-MM-DD", "idhorario": <id> }
        """
        consulta = self.get_object()
        
        nueva_fecha = request.data.get('fecha')
        nuevo_horario_id = request.data.get('idhorario')
        
        if not nueva_fecha or not nuevo_horario_id:
            return Response(
                {'error': 'Debe proporcionar fecha e idhorario'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar que el horario existe
        try:
            nuevo_horario = Horario.objects.get(id=nuevo_horario_id)
        except Horario.DoesNotExist:
            return Response(
                {'error': 'El horario especificado no existe'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Verificar que el horario no esté ocupado
        horario_ocupado = Consulta.objects.filter(
            fecha=nueva_fecha,
            idhorario=nuevo_horario,
            cododontologo=consulta.cododontologo
        ).exclude(id=consulta.id).exists()
        
        if horario_ocupado:
            return Response(
                {'error': 'El horario seleccionado ya está ocupado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Actualizar la consulta
        consulta.fecha = nueva_fecha
        consulta.idhorario = nuevo_horario
        
        # Si estaba cancelada, reactivarla como pendiente
        if consulta.estado == 'cancelada':
            consulta.estado = 'pendiente'
            try:
                estado_pendiente = Estadodeconsulta.objects.get(estado='Pendiente')
                consulta.idestadoconsulta = estado_pendiente
            except Estadodeconsulta.DoesNotExist:
                pass
        
        consulta.save()
        
        serializer = self.get_serializer(consulta)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='marcar-noshow')
    def marcar_noshow(self, request, pk=None):
        """
        Marcar una consulta como No-Show (paciente no asistió).
        CU18: No-Show Automation
        
        Automáticamente bloquea al paciente si acumula 3 o más faltas.
        """
        consulta = self.get_object()
        
        # Verificar que la consulta esté en un estado válido para marcar no-show
        if consulta.estado in ['cancelada', 'completada']:
            return Response(
                {'error': f'No se puede marcar como no-show una consulta {consulta.estado}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obtener o crear estado no_show
        try:
            estado_noshow = Estadodeconsulta.objects.get(estado__iexact='no_show')
        except Estadodeconsulta.DoesNotExist:
            # Si no existe, crear el estado
            estado_noshow = Estadodeconsulta.objects.create(
                estado='no_show',
                descripcion='Paciente no asistió a la cita'
            )
        
        # Marcar como no-show
        consulta.estado = 'no_show'
        consulta.idestadoconsulta = estado_noshow
        consulta.save()
        
        # Contar faltas del paciente
        paciente = consulta.codpaciente
        total_noshows = Consulta.objects.filter(
            codpaciente=paciente,
            estado='no_show'
        ).count()
        
        # Auto-bloqueo si tiene 3 o más faltas
        mensaje_bloqueo = None
        if total_noshows >= 3:
            from apps.autenticacion.models import BloqueoUsuario
            from django.utils import timezone
            
            # Verificar si ya está bloqueado
            usuario = paciente.codusuario
            bloqueo_existente = BloqueoUsuario.objects.filter(
                usuario=usuario,
                activo=True
            ).first()
            
            if not bloqueo_existente:
                # Crear bloqueo automático
                BloqueoUsuario.objects.create(
                    usuario=usuario,
                    motivo=f'Bloqueo automático: {total_noshows} faltas (no-show) registradas',
                    fecha_bloqueo=timezone.now(),
                    bloqueado_por=request.user,
                    activo=True
                )
                mensaje_bloqueo = f'⚠️ PACIENTE BLOQUEADO: Acumuló {total_noshows} faltas'
        
        # Respuesta
        response_data = {
            **ConsultaSerializer(consulta).data,
            'total_noshows': total_noshows,
            'mensaje': f'Consulta marcada como no-show. Total faltas del paciente: {total_noshows}'
        }
        
        if mensaje_bloqueo:
            response_data['alerta_bloqueo'] = mensaje_bloqueo
        
        return Response(response_data)
