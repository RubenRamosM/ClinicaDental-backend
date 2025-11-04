from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Q, Count, Sum

from .models import PlanTratamiento, Presupuesto, ItemPresupuesto, Procedimiento, HistorialPago, SesionTratamiento
from .serializers import (
    PlanTratamientoSerializer,
    PlanTratamientoCrearSerializer,
    PresupuestoSerializer,
    PresupuestoCrearSerializer,
    AprobarPresupuestoSerializer,
    RechazarPresupuestoSerializer,
    ItemPresupuestoSerializer,
    ProcedimientoSerializer,
    ProcedimientoCrearSerializer,
    HistorialPagoSerializer,
    HistorialPagoCrearSerializer,
    SesionTratamientoSerializer,
    SesionTratamientoCrearSerializer,
)
from apps.comun.permisos import EsOdontologo, EsStaff


class PlanTratamientoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de planes de tratamiento.
    CU19: Crear y gestionar planes de tratamiento
    """
    queryset = PlanTratamiento.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['estado', 'paciente', 'odontologo']
    search_fields = ['codigo', 'descripcion', 'paciente__usuario__nombre', 'paciente__usuario__apellido']
    ordering_fields = ['fecha_creacion', 'fecha_aprobacion', 'estado']
    ordering = ['-fecha_creacion']

    def get_queryset(self):
        """
        Personaliza el queryset para manejar filtros del frontend.
        Mapea estado_plan -> estado y convierte valores a minúsculas.
        """
        queryset = super().get_queryset()
        
        # Obtener parámetros del frontend
        estado_plan = self.request.query_params.get('estado_plan')
        estado_aceptacion = self.request.query_params.get('estado_aceptacion')
        
        # Filtrar por estado_plan (mapear a campo 'estado')
        if estado_plan:
            # Convertir a minúsculas y mapear nombres
            estado_map = {
                'borrador': 'borrador',
                'aprobado': 'aprobado',
                'en_proceso': 'en_proceso',
                'completado': 'completado',
                'cancelado': 'cancelado',
            }
            estado_lower = estado_plan.lower()
            if estado_lower in estado_map:
                queryset = queryset.filter(estado=estado_map[estado_lower])
        
        # TODO: Implementar filtro por estado_aceptacion cuando se agregue ese campo al modelo
        # Por ahora, estado_aceptacion no existe en el modelo PlanTratamiento
        
        return queryset

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return PlanTratamientoCrearSerializer
        return PlanTratamientoSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [EsOdontologo()]
        return [IsAuthenticated()]

    @action(detail=False, methods=['get'], url_path='por-paciente')
    def por_paciente(self, request):
        """Obtener planes de tratamiento de un paciente específico"""
        paciente_id = request.query_params.get('paciente_id')
        if not paciente_id:
            return Response(
                {'error': 'Se requiere paciente_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Corregido: filtrar por el campo 'paciente' (FK a Paciente)
        planes = self.queryset.filter(paciente=paciente_id)
        serializer = self.get_serializer(planes, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='por-estado')
    def por_estado(self, request):
        """Filtrar planes por estado"""
        estado = request.query_params.get('estado')
        if not estado:
            return Response(
                {'error': 'Se requiere parámetro estado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        planes = self.queryset.filter(estado=estado)
        serializer = self.get_serializer(planes, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='validar-aprobacion')
    def validar_aprobacion(self, request, pk=None):
        """
        Valida si el usuario actual puede aprobar el plan de tratamiento.
        Usado por el frontend para habilitar/deshabilitar botones.
        """
        plan = self.get_object()
        user = request.user
        
        # Lógica de permisos
        puede_aprobar = False
        razones = []
        
        # Solo odontólogos pueden aprobar
        if not hasattr(user, 'odontologo'):
            razones.append("Solo odontólogos pueden aprobar planes")
        else:
            puede_aprobar = True
        
        # No se puede aprobar un plan ya aprobado
        if plan.estado == 'aprobado':
            puede_aprobar = False
            razones.append("El plan ya está aprobado")
        
        # No se puede aprobar un plan cancelado
        if plan.estado == 'cancelado':
            puede_aprobar = False
            razones.append("El plan está cancelado")
        
        return Response({
            'puede_aprobar': puede_aprobar,
            'razones': razones,
            'estado_actual': plan.estado,
            'es_odontologo': hasattr(user, 'odontologo'),
            'odontologo_responsable_id': plan.odontologo.codusuario.codigo if plan.odontologo else None
        })
    
    @action(detail=True, methods=['post'], url_path='agregar-item')
    def agregar_item(self, request, pk=None):
        """
        Agregar un nuevo procedimiento/ítem al plan de tratamiento.
        
        Endpoint: POST /api/v1/tratamientos/planes-tratamiento/{id}/agregar-item/
        
        Permisos:
        - Usuario debe ser Administrador u Odontólogo
        - Plan debe estar en estado 'borrador'
        
        Body:
        {
          "idservicio": 2,              // ID del servicio (OBLIGATORIO)
          "idpiezadental": 18,          // Número de pieza dental (opcional, 1-32)
          "costofinal": 180.00,         // Costo del procedimiento (OBLIGATORIO)
          "fecha_objetivo": "2024-11-15",  // Fecha planificada (opcional)
          "tiempo_estimado": 45,        // Duración en minutos (opcional)
          "estado_item": "Pendiente",   // Estado (siempre Pendiente al crear)
          "notas_item": "...",          // Observaciones (opcional)
          "orden": 1                    // Orden de ejecución (opcional)
        }
        """
        from apps.administracion_clinica.models import Servicio
        
        from apps.usuarios.models import Usuario
        from rest_framework.authtoken.models import Token
        
        plan = self.get_object()
        data = request.data
        
        # VALIDACIÓN 1: Plan debe estar en estado borrador
        if plan.estado != 'borrador':
            return Response(
                {
                    'error': 'El plan ya fue aprobado y no puede ser editado',
                    'detalle': 'Solo los planes en estado "Borrador" pueden ser modificados'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # VALIDACIÓN 2: Usuario debe tener permisos (admin u odontólogo)
        # Obtener el Usuario customizado desde el token
        try:
            # request.user es el User de Django, necesitamos obtener nuestro Usuario
            token_key = request.auth.key if request.auth else None
            if not token_key:
                return Response(
                    {'detail': 'No autenticado'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            token = Token.objects.select_related('user').get(key=token_key)
            # Obtener el Usuario customizado por email
            usuario = Usuario.objects.select_related('idtipousuario').get(
                correoelectronico=token.user.username
            )
            
            # Tipo 1 = Administrador, Tipo 2 = Odontólogo
            if usuario.idtipousuario.id not in [1, 2]:
                return Response(
                    {'detail': 'No tiene permisos para modificar este plan de tratamiento'},
                    status=status.HTTP_403_FORBIDDEN
                )
        except (Token.DoesNotExist, Usuario.DoesNotExist):
            return Response(
                {'detail': 'Usuario no válido'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # VALIDACIÓN 3: idservicio es obligatorio
        if not data.get('idservicio'):
            return Response(
                {'idservicio': ['Este campo es requerido.']},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # VALIDACIÓN 4: costofinal es obligatorio y debe ser > 0
        costofinal = data.get('costofinal')
        if not costofinal or float(costofinal) <= 0:
            return Response(
                {'costofinal': ['Asegúrese de que este valor sea mayor que 0.']},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # VALIDACIÓN 5: Servicio existe y está activo
        try:
            servicio = Servicio.objects.get(id=data['idservicio'], activo=True)
        except Servicio.DoesNotExist:
            return Response(
                {'idservicio': ['Servicio no encontrado o inactivo.']},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # VALIDACIÓN 6: Número de pieza dental válido si se proporciona
        # El frontend puede enviar:
        # - codigo (1-32): ID interno del catálogo
        # - numero FDI (11-48): Nomenclatura internacional como string
        numero_diente = data.get('idpiezadental')
        if numero_diente:
            try:
                numero_diente_int = int(numero_diente)
                
                # Si es código 1-32, convertir a número FDI usando el catálogo
                if 1 <= numero_diente_int <= 32:
                    from apps.administracion_clinica.views import PIEZAS_DENTALES_UNIVERSAL
                    pieza = next((p for p in PIEZAS_DENTALES_UNIVERSAL if p['codigo'] == numero_diente_int), None)
                    if pieza:
                        numero_diente = int(pieza['numero'])  # Convertir "18" -> 18
                    else:
                        return Response(
                            {'idpiezadental': ['Código de pieza dental no encontrado en el catálogo.']},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                # Si ya es número FDI (11-48), validar que sea correcto
                else:
                    numero_diente = numero_diente_int
                    # Validar sistema FDI (11-18, 21-28, 31-38, 41-48)
                    valid_ranges = [
                        range(11, 19), range(21, 29),  # Superior
                        range(31, 39), range(41, 49)   # Inferior
                    ]
                    if not any(numero_diente in r for r in valid_ranges):
                        return Response(
                            {'idpiezadental': ['Número de pieza dental inválido según nomenclatura FDI.']},
                            status=status.HTTP_400_BAD_REQUEST
                        )
            except (ValueError, TypeError):
                return Response(
                    {'idpiezadental': ['Debe ser un número válido.']},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Mapear campos del frontend al backend
        procedimiento_data = {
            'plan_tratamiento': plan.id,
            'servicio': data['idservicio'],
            'odontologo': plan.odontologo.codusuario_id if plan.odontologo else None,
            'numero_diente': numero_diente,
            'descripcion': data.get('notas_item', ''),
            'estado': 'pendiente',
            'fecha_planificada': data.get('fecha_objetivo'),
            'duracion_minutos': data.get('tiempo_estimado'),
            'costo_estimado': costofinal,
            'notas': data.get('notas_item', '')
        }
        
        # Crear procedimiento
        serializer = ProcedimientoCrearSerializer(data=procedimiento_data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        procedimiento = serializer.save()
        
        # Función helper para obtener nombre de pieza dental
        def obtener_nombre_pieza(numero):
            if not numero:
                return None
            piezas = {
                # Cuadrante 1 (Superior derecho)
                18: "Tercer molar superior derecho", 17: "Segundo molar superior derecho",
                16: "Primer molar superior derecho", 15: "Segundo premolar superior derecho",
                14: "Primer premolar superior derecho", 13: "Canino superior derecho",
                12: "Incisivo lateral superior derecho", 11: "Incisivo central superior derecho",
                # Cuadrante 2 (Superior izquierdo)
                21: "Incisivo central superior izquierdo", 22: "Incisivo lateral superior izquierdo",
                23: "Canino superior izquierdo", 24: "Primer premolar superior izquierdo",
                25: "Segundo premolar superior izquierdo", 26: "Primer molar superior izquierdo",
                27: "Segundo molar superior izquierdo", 28: "Tercer molar superior izquierdo",
                # Cuadrante 3 (Inferior izquierdo)
                38: "Tercer molar inferior izquierdo", 37: "Segundo molar inferior izquierdo",
                36: "Primer molar inferior izquierdo", 35: "Segundo premolar inferior izquierdo",
                34: "Primer premolar inferior izquierdo", 33: "Canino inferior izquierdo",
                32: "Incisivo lateral inferior izquierdo", 31: "Incisivo central inferior izquierdo",
                # Cuadrante 4 (Inferior derecho)
                41: "Incisivo central inferior derecho", 42: "Incisivo lateral inferior derecho",
                43: "Canino inferior derecho", 44: "Primer premolar inferior derecho",
                45: "Segundo premolar inferior derecho", 46: "Primer molar inferior derecho",
                47: "Segundo molar inferior derecho", 48: "Tercer molar inferior derecho"
            }
            return piezas.get(int(numero), f"Pieza #{numero}")
        
        # Calcular totales actualizados
        total_plan = plan.calcular_costo_total()
        
        # Respuesta en formato esperado por frontend
        return Response({
            'success': True,
            'mensaje': 'Ítem agregado exitosamente al plan',
            'item': {
                'id': procedimiento.id,
                'servicio_nombre': servicio.nombre,
                'pieza_dental_nombre': obtener_nombre_pieza(numero_diente),
                'costofinal': str(procedimiento.costo_estimado),
                'estado_item': procedimiento.get_estado_display(),
                'orden': data.get('orden', 0)
            },
            'totales': {
                'subtotal': str(total_plan),
                'descuento': '0.00',
                'total': str(total_plan)
            }
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'], url_path='cambiar-estado')
    def cambiar_estado(self, request, pk=None):
        """Cambiar estado del plan de tratamiento"""
        plan = self.get_object()
        nuevo_estado = request.data.get('estado')
        
        if nuevo_estado not in dict(PlanTratamiento.ESTADO_CHOICES):
            return Response(
                {'error': 'Estado inválido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        plan.estado = nuevo_estado
        
        # Si se aprueba, registrar fecha
        if nuevo_estado == 'aprobado' and not plan.fecha_aprobacion:
            plan.fecha_aprobacion = timezone.now()
        
        plan.save()
        serializer = self.get_serializer(plan)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='estadisticas')
    def estadisticas(self, request, pk=None):
        """Obtener estadísticas del plan de tratamiento"""
        plan = self.get_object()
        
        estadisticas = {
            'total_procedimientos': plan.procedimientos.count(),
            'procedimientos_completados': plan.procedimientos.filter(estado='completado').count(),
            'procedimientos_pendientes': plan.procedimientos.filter(estado='pendiente').count(),
            'procedimientos_en_proceso': plan.procedimientos.filter(estado='en_proceso').count(),
            'costo_total_estimado': plan.calcular_costo_total(),
            'costo_total_real': plan.procedimientos.filter(
                costo_real__isnull=False
            ).aggregate(total=Sum('costo_real'))['total'] or 0,
            'progreso_porcentaje': plan.obtener_progreso(),
            'total_presupuestos': plan.presupuestos.count(),
            'presupuestos_aprobados': plan.presupuestos.filter(estado='aprobado').count(),
        }
        
        return Response(estadisticas)

    @action(detail=True, methods=['get'], url_path='progreso-detallado')
    def progreso_detallado(self, request, pk=None):
        """
        Obtener progreso detallado con información de sesiones
        GET /api/v1/tratamientos/planes-tratamiento/{id}/progreso-detallado/
        """
        plan = self.get_object()
        items = plan.procedimientos.all()
        
        items_data = []
        for item in items:
            sesiones = SesionTratamiento.objects.filter(procedimiento=item)
            sesiones_completadas = sesiones.filter(estado='completada').count()
            sesiones_totales = sesiones.count()
            progreso = (sesiones_completadas / sesiones_totales * 100) if sesiones_totales > 0 else 0
            
            items_data.append({
                'id': item.id,
                'nombre': item.servicio.nombre if hasattr(item, 'servicio') and item.servicio else 'Sin nombre',
                'progreso': round(progreso, 2),
                'estado': item.estado,
                'sesiones_completadas': sesiones_completadas,
                'sesiones_totales': sesiones_totales
            })
        
        # Calcular totales
        total_items = items.count()
        items_completados = items.filter(estado='completado').count()
        items_en_proceso = items.filter(estado='en_proceso').count()
        items_pendientes = items.filter(estado='pendiente').count()
        
        # Sesiones totales
        todas_sesiones = SesionTratamiento.objects.filter(plan_tratamiento=plan)
        sesiones_totales = todas_sesiones.count()
        sesiones_realizadas = todas_sesiones.filter(estado='completada').count()
        
        porcentaje_global = (items_completados / total_items * 100) if total_items > 0 else 0
        
        costo_ejecutado = items.filter(costo_real__isnull=False).aggregate(
            total=Sum('costo_real'))['total'] or 0
        
        return Response({
            'plan_id': plan.id,
            'codigo_plan': plan.codigo,
            'total_items': total_items,
            'items_completados': items_completados,
            'items_en_proceso': items_en_proceso,
            'items_pendientes': items_pendientes,
            'porcentaje_global': round(porcentaje_global, 2),
            'sesiones_totales': sesiones_totales,
            'sesiones_realizadas': sesiones_realizadas,
            'costo_total': float(plan.calcular_costo_total()),
            'costo_ejecutado': float(costo_ejecutado),
            'items': items_data
        })


class PresupuestoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de presupuestos.
    CU20: Generar presupuesto
    CU21: Aprobar/rechazar presupuesto
    """
    queryset = Presupuesto.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['plan_tratamiento']  # Solo plan_tratamiento usa filtro automático
    search_fields = ['codigo', 'notas']
    ordering_fields = ['fecha_creacion', 'fecha_vencimiento', 'total']
    ordering = ['-fecha_creacion']

    def get_queryset(self):
        """
        Personaliza el queryset para manejar filtros personalizados.
        
        Normaliza valores de filtros para compatibilidad con frontend:
        - estado: Convierte a minúsculas y mapea aliases (Borrador -> pendiente)
        - es_tramo: Se ignora (no existe en modelo)
        """
        queryset = super().get_queryset()
        
        # Normalizar filtro de estado (case-insensitive + aliases)
        estado = self.request.query_params.get('estado')
        if estado:
            # Mapear nombres del frontend a valores del modelo
            estado_map = {
                'borrador': 'pendiente',
                'pendiente': 'pendiente',
                'emitido': 'pendiente',  # Alias
                'aprobado': 'aprobado',
                'aceptado': 'aprobado',  # Alias
                'rechazado': 'rechazado',
                'vencido': 'vencido',
            }
            estado_lower = estado.lower()
            if estado_lower in estado_map:
                queryset = queryset.filter(estado=estado_map[estado_lower])
        
        # El filtro 'es_tramo' no existe en el modelo Presupuesto
        # Se ignora silenciosamente para compatibilidad con frontend
        # TODO: Definir si se necesita agregar este campo al modelo
        
        return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return PresupuestoCrearSerializer
        return PresupuestoSerializer

    def get_permissions(self):
        """
        Permisos personalizados:
        - Create/Update/Delete: Staff (Administrador, Odontólogo, Recepcionista)
        - Read: Cualquier usuario autenticado
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [EsStaff()]
        return [IsAuthenticated()]

    @action(detail=True, methods=['post'], url_path='aprobar')
    def aprobar(self, request, pk=None):
        """
        Aprobar un presupuesto.
        CU21: Aprobar presupuesto
        """
        presupuesto = self.get_object()
        
        if presupuesto.estado != 'pendiente':
            return Response(
                {'error': 'Solo se pueden aprobar presupuestos pendientes'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = AprobarPresupuestoSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        presupuesto.estado = 'aprobado'
        presupuesto.fecha_aprobacion = timezone.now()
        presupuesto.aprobado_por = serializer.validated_data['aprobado_por']
        if serializer.validated_data.get('notas'):
            presupuesto.notas = serializer.validated_data['notas']
        presupuesto.save()
        
        # Cambiar estado del plan a aprobado también
        plan = presupuesto.plan_tratamiento
        if plan.estado == 'borrador':
            plan.estado = 'aprobado'
            plan.fecha_aprobacion = timezone.now()
            plan.save()
        
        return Response(
            PresupuestoSerializer(presupuesto).data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], url_path='rechazar')
    def rechazar(self, request, pk=None):
        """
        Rechazar un presupuesto.
        CU21: Rechazar presupuesto
        """
        presupuesto = self.get_object()
        
        if presupuesto.estado != 'pendiente':
            return Response(
                {'error': 'Solo se pueden rechazar presupuestos pendientes'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = RechazarPresupuestoSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        presupuesto.estado = 'rechazado'
        presupuesto.motivo_rechazo = serializer.validated_data['motivo_rechazo']
        presupuesto.save()
        
        return Response(
            PresupuestoSerializer(presupuesto).data,
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['get'], url_path='pendientes')
    def pendientes(self, request):
        """Obtener presupuestos pendientes de aprobación"""
        presupuestos = self.queryset.filter(estado='pendiente')
        serializer = self.get_serializer(presupuestos, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='por-plan')
    def por_plan(self, request):
        """Obtener presupuestos de un plan específico"""
        plan_id = request.query_params.get('plan_id')
        if not plan_id:
            return Response(
                {'error': 'Se requiere plan_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        presupuestos = self.queryset.filter(plan_tratamiento_id=plan_id)
        serializer = self.get_serializer(presupuestos, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='mis-presupuestos')
    def mis_presupuestos(self, request):
        """
        Obtener presupuestos del paciente autenticado.
        
        Endpoint: GET /api/v1/presupuestos-digitales/mis-presupuestos/
        
        Retorna todos los presupuestos asociados a los planes de tratamiento
        del paciente que realiza la petición.
        """
        # Verificar que el usuario esté autenticado
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Debes iniciar sesión'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Obtener el ID del paciente desde el usuario autenticado
        try:
            from apps.usuarios.models import Usuario, Paciente
            
            # El Token está ligado al Django User (request.user)
            # Necesitamos obtener el Usuario de nuestra app usando el correo
            try:
                usuario = Usuario.objects.get(correoelectronico=request.user.username)
            except Usuario.DoesNotExist:
                return Response(
                    {'error': 'No se encontró el usuario en el sistema'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # El modelo Paciente usa codusuario como primary key (OneToOne con Usuario)
            try:
                paciente = Paciente.objects.get(codusuario=usuario.codigo)
                paciente_id = paciente.codusuario_id  # Este es el usuario.codigo
            except Paciente.DoesNotExist:
                return Response(
                    {'error': 'No se encontró información de paciente para este usuario'},
                    status=status.HTTP_404_NOT_FOUND
                )
        except Exception as e:
            return Response(
                {'error': f'Error al obtener información del paciente: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Filtrar presupuestos por planes de tratamiento del paciente
        presupuestos = self.queryset.filter(
            plan_tratamiento__paciente_id=paciente_id
        ).select_related(
            'plan_tratamiento',
            'plan_tratamiento__paciente',
            'plan_tratamiento__odontologo'
        ).order_by('-fecha_creacion')
        
        # Paginar resultados
        page = self.paginate_queryset(presupuestos)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(presupuestos, many=True)
        return Response({
            'count': presupuestos.count(),
            'results': serializer.data
        })

    @action(detail=False, methods=['get'], url_path='planes-disponibles')
    def planes_disponibles(self, request):
        """
        Obtener planes de tratamiento disponibles para vincular a presupuestos.
        
        Endpoint: GET /api/v1/presupuestos-digitales/planes-disponibles/
        
        Retorna planes que:
        - Están en estado 'aprobado' o 'borrador'
        - Tienen al menos un procedimiento
        - Opcionalmente filtrados por paciente
        
        Query params:
        - paciente_id (opcional): Filtrar por paciente específico
        
        Respuesta:
        [
          {
            "id": 1,
            "codigo": "PLAN-202411-0001",
            "paciente": {...},
            "descripcion": "...",
            "estado": "aprobado",
            "costo_total": "1500.00",
            "cantidad_items": 3
          }
        ]
        """
        # Filtrar planes disponibles (aprobados o borradores)
        planes = PlanTratamiento.objects.filter(
            estado__in=['aprobado', 'borrador']
        ).select_related(
            'paciente__codusuario',  # Corregido: ForeignKey correcta
            'odontologo__codusuario'
        ).prefetch_related(
            'procedimientos'  # Cargar procedimientos para filtrar en Python
        )
        
        # Filtrar por paciente si se especifica
        paciente_id = request.query_params.get('paciente_id')
        if paciente_id and paciente_id != 'None':  # Evitar filtro con None/null
            try:
                planes = planes.filter(paciente_id=int(paciente_id))
            except (ValueError, TypeError):
                pass  # Ignorar valores inválidos
        
        # Filtrar planes que tengan al menos un procedimiento (hacer en Python para evitar errores SQL)
        planes_con_procedimientos = [
            plan for plan in planes 
            if plan.procedimientos.count() > 0
        ]
        
        # Serializar usando el serializer existente
        serializer = PlanTratamientoSerializer(planes_con_procedimientos, many=True)
        return Response(serializer.data)


class ProcedimientoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de procedimientos.
    CU24: Registrar procedimiento realizado
    """
    queryset = Procedimiento.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ProcedimientoCrearSerializer
        return ProcedimientoSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [EsOdontologo()]
        return [IsAuthenticated()]

    @action(detail=True, methods=['post'], url_path='marcar-completado')
    def marcar_completado(self, request, pk=None):
        """
        Marcar un procedimiento como completado.
        CU24: Registrar procedimiento realizado
        """
        procedimiento = self.get_object()
        
        if procedimiento.estado == 'completado':
            return Response(
                {'error': 'El procedimiento ya está completado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Actualizar datos del procedimiento
        procedimiento.estado = 'completado'
        procedimiento.fecha_realizado = timezone.now()
        
        # Opcional: actualizar costo real y notas
        if request.data.get('costo_real'):
            procedimiento.costo_real = request.data['costo_real']
        if request.data.get('notas'):
            procedimiento.notas = request.data['notas']
        if request.data.get('complicaciones'):
            procedimiento.complicaciones = request.data['complicaciones']
        if request.data.get('duracion_minutos'):
            procedimiento.duracion_minutos = request.data['duracion_minutos']
        
        procedimiento.save()
        
        # Verificar si todos los procedimientos del plan están completados
        plan = procedimiento.plan_tratamiento
        if plan.procedimientos.exclude(estado='completado').count() == 0:
            plan.estado = 'completado'
            plan.fecha_finalizacion = timezone.now().date()
            plan.save()
        
        return Response(
            ProcedimientoSerializer(procedimiento).data,
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['get'], url_path='por-plan')
    def por_plan(self, request):
        """Obtener procedimientos de un plan específico"""
        plan_id = request.query_params.get('plan_id')
        if not plan_id:
            return Response(
                {'error': 'Se requiere plan_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        procedimientos = self.queryset.filter(plan_tratamiento_id=plan_id)
        serializer = self.get_serializer(procedimientos, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='pendientes')
    def pendientes(self, request):
        """Obtener procedimientos pendientes"""
        procedimientos = self.queryset.filter(estado='pendiente')
        serializer = self.get_serializer(procedimientos, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='hoy')
    def hoy(self, request):
        """Obtener procedimientos planificados para hoy"""
        hoy = timezone.now().date()
        procedimientos = self.queryset.filter(
            fecha_planificada=hoy,
            estado__in=['pendiente', 'en_proceso']
        )
        serializer = self.get_serializer(procedimientos, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='progreso')
    def progreso(self, request, pk=None):
        """
        Obtener progreso de un procedimiento (ítem del plan)
        GET /api/v1/tratamientos/procedimientos/{id}/progreso/
        """
        procedimiento = self.get_object()
        
        # Obtener sesiones relacionadas
        sesiones = SesionTratamiento.objects.filter(procedimiento=procedimiento)
        sesiones_completadas = sesiones.filter(estado='completada').count()
        sesiones_totales = sesiones.count()
        
        porcentaje = (sesiones_completadas / sesiones_totales * 100) if sesiones_totales > 0 else 0
        
        ultima_sesion = sesiones.filter(estado='completada').order_by('-fecha_inicio').first()
        proxima_sesion = sesiones.filter(estado='programada').order_by('fecha_programada').first()
        
        return Response({
            'item_id': procedimiento.id,
            'nombre_item': procedimiento.servicio.nombre if hasattr(procedimiento, 'servicio') and procedimiento.servicio else 'Sin nombre',
            'sesiones_completadas': sesiones_completadas,
            'sesiones_totales': sesiones_totales,
            'porcentaje_completado': round(porcentaje, 2),
            'estado_actual': procedimiento.estado,
            'ultima_sesion_fecha': ultima_sesion.fecha_inicio if ultima_sesion else None,
            'proxima_sesion_fecha': proxima_sesion.fecha_programada if proxima_sesion else None
        })

    @action(detail=True, methods=['post'], url_path='completar')
    def completar(self, request, pk=None):
        """
        Marcar un procedimiento como completado
        POST /api/v1/tratamientos/procedimientos/{id}/completar/
        """
        procedimiento = self.get_object()
        
        if procedimiento.estado == 'completado':
            return Response(
                {'error': 'El procedimiento ya está completado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Actualizar procedimiento
        procedimiento.estado = 'completado'
        procedimiento.fecha_realizado = timezone.now()
        
        if request.data.get('observaciones'):
            procedimiento.notas = request.data['observaciones']
        if request.data.get('costo_real'):
            procedimiento.costo_real = request.data['costo_real']
        
        procedimiento.save()
        
        # Verificar si todos los procedimientos del plan están completados
        plan = procedimiento.plan_tratamiento
        plan_actualizado = False
        if plan.procedimientos.exclude(estado='completado').count() == 0:
            plan.estado = 'completado'
            plan.fecha_finalizacion = timezone.now().date()
            plan.save()
            plan_actualizado = True
        
        return Response({
            'mensaje': 'Procedimiento marcado como completado exitosamente',
            'item': {
                'id': procedimiento.id,
                'estado': procedimiento.estado,
                'fecha_completado': procedimiento.fecha_realizado,
                'observaciones': procedimiento.notas,
                'costo_real': float(procedimiento.costo_real) if procedimiento.costo_real else None
            },
            'plan_actualizado': plan_actualizado
        })


class HistorialPagoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de historial de pagos.
    Permite registrar, consultar y gestionar pagos asociados a planes de tratamiento.
    """
    queryset = HistorialPago.objects.select_related(
        'plan_tratamiento', 
        'plan_tratamiento__paciente',
        'plan_tratamiento__paciente__codusuario',
        'presupuesto'
    ).all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['plan_tratamiento', 'presupuesto', 'metodo_pago', 'estado']
    search_fields = ['codigo', 'numero_comprobante', 'numero_transaccion', 'registrado_por']
    ordering_fields = ['fecha_pago', 'monto']
    ordering = ['-fecha_pago']

    def get_serializer_class(self):
        """Usa serializer específico para creación"""
        from .serializers import HistorialPagoSerializer, HistorialPagoCrearSerializer
        
        if self.action in ['create', 'update', 'partial_update']:
            return HistorialPagoCrearSerializer
        return HistorialPagoSerializer

    def get_permissions(self):
        """
        Permisos:
        - Create: Solo staff (recepcionista/admin)
        - Read: Todos autenticados (con filtros por rol)
        - Update/Delete: Solo admin
        """
        if self.action == 'create':
            return [EsStaff()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [EsStaff()]  # Solo admin puede modificar
        return [IsAuthenticated()]

    def get_queryset(self):
        """
        Filtrar pagos según el rol del usuario:
        - Paciente: Solo sus propios pagos
        - Odontólogo: Pagos de sus pacientes
        - Staff: Todos los pagos
        """
        queryset = super().get_queryset()
        user = self.request.user
        
        # Si es paciente, filtrar solo sus pagos
        if hasattr(user, 'paciente'):
            queryset = queryset.filter(plan_tratamiento__paciente=user.paciente)
        
        # Si es odontólogo, filtrar pagos de sus pacientes
        elif hasattr(user, 'odontologo'):
            queryset = queryset.filter(plan_tratamiento__odontologo=user.odontologo)
        
        # Staff y admin ven todos los pagos (no se filtra)
        
        return queryset

    def perform_create(self, serializer):
        """
        Al crear un pago, registrar automáticamente el usuario que lo creó.
        """
        user = self.request.user
        registrado_por = f"{user.nombre} {user.apellido}" if hasattr(user, 'nombre') else str(user)
        serializer.save(registrado_por=registrado_por)

    @action(detail=False, methods=['get'], url_path='mis-pagos')
    def mis_pagos(self, request):
        """
        Obtener pagos del paciente autenticado.
        Solo disponible para pacientes.
        """
        from apps.usuarios.models import Paciente, Usuario
        
        # Patrón de puente dual: User → Usuario → Paciente
        try:
            usuario = Usuario.objects.get(correoelectronico=request.user.email)
            paciente = Paciente.objects.get(codusuario=usuario)
        except (Usuario.DoesNotExist, Paciente.DoesNotExist):
            return Response(
                {'error': 'Este endpoint solo está disponible para pacientes'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        pagos = self.queryset.filter(plan_tratamiento__paciente=paciente)
        serializer = self.get_serializer(pagos, many=True)
        
        # Calcular totales
        from decimal import Decimal
        total_pagado = pagos.filter(estado='completado').aggregate(
            total=Sum('monto')
        )['total'] or Decimal('0')
        
        return Response({
            'total_pagos': pagos.count(),
            'total_pagado': total_pagado,
            'pagos': serializer.data
        })

    @action(detail=False, methods=['get'], url_path='por-plan/(?P<plan_id>[^/.]+)')
    def por_plan(self, request, plan_id=None):
        """
        Obtener todos los pagos de un plan de tratamiento específico.
        Incluye estadísticas de pago.
        """
        from decimal import Decimal
        
        # Verificar que el plan existe
        try:
            plan = PlanTratamiento.objects.get(id=plan_id)
        except PlanTratamiento.DoesNotExist:
            return Response(
                {'error': 'Plan de tratamiento no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Filtrar pagos del plan
        pagos = self.queryset.filter(plan_tratamiento=plan)
        serializer = self.get_serializer(pagos, many=True)
        
        # Calcular estadísticas
        total_pagado = pagos.filter(estado='completado').aggregate(
            total=Sum('monto')
        )['total'] or Decimal('0')
        
        # Obtener presupuesto aprobado
        presupuesto = plan.presupuestos.filter(estado='aprobado').first()
        total_presupuesto = presupuesto.total if presupuesto else Decimal('0')
        saldo_pendiente = total_presupuesto - total_pagado
        
        return Response({
            'plan_tratamiento': {
                'id': plan.id,
                'codigo': plan.codigo,
                'descripcion': plan.descripcion,
                'estado': plan.estado
            },
            'presupuesto': {
                'id': presupuesto.id if presupuesto else None,
                'codigo': presupuesto.codigo if presupuesto else None,
                'total': total_presupuesto
            },
            'resumen_pagos': {
                'total_presupuesto': total_presupuesto,
                'total_pagado': total_pagado,
                'saldo_pendiente': saldo_pendiente,
                'cantidad_pagos': pagos.count()
            },
            'pagos': serializer.data
        })

    @action(detail=False, methods=['get'], url_path='por-presupuesto/(?P<presupuesto_id>[^/.]+)')
    def por_presupuesto(self, request, presupuesto_id=None):
        """
        Obtener pagos asociados a un presupuesto específico.
        """
        from decimal import Decimal
        
        try:
            presupuesto = Presupuesto.objects.get(id=presupuesto_id)
        except Presupuesto.DoesNotExist:
            return Response(
                {'error': 'Presupuesto no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        pagos = self.queryset.filter(presupuesto=presupuesto)
        serializer = self.get_serializer(pagos, many=True)
        
        total_pagado = pagos.filter(estado='completado').aggregate(
            total=Sum('monto')
        )['total'] or Decimal('0')
        
        return Response({
            'presupuesto': {
                'id': presupuesto.id,
                'codigo': presupuesto.codigo,
                'total': presupuesto.total,
                'estado': presupuesto.estado
            },
            'total_pagado': total_pagado,
            'saldo_pendiente': presupuesto.total - total_pagado,
            'pagos': serializer.data
        })

    @action(detail=True, methods=['post'], url_path='anular')
    def anular(self, request, pk=None):
        """
        Anular un pago (cambiar estado a 'cancelado').
        Solo staff puede anular pagos.
        Requiere motivo de anulación en el body.
        """
        pago = self.get_object()
        
        if pago.estado == 'cancelado':
            return Response(
                {'error': 'El pago ya está cancelado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        motivo = request.data.get('motivo')
        if not motivo:
            return Response(
                {'error': 'Debe proporcionar un motivo de anulación'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        pago.estado = 'cancelado'
        pago.notas = f"{pago.notas or ''}\n\nANULADO: {motivo} (por {request.user.nombre} {request.user.apellido})"
        pago.save()
        
        serializer = self.get_serializer(pago)
        return Response({
            'mensaje': 'Pago anulado exitosamente',
            'pago': serializer.data
        })

    @action(detail=False, methods=['get'], url_path='estadisticas')
    def estadisticas(self, request):
        """
        Obtener estadísticas generales de pagos.
        Disponible solo para staff.
        """
        from decimal import Decimal
        from django.db.models import Count
        
        # Verificar permisos
        if not (hasattr(request.user, 'recepcionista') or request.user.is_staff):
            return Response(
                {'error': 'No tiene permisos para ver estadísticas'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        queryset = self.queryset
        
        # Totales por estado
        totales_por_estado = queryset.values('estado').annotate(
            cantidad=Count('id'),
            total=Sum('monto')
        )
        
        # Totales por método de pago
        totales_por_metodo = queryset.filter(estado='completado').values('metodo_pago').annotate(
            cantidad=Count('id'),
            total=Sum('monto')
        )
        
        # Total general
        total_completado = queryset.filter(estado='completado').aggregate(
            total=Sum('monto')
        )['total'] or Decimal('0')
        
        return Response({
            'total_completado': total_completado,
            'cantidad_total': queryset.count(),
            'por_estado': list(totales_por_estado),
            'por_metodo_pago': list(totales_por_metodo)
        })


class SesionTratamientoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de sesiones de tratamiento.
    Permite registrar y gestionar sesiones donde se realizan procedimientos.
    """
    queryset = SesionTratamiento.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['estado', 'plan_tratamiento', 'odontologo']
    search_fields = ['codigo', 'titulo', 'descripcion']
    ordering_fields = ['fecha_programada', 'numero_sesion']
    ordering = ['-fecha_programada']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return SesionTratamientoCrearSerializer
        return SesionTratamientoSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [EsOdontologo()]
        return [IsAuthenticated()]

    @action(detail=False, methods=['get'], url_path='por-plan/(?P<plan_id>[^/.]+)')
    def por_plan(self, request, plan_id=None):
        """Obtener todas las sesiones de un plan de tratamiento específico"""
        try:
            sesiones = self.queryset.filter(plan_tratamiento_id=plan_id).order_by('numero_sesion')
            serializer = self.get_serializer(sesiones, many=True)
            return Response({
                'plan_id': plan_id,
                'count': sesiones.count(),
                'sesiones': serializer.data
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'], url_path='iniciar')
    def iniciar(self, request, pk=None):
        """Iniciar una sesión (cambiar estado a 'en_curso')"""
        sesion = self.get_object()
        
        if sesion.estado != 'programada':
            return Response(
                {'error': f'La sesión debe estar en estado "programada". Estado actual: {sesion.get_estado_display()}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        sesion.estado = 'en_curso'
        sesion.fecha_inicio = timezone.now()
        sesion.save()
        
        serializer = self.get_serializer(sesion)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='completar')
    def completar(self, request, pk=None):
        """Completar una sesión"""
        sesion = self.get_object()
        
        if sesion.estado == 'completada':
            return Response(
                {'error': 'La sesión ya está completada'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if sesion.estado == 'cancelada':
            return Response(
                {'error': 'No se puede completar una sesión cancelada'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Actualizar con datos del request si existen
        observaciones = request.data.get('observaciones')
        recomendaciones = request.data.get('recomendaciones')
        proxima_sesion = request.data.get('proxima_sesion_programada')
        
        if observaciones:
            sesion.observaciones = observaciones
        if recomendaciones:
            sesion.recomendaciones = recomendaciones
        if proxima_sesion:
            sesion.proxima_sesion_programada = proxima_sesion
        
        # Marcar como completada
        sesion.marcar_completada()
        
        serializer = self.get_serializer(sesion)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='cancelar')
    def cancelar(self, request, pk=None):
        """Cancelar una sesión"""
        sesion = self.get_object()
        
        if sesion.estado == 'completada':
            return Response(
                {'error': 'No se puede cancelar una sesión completada'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        motivo = request.data.get('motivo', '')
        sesion.estado = 'cancelada'
        if motivo:
            sesion.observaciones = f"CANCELADA: {motivo}"
        sesion.save()
        
        serializer = self.get_serializer(sesion)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='estadisticas/odontologo/(?P<odontologo_id>[^/.]+)')
    def estadisticas_odontologo(self, request, odontologo_id=None):
        """
        Obtener estadísticas de sesiones de un odontólogo
        GET /api/v1/tratamientos/sesiones-tratamiento/estadisticas/odontologo/{id}/
        """
        from apps.profesionales.models import Odontologo
        from django.db.models import Count, Avg, Sum
        from datetime import timedelta
        
        try:
            odontologo = Odontologo.objects.get(codusuario_id=odontologo_id)
        except Odontologo.DoesNotExist:
            return Response(
                {'error': 'Odontólogo no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        sesiones = self.queryset.filter(odontologo=odontologo)
        
        # Estadísticas generales
        estadisticas = {
            'sesiones_totales': sesiones.count(),
            'sesiones_completadas': sesiones.filter(estado='completada').count(),
            'sesiones_pendientes': sesiones.filter(estado='programada').count(),
            'sesiones_canceladas': sesiones.filter(estado='cancelada').count(),
            'pacientes_atendidos': sesiones.values('plan_tratamiento__paciente').distinct().count(),
        }
        
        # Estadísticas por mes (últimos 6 meses)
        hoy = timezone.now()
        hace_6_meses = hoy - timedelta(days=180)
        
        sesiones_recientes = sesiones.filter(fecha_programada__gte=hace_6_meses)
        
        por_mes = []
        for i in range(6):
            mes_inicio = hoy - timedelta(days=30 * (5 - i))
            mes_fin = hoy - timedelta(days=30 * (4 - i))
            
            sesiones_mes = sesiones_recientes.filter(
                fecha_programada__gte=mes_inicio,
                fecha_programada__lt=mes_fin
            )
            
            por_mes.append({
                'mes': mes_inicio.strftime('%B %Y'),
                'sesiones': sesiones_mes.count(),
                'pacientes': sesiones_mes.values('plan_tratamiento__paciente').distinct().count()
            })
        
        return Response({
            'odontologo_id': odontologo.codusuario.codigo,
            'nombre_completo': f"{odontologo.codusuario.nombre} {odontologo.codusuario.apellido}",
            'estadisticas': estadisticas,
            'por_mes': por_mes
        })

    @action(detail=False, methods=['get'], url_path='paciente/(?P<paciente_id>[^/.]+)')
    def por_paciente(self, request, paciente_id=None):
        """
        Obtener sesiones de un paciente específico
        GET /api/v1/tratamientos/sesiones-tratamiento/paciente/{id}/
        """
        from apps.usuarios.models import Paciente
        
        try:
            paciente = Paciente.objects.get(codusuario_id=paciente_id)
        except Paciente.DoesNotExist:
            return Response(
                {'error': 'Paciente no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        sesiones = self.queryset.filter(
            plan_tratamiento__paciente=paciente
        ).order_by('-fecha_programada')
        
        serializer = self.get_serializer(sesiones, many=True)
        
        return Response({
            'paciente_id': paciente.codusuario.codigo,
            'nombre_paciente': f"{paciente.codusuario.nombre} {paciente.codusuario.apellido}",
            'total_sesiones': sesiones.count(),
            'sesiones': serializer.data
        })
