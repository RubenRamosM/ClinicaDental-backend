"""
Views para historial clÃ­nico.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.http import HttpResponse

from . import models, serializers
from .models import Historialclinico, DocumentoClinico
from .serializers import (
    HistorialclinicoSerializer,
    HistorialclinicoCrearSerializer,
    DocumentoClinicoSerializer,
    DocumentoClinicoCrearSerializer
)
from apps.comun.permisos import EsStaff, EsOdontologo
from apps.usuarios.models import Usuario  # ← IMPORTAR Usuario desde usuarios app


class HistorialclinicoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestiÃ³n de historial clÃ­nico.
    
    Endpoints:
    - GET /api/v1/historia-clinica/historiales/
    - POST /api/v1/historia-clinica/historiales/
    - GET /api/v1/historia-clinica/historiales/{id}/
    - PUT /api/v1/historia-clinica/historiales/{id}/
    - DELETE /api/v1/historia-clinica/historiales/{id}/
    - GET /api/v1/historia-clinica/historiales/por_paciente/?paciente_id=1
    - GET /api/v1/historia-clinica/historiales/{id}/documentos/
    """
    queryset = Historialclinico.objects.all()
    serializer_class = HistorialclinicoSerializer
    permission_classes = [IsAuthenticated]  # Permitir a odontólogos autenticados
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['pacientecodigo']  # Corregido: campo correcto del modelo
    search_fields = ['descripcion']  # Corregido: campo que existe en el modelo
    ordering_fields = ['fecha']  # Corregido: sin created_at
    ordering = ['-fecha']
    
    def get_serializer_class(self):
        """Seleccionar serializer según acción."""
        if self.action == 'create':
            return HistorialclinicoCrearSerializer
        return HistorialclinicoSerializer
    
    def create(self, request, *args, **kwargs):
        """
        Crear historia clínica y devolver respuesta con serializer completo.
        
        Fix: Usa HistorialclinicoCrearSerializer para validación (sin id),
        pero HistorialclinicoSerializer para la respuesta (con id, episodio, fecha).
        """
        # Validar y crear con serializer de creación
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        
        # Usar serializer completo para la respuesta
        response_serializer = HistorialclinicoSerializer(instance)
        headers = self.get_success_headers(response_serializer.data)
        
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )
    
    def get_permissions(self):
        """Permisos específicos: solo odontólogos pueden crear/editar."""
        if self.action in ['create', 'update', 'partial_update']:
            return [IsAuthenticated(), EsOdontologo()]
        return super().get_permissions()
    
    @action(detail=False, methods=['get'])
    def por_paciente(self, request):
        """Listar historial de un paciente específico."""
        paciente_id = request.query_params.get('paciente_id')
        
        if not paciente_id:
            return Response(
                {'error': 'Debe proporcionar paciente_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        historiales = self.queryset.filter(pacientecodigo_id=paciente_id)
        serializer = self.get_serializer(historiales, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def documentos(self, request, pk=None):
        """Listar documentos asociados a un historial."""
        historial = self.get_object()
        documentos = DocumentoClinico.objects.filter(historial=historial)
        
        serializer = DocumentoClinicoSerializer(documentos, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='paciente/(?P<paciente_id>[^/.]+)')
    def paciente(self, request, paciente_id=None):
        """Obtener historial completo de un paciente por ID."""
        historiales = self.queryset.filter(pacientecodigo_id=paciente_id).order_by('-fecha')  # Corregido: pacientecodigo_id
        page = self.paginate_queryset(historiales)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(historiales, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='odontograma/(?P<paciente_id>[^/.]+)')
    def odontograma(self, request, paciente_id=None):
        """Obtener odontograma de un paciente."""
        # Corregido: usar modelo del mismo archivo models.py (no importar models_odontograma)
        from .models import Odontograma
        try:
            odontograma = Odontograma.objects.filter(paciente_id=paciente_id).first()
            if not odontograma:
                return Response({'error': 'Odontograma no encontrado'}, status=status.HTTP_404_NOT_FOUND)
            # Aquí retornar datos del odontograma (simplificado)
            return Response({'paciente_id': paciente_id, 'odontograma': 'datos del odontograma'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def ultimos(self, request):
        """Obtener últimos registros de historial clínico."""
        limit = int(request.query_params.get('limit', 10))
        historiales = self.queryset.order_by('-fecha')[:limit]  # Corregido: usar -fecha en lugar de -created_at
        serializer = self.get_serializer(historiales, many=True)
        return Response(serializer.data)


class DocumentoClinicoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestiÃ³n de documentos clÃ­nicos.
    
    Endpoints:
    - GET /api/v1/historia-clinica/documentos/
    - POST /api/v1/historia-clinica/documentos/ (multipart/form-data)
    - GET /api/v1/historia-clinica/documentos/{id}/
    - DELETE /api/v1/historia-clinica/documentos/{id}/
    - GET /api/v1/historia-clinica/documentos/por_paciente/?paciente_id=1
    - GET /api/v1/historia-clinica/documentos/por_tipo/?tipo=radiografia
    """
    queryset = DocumentoClinico.objects.all()
    serializer_class = DocumentoClinicoSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['historial', 'tipo_documento']
    search_fields = ['titulo', 'descripcion']
    ordering_fields = ['fecha_subida']
    ordering = ['-fecha_subida']
    
    def get_serializer_class(self):
        """Seleccionar serializer segÃºn acciÃ³n."""
        if self.action == 'create':
            return DocumentoClinicoCrearSerializer
        return DocumentoClinicoSerializer
    
    @action(detail=False, methods=['get'])
    def por_paciente(self, request):
        """Listar documentos de un paciente."""
        paciente_id = request.query_params.get('paciente_id')
        
        if not paciente_id:
            return Response(
                {'error': 'Debe proporcionar paciente_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        documentos = self.queryset.filter(historial__pacientecodigo_id=paciente_id)
        serializer = self.get_serializer(documentos, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def por_tipo(self, request):
        """Filtrar documentos por tipo."""
        tipo = request.query_params.get('tipo')
        
        if not tipo:
            return Response(
                {'error': 'Debe proporcionar el parÃ¡metro tipo'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        documentos = self.queryset.filter(tipo_documento__icontains=tipo)
        serializer = self.get_serializer(documentos, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], url_path='download_url')
    def download_url(self, request, pk=None):
        """
        Obtener la URL de descarga de un documento.
        
        Endpoint: GET /api/v1/historia-clinica/documentos/{id}/download_url/
        """
        documento = self.get_object()
        
        # Construir URL absoluta para el archivo
        if documento.archivo_url:
            # Si la URL ya es absoluta (http/https), usarla tal cual
            if documento.archivo_url.startswith(('http://', 'https://')):
                download_url = documento.archivo_url
            else:
                # Construir URL absoluta desde la URL relativa
                download_url = request.build_absolute_uri(documento.archivo_url)
        else:
            download_url = None
        
        return Response({
            'id': documento.id,
            'titulo': documento.titulo,
            'archivo_url': download_url,  # URL completa
            'download_url': download_url,  # Campo que espera el frontend
            'tipo_documento': documento.tipo_documento,
            'fecha_subida': documento.fecha_subida
        })
    
    def perform_destroy(self, instance):
        """Al eliminar, tambiÃ©n eliminar archivo de S3."""
        # TODO: Implementar eliminaciÃ³n de S3
        # from apps.api.supabase_client import supabase_client
        # supabase_client.delete_file(instance.archivo_url)
        
        instance.delete()


# =============== ODONTOGRAMA DIGITAL ===============

class OdontogramaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestiÃ³n de odontogramas.
    
    Endpoints:
    - GET /api/v1/historia-clinica/odontogramas/
    - POST /api/v1/historia-clinica/odontogramas/
    - GET /api/v1/historia-clinica/odontogramas/{id}/
    - PUT /api/v1/historia-clinica/odontogramas/{id}/
    - DELETE /api/v1/historia-clinica/odontogramas/{id}/
    - GET /api/v1/historia-clinica/odontogramas/por_paciente/?paciente_id=1
    - POST /api/v1/historia-clinica/odontogramas/{id}/actualizar_diente/
    - GET /api/v1/historia-clinica/odontogramas/{id}/estadisticas/
    """
    queryset = models.Odontograma.objects.all()
    serializer_class = serializers.OdontogramaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['paciente', 'odontologo']
    search_fields = ['paciente__codusuario__nombre', 'paciente__codusuario__apellido']
    ordering_fields = ['fecha_creacion', 'fecha_actualizacion']
    ordering = ['-fecha_actualizacion']
    
    def get_serializer_class(self):
        """Seleccionar serializer segÃºn acciÃ³n."""
        if self.action == 'create':
            return serializers.OdontogramaCrearSerializer
        elif self.action == 'actualizar_diente':
            return serializers.ActualizarDienteSerializer
        return serializers.OdontogramaSerializer
    
    def get_permissions(self):
        """Permisos especÃ­ficos: solo odontÃ³logos pueden crear/editar."""
        if self.action in ['create', 'update', 'partial_update', 'actualizar_diente']:
            return [IsAuthenticated(), EsOdontologo()]
        return super().get_permissions()
    
    @action(detail=False, methods=['get'])
    def por_paciente(self, request):
        """Listar odontogramas de un paciente."""
        paciente_id = request.query_params.get('paciente_id')
        
        if not paciente_id:
            return Response(
                {'error': 'Debe proporcionar paciente_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        odontogramas = self.queryset.filter(paciente__codusuario=paciente_id)
        serializer = self.get_serializer(odontogramas, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def actualizar_diente(self, request, pk=None):
        """Actualizar el estado de un diente especÃ­fico."""
        odontograma = self.get_object()
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            numero_diente = serializer.validated_data['numero_diente']
            estado = serializer.validated_data['estado']
            caras = serializer.validated_data.get('caras_afectadas', [])
            observaciones = serializer.validated_data.get('observaciones', '')
            
            odontograma.actualizar_diente(numero_diente, estado, caras, observaciones)
            
            return Response({
                'mensaje': f'Diente #{numero_diente} actualizado correctamente',
                'diente': odontograma.dientes.get(str(numero_diente))
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def estadisticas(self, request, pk=None):
        """Obtener estadÃ­sticas del estado dental."""
        odontograma = self.get_object()
        stats = odontograma.obtener_estadisticas()
        
        paciente_nombre = "Sin nombre"
        if odontograma.paciente and odontograma.paciente.codusuario:
            paciente_nombre = f"{odontograma.paciente.codusuario.nombre} {odontograma.paciente.codusuario.apellido}"
        
        return Response({
            'paciente': paciente_nombre,
            'fecha_actualizacion': odontograma.fecha_actualizacion,
            'estadisticas': stats,
            'total_dientes': sum(stats.values())
        })


class TratamientoOdontologicoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestiÃ³n de tratamientos odontolÃ³gicos.
    
    Endpoints:
    - GET /api/v1/historia-clinica/tratamientos-odonto/
    - POST /api/v1/historia-clinica/tratamientos-odonto/
    - GET /api/v1/historia-clinica/tratamientos-odonto/{id}/
    - PUT /api/v1/historia-clinica/tratamientos-odonto/{id}/
    - DELETE /api/v1/historia-clinica/tratamientos-odonto/{id}/
    - GET /api/v1/historia-clinica/tratamientos-odonto/por_odontograma/?odontograma_id=1
    """
    queryset = models.TratamientoOdontologico.objects.all()
    serializer_class = serializers.TratamientoOdontologicoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['odontograma', 'numero_diente']
    search_fields = ['tipo_tratamiento', 'descripcion']
    ordering_fields = ['fecha_tratamiento']
    ordering = ['-fecha_tratamiento']
    
    def get_permissions(self):
        """Solo odontÃ³logos pueden crear/editar."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), EsOdontologo()]
        return super().get_permissions()
    
    @action(detail=False, methods=['get'])
    def por_odontograma(self, request):
        """Listar tratamientos de un odontograma."""
        odontograma_id = request.query_params.get('odontograma_id')
        
        if not odontograma_id:
            return Response(
                {'error': 'Debe proporcionar odontograma_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        tratamientos = self.queryset.filter(odontograma_id=odontograma_id)
        serializer = self.get_serializer(tratamientos, many=True)
        return Response(serializer.data)


class ConsentimientoInformadoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestiÃ³n de consentimientos informados.
    CU13: Gestionar consentimiento informado
    
    Endpoints:
    - GET /api/v1/historia-clinica/consentimientos/
    - POST /api/v1/historia-clinica/consentimientos/
    - GET /api/v1/historia-clinica/consentimientos/{id}/
    - POST /api/v1/historia-clinica/consentimientos/{id}/firmar/
    - GET /api/v1/historia-clinica/consentimientos/pendientes/
    - GET /api/v1/historia-clinica/consentimientos/por_paciente/?paciente_id=1
    """
    queryset = models.ConsentimientoInformado.objects.select_related(
        'paciente__codusuario',
        'odontologo__codusuario'
    ).all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['estado', 'paciente', 'odontologo']
    search_fields = ['tipo_tratamiento', 'contenido_documento']
    ordering_fields = ['fecha_creacion', 'fecha_firma']
    ordering = ['-fecha_creacion']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return serializers.ConsentimientoCrearSerializer
        elif self.action == 'firmar':
            return serializers.FirmarConsentimientoSerializer
        return serializers.ConsentimientoInformadoSerializer
    
    def get_permissions(self):
        """
        Permisos:
        - Crear/editar/eliminar: Solo odontólogos
        - Firmar: Pacientes autenticados
        - Crear y firmar: Pacientes autenticados
        - Listar/ver: Autenticados
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), EsOdontologo()]
        elif self.action in ['firmar', 'crear_y_firmar']:
            # Pacientes pueden firmar sus propios consentimientos
            return [IsAuthenticated()]
        return super().get_permissions()
    
    @action(detail=False, methods=['post'], url_path='crear-y-firmar')
    def crear_y_firmar(self, request):
        """
        Crear y firmar un consentimiento en un solo paso (para pacientes).
        
        Endpoint: POST /api/v1/historial-clinico/consentimientos/crear-y-firmar/
        Body: {
            "paciente": codigo_paciente,
            "consulta": id_consulta (opcional),
            "tipo_tratamiento": "...",
            "contenido_documento": "...",
            "firma_paciente_url": "...",
            "firma_tutor_url": "..." (opcional),
            "nombre_tutor": "..." (opcional),
            "documento_tutor": "..." (opcional)
        }
        """
        from django.utils import timezone
        
        # Validar que el usuario autenticado es un paciente
        usuario = Usuario.objects.filter(
            correoelectronico=request.user.username
        ).first()
        
        # ✅ CORREGIDO: idtipousuario es ForeignKey, usar _id para comparar el ID directamente
        if not usuario or usuario.idtipousuario_id != 4:  # 4 = Paciente
            return Response(
                {'error': 'Solo los pacientes pueden usar este endpoint'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validar que el paciente esté firmando su propio documento
        paciente_id = request.data.get('paciente')
        if paciente_id != usuario.codigo:
            return Response(
                {'error': 'Solo puede firmar sus propios consentimientos'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validar que la consulta pertenece al paciente (si se proporciona)
        consulta_id = request.data.get('consulta')
        if consulta_id:
            from apps.citas.models import Consulta
            from apps.usuarios.models import Paciente
            
            try:
                # ✅ CORREGIDO: Paciente usa codusuario_id (no codigo) como primary key
                paciente = Paciente.objects.get(codusuario_id=usuario.codigo)
                consulta = Consulta.objects.get(id=consulta_id)
                
                if consulta.codpaciente != paciente:
                    return Response(
                        {'error': 'No puede firmar consentimientos de citas que no le pertenecen'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except Consulta.DoesNotExist:
                return Response(
                    {'error': 'La consulta especificada no existe'},
                    status=status.HTTP_404_NOT_FOUND
                )
            except Paciente.DoesNotExist:
                return Response(
                    {'error': 'Perfil de paciente no encontrado'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Crear el consentimiento
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Guardar con estado 'firmado' y fecha de firma
        consentimiento = serializer.save(
            estado='firmado',
            fecha_firma=timezone.now()
        )
        
        # Capturar IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            consentimiento.ip_firma = x_forwarded_for.split(',')[0]
        else:
            consentimiento.ip_firma = request.META.get('REMOTE_ADDR')
        consentimiento.save()
        
        # ✅ FIX: Usar serializer completo para la respuesta (incluye consulta)
        response_serializer = serializers.ConsentimientoInformadoSerializer(consentimiento)
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def firmar(self, request, pk=None):
        """
        Firmar un consentimiento informado.
        CU13: Firmar consentimiento
        """
        consentimiento = self.get_object()
        
        # Validar estado
        if consentimiento.estado != 'pendiente':
            return Response(
                {'error': f'No se puede firmar un consentimiento {consentimiento.estado}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar datos
        serializer = serializers.FirmarConsentimientoSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Actualizar consentimiento
        from django.utils import timezone
        consentimiento.firma_paciente_url = serializer.validated_data['firma_paciente_url']
        consentimiento.estado = 'firmado'
        consentimiento.fecha_firma = timezone.now()
        
        # Datos opcionales del tutor
        if serializer.validated_data.get('firma_tutor_url'):
            consentimiento.firma_tutor_url = serializer.validated_data['firma_tutor_url']
        if serializer.validated_data.get('nombre_tutor'):
            consentimiento.nombre_tutor = serializer.validated_data['nombre_tutor']
        if serializer.validated_data.get('documento_tutor'):
            consentimiento.documento_tutor = serializer.validated_data['documento_tutor']
        
        # Capturar IP
        if serializer.validated_data.get('ip_firma'):
            consentimiento.ip_firma = serializer.validated_data['ip_firma']
        else:
            # Intentar obtener IP del request
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                consentimiento.ip_firma = x_forwarded_for.split(',')[0]
            else:
                consentimiento.ip_firma = request.META.get('REMOTE_ADDR')
        
        consentimiento.save()
        
        return Response(
            serializers.ConsentimientoInformadoSerializer(consentimiento).data,
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'])
    def pendientes(self, request):
        """Obtener consentimientos pendientes de firma."""
        consentimientos = self.queryset.filter(estado='pendiente')
        serializer = self.get_serializer(consentimientos, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def por_paciente(self, request):
        """Obtener consentimientos de un paciente específico."""
        paciente_id = request.query_params.get('paciente_id')
        
        if not paciente_id:
            return Response(
                {'error': 'Debe proporcionar paciente_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        consentimientos = self.queryset.filter(paciente__codusuario=paciente_id)
        serializer = self.get_serializer(consentimientos, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def vigentes(self, request):
        """Obtener solo consentimientos vigentes."""
        from django.utils import timezone
        from django.db.models import Q
        hoy = timezone.now().date()
        
        consentimientos = self.queryset.filter(
            estado='firmado'
        ).filter(
            Q(fecha_vencimiento__isnull=True) | 
            Q(fecha_vencimiento__gte=hoy)
        )
        
        serializer = self.get_serializer(consentimientos, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], url_path='pdf')
    def pdf(self, request, pk=None):
        """
        Generar y descargar PDF del consentimiento informado.
        
        Endpoint: GET /api/v1/historial-clinico/consentimientos/{id}/pdf/
        """
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
        from reportlab.lib import colors
        from io import BytesIO
        
        consentimiento = self.get_object()
        
        # Crear buffer para el PDF
        buffer = BytesIO()
        
        # Crear documento
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )
        
        # Contenedor para elementos del PDF
        elements = []
        
        # Estilos
        styles = getSampleStyleSheet()
        style_title = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        style_heading = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        )
        style_normal = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=11,
            alignment=TA_JUSTIFY,
            spaceAfter=12
        )
        
        # Título
        elements.append(Paragraph("CONSENTIMIENTO INFORMADO", style_title))
        elements.append(Spacer(1, 0.2*inch))
        
        # Información del paciente
        elements.append(Paragraph("INFORMACIÓN DEL PACIENTE", style_heading))
        
        paciente_nombre = "N/A"
        if consentimiento.paciente and consentimiento.paciente.codusuario:
            paciente_nombre = f"{consentimiento.paciente.codusuario.nombre} {consentimiento.paciente.codusuario.apellido}"
        
        odontologo_nombre = "N/A"
        if consentimiento.odontologo and consentimiento.odontologo.codusuario:
            odontologo_nombre = f"{consentimiento.odontologo.codusuario.nombre} {consentimiento.odontologo.codusuario.apellido}"
        
        data_paciente = [
            ['Paciente:', paciente_nombre],
            ['Odontólogo:', odontologo_nombre],
            ['Tratamiento:', consentimiento.tipo_tratamiento or 'N/A'],
            ['Fecha:', consentimiento.fecha_creacion.strftime('%d/%m/%Y')],
            ['Estado:', consentimiento.estado.upper()],
        ]
        
        if consentimiento.fecha_firma:
            data_paciente.append(['Fecha Firma:', consentimiento.fecha_firma.strftime('%d/%m/%Y %H:%M')])
        
        table = Table(data_paciente, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e5e7eb')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Contenido del consentimiento
        elements.append(Paragraph("CONTENIDO DEL CONSENTIMIENTO", style_heading))
        contenido_texto = consentimiento.contenido_documento or "No se ha proporcionado contenido."
        elements.append(Paragraph(contenido_texto, style_normal))
        elements.append(Spacer(1, 0.3*inch))
        
        # Riesgos
        if consentimiento.riesgos:
            elements.append(Paragraph("RIESGOS ASOCIADOS", style_heading))
            elements.append(Paragraph(consentimiento.riesgos, style_normal))
            elements.append(Spacer(1, 0.2*inch))
        
        # Beneficios
        if consentimiento.beneficios:
            elements.append(Paragraph("BENEFICIOS ESPERADOS", style_heading))
            elements.append(Paragraph(consentimiento.beneficios, style_normal))
            elements.append(Spacer(1, 0.2*inch))
        
        # Alternativas
        if consentimiento.alternativas:
            elements.append(Paragraph("ALTERNATIVAS DE TRATAMIENTO", style_heading))
            elements.append(Paragraph(consentimiento.alternativas, style_normal))
            elements.append(Spacer(1, 0.3*inch))
        
        # Información de firma (si está firmado)
        if consentimiento.estado == 'firmado':
            elements.append(Paragraph("INFORMACIÓN DE FIRMA", style_heading))
            
            data_firma = [
                ['Firmado el:', consentimiento.fecha_firma.strftime('%d/%m/%Y %H:%M:%S') if consentimiento.fecha_firma else 'N/A'],
            ]
            
            if consentimiento.ip_firma:
                data_firma.append(['IP:', consentimiento.ip_firma])
            
            if consentimiento.nombre_tutor:
                data_firma.append(['Tutor Legal:', consentimiento.nombre_tutor])
                if consentimiento.documento_tutor:
                    data_firma.append(['Documento Tutor:', consentimiento.documento_tutor])
            
            table_firma = Table(data_firma, colWidths=[2*inch, 4*inch])
            table_firma.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e5e7eb')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            elements.append(table_firma)
        
        # Construir PDF
        doc.build(elements)
        
        # Obtener PDF del buffer
        pdf = buffer.getvalue()
        buffer.close()
        
        # Crear respuesta HTTP
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f"consentimiento_{consentimiento.id}_{paciente_nombre.replace(' ', '_')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response



