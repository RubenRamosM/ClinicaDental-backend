"""
Views para la app de usuarios.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from .models import Tipodeusuario, Usuario, Paciente
from .serializers import (
    TipodeusuarioSerializer,
    UsuarioSerializer,
    UsuarioDetalleSerializer,
    PacienteSerializer,
    PacienteCrearSerializer,
    UsuarioActualizarNotificacionesSerializer
)
from apps.comun.permisos import EsStaff, EsAdministrador, EsPropietarioOStaff


class TipodeusuarioViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para tipos de usuario.
    """
    queryset = Tipodeusuario.objects.all()
    serializer_class = TipodeusuarioSerializer
    permission_classes = [IsAuthenticated]


class UsuarioViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de usuarios.
    """
    queryset = Usuario.objects.select_related('idtipousuario').all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['idtipousuario', 'sexo']
    search_fields = ['nombre', 'apellido', 'correoelectronico', 'telefono']
    ordering_fields = ['codigo', 'nombre', 'apellido']
    ordering = ['-codigo']
    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return UsuarioDetalleSerializer
        return UsuarioSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'destroy']:
            return [IsAuthenticated(), EsAdministrador()]
        if self.action in ['retrieve', 'update', 'partial_update']:
            return [IsAuthenticated(), EsPropietarioOStaff()]
        return super().get_permissions()
    
    @action(detail=True, methods=['patch'])
    def actualizar_notificaciones(self, request, pk=None):
        """
        Actualizar preferencias de notificaciones de un usuario.
        """
        usuario = self.get_object()
        serializer = UsuarioActualizarNotificacionesSerializer(
            usuario, data=request.data, partial=True
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def yo(self, request):
        """
        Obtener información del usuario autenticado.
        """
        # Obtener el Usuario personalizado a partir del User de Django por correo
        try:
            usuario = Usuario.objects.select_related('idtipousuario').get(
                correoelectronico=request.user.email
            )
            serializer = UsuarioDetalleSerializer(usuario)
            return Response(serializer.data)
        except Usuario.DoesNotExist:
            return Response({
                'error': 'Usuario no encontrado en el sistema'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get'], url_path='count')
    def count(self, request):
        """
        Obtener conteo total de usuarios.
        
        Endpoint: GET /api/v1/usuarios/usuarios/count/
        
        Respuesta:
        {
          "count": 150
        }
        """
        total = self.get_queryset().count()
        
        return Response({
            'count': total
        })
    
    @action(detail=False, methods=['get'], url_path='crear-usuario/campos-requeridos')
    def campos_requeridos(self, request):
        """
        Obtener campos requeridos para crear un usuario según su tipo.
        
        Endpoint: GET /api/v1/usuarios/usuarios/crear-usuario/campos-requeridos/?tipo=X
        
        Parámetros query:
        - tipo: ID del tipo de usuario (1=Paciente, 2=Odontólogo, 3=Recepcionista, 4=Administrador)
        
        Respuesta:
        {
          "campos": ["nombre", "apellido", "correo", ...],
          "opcionales": ["telefono", ...]
        }
        """
        tipo_usuario_id = request.query_params.get('tipo')
        
        if not tipo_usuario_id:
            return Response(
                {'error': 'Parámetro "tipo" es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            tipo_usuario = Tipodeusuario.objects.get(id=tipo_usuario_id)
        except Tipodeusuario.DoesNotExist:
            return Response(
                {'error': 'Tipo de usuario no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Campos comunes para todos los tipos de usuario
        campos_base = [
            'nombre',
            'apellido',
            'correoelectronico',
            'password',
            'sexo'
        ]
        
        campos_opcionales_base = [
            'telefono',
            'direccion',
            'fechanacimiento'
        ]
        
        # Campos específicos según tipo de usuario
        if tipo_usuario_id == '1':  # Paciente
            campos_especificos = ['carnetidentidad']
            opcionales_especificos = ['gruposanguineo', 'alergias', 'contactoemergencia']
        elif tipo_usuario_id == '2':  # Odontólogo
            campos_especificos = ['especialidad', 'numerolicencia']
            opcionales_especificos = ['añosexperiencia']
        elif tipo_usuario_id == '3':  # Recepcionista
            campos_especificos = []
            opcionales_especificos = ['turno']
        elif tipo_usuario_id == '4':  # Administrador
            campos_especificos = []
            opcionales_especificos = []
        else:
            campos_especificos = []
            opcionales_especificos = []
        
        return Response({
            'tipo_usuario': {
                'id': tipo_usuario.id,
                'nombre': tipo_usuario.rol
            },
            'campos_requeridos': campos_base + campos_especificos,
            'campos_opcionales': campos_opcionales_base + opcionales_especificos
        })
    
    @action(detail=False, methods=['post'], url_path='crear-usuario', permission_classes=[IsAuthenticated, EsAdministrador])
    def crear_usuario(self, request):
        """
        Crear un nuevo usuario según su tipo.
        
        Endpoint: POST /api/v1/usuarios/usuarios/crear-usuario/
        
        Body:
        {
          "tipo_usuario": 1-4,
          "datos": {
            "nombre": "Juan",
            "apellido": "Pérez",
            "correoelectronico": "juan@example.com",
            "password": "contraseña123",
            "sexo": "Masculino",
            "telefono": "12345678",
            ... campos específicos según tipo
          }
        }
        """
        from django.contrib.auth.hashers import make_password
        from apps.profesionales.models import Odontologo, Recepcionista
        
        # Validar datos requeridos
        tipo_usuario_id = request.data.get('tipo_usuario')
        datos = request.data.get('datos', {})
        
        if not tipo_usuario_id:
            return Response(
                {'error': 'Campo "tipo_usuario" es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not datos:
            return Response(
                {'error': 'Campo "datos" es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar que el tipo de usuario existe
        try:
            tipo_usuario = Tipodeusuario.objects.get(id=tipo_usuario_id)
        except Tipodeusuario.DoesNotExist:
            return Response(
                {'error': 'Tipo de usuario no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Validar campos requeridos comunes
        campos_requeridos = ['nombre', 'apellido', 'correoelectronico', 'password', 'sexo']
        for campo in campos_requeridos:
            if not datos.get(campo):
                return Response(
                    {'error': f'Campo "{campo}" es requerido'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Validar campos específicos según tipo
        if tipo_usuario_id == 1:  # Paciente
            if not datos.get('carnetidentidad'):
                return Response(
                    {'error': 'Campo "carnetidentidad" es requerido para pacientes'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        elif tipo_usuario_id == 2:  # Odontólogo
            if not datos.get('especialidad') or not datos.get('numerolicencia'):
                return Response(
                    {'error': 'Campos "especialidad" y "numerolicencia" son requeridos para odontólogos'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Validar que el correo no esté en uso
        if Usuario.objects.filter(correoelectronico=datos['correoelectronico']).exists():
            return Response(
                {'error': 'El correo electrónico ya está registrado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Crear usuario base
        try:
            # Extraer password antes de crear el usuario
            password = datos.pop('password')
            
            # Extraer campos específicos para no incluirlos en Usuario
            campos_especificos = {}
            if tipo_usuario_id == 1:  # Paciente
                campos_especificos['carnetidentidad'] = datos.pop('carnetidentidad', None)
                campos_especificos['gruposanguineo'] = datos.pop('gruposanguineo', None)
                campos_especificos['alergias'] = datos.pop('alergias', None)
                campos_especificos['contactoemergencia'] = datos.pop('contactoemergencia', None)
            elif tipo_usuario_id == 2:  # Odontólogo
                campos_especificos['especialidad'] = datos.pop('especialidad', None)
                campos_especificos['numerolicencia'] = datos.pop('numerolicencia', None)
                campos_especificos['añosexperiencia'] = datos.pop('añosexperiencia', None)
            elif tipo_usuario_id == 3:  # Recepcionista
                campos_especificos['turno'] = datos.pop('turno', None)
            
            # Extraer campos comunes opcionales
            telefono = datos.pop('telefono', None)
            direccion = datos.pop('direccion', None)
            fechanacimiento = datos.pop('fechanacimiento', None)
            
            # Crear el usuario
            usuario = Usuario.objects.create(
                nombre=datos['nombre'],
                apellido=datos['apellido'],
                correoelectronico=datos['correoelectronico'],
                sexo=datos.get('sexo', ''),
                telefono=telefono or '',
                idtipousuario=tipo_usuario
            )
            
            # TODO: Implementar hashing de password cuando se integre autenticación
            # Por ahora se guarda en texto plano (cambiar en producción)
            # usuario.password = make_password(password)
            # usuario.save()
            
            # Crear registro específico según tipo de usuario
            registro_especifico = None
            if tipo_usuario_id == 1:  # Paciente
                registro_especifico = Paciente.objects.create(
                    codusuario=usuario,
                    carnetidentidad=campos_especificos.get('carnetidentidad'),
                    fechanacimiento=fechanacimiento,
                    direccion=direccion
                )
                # TODO: Agregar campos adicionales cuando estén en el modelo
                # gruposanguineo, alergias, contactoemergencia
                
            elif tipo_usuario_id == 2:  # Odontólogo
                registro_especifico = Odontologo.objects.create(
                    codusuario=usuario,
                    especialidad=campos_especificos.get('especialidad'),
                    nromatricula=campos_especificos.get('numerolicencia'),
                    experienciaprofesional=campos_especificos.get('añosexperiencia', '')
                )
                
            elif tipo_usuario_id == 3:  # Recepcionista
                registro_especifico = Recepcionista.objects.create(
                    codusuario=usuario,
                    habilidadessoftware=campos_especificos.get('turno', '')  # Mapeo temporal
                )
            
            # Preparar respuesta
            response_data = {
                'mensaje': 'Usuario creado exitosamente',
                'usuario': {
                    'codigo': usuario.codigo,
                    'nombre': usuario.nombre,
                    'apellido': usuario.apellido,
                    'correoelectronico': usuario.correoelectronico,
                    'sexo': usuario.sexo,
                    'telefono': usuario.telefono,
                    'tipo_usuario': {
                        'id': tipo_usuario.id,
                        'nombre': tipo_usuario.rol
                    }
                }
            }
            
            # Agregar datos específicos según tipo
            if tipo_usuario_id == 1 and registro_especifico:
                response_data['paciente'] = {
                    'carnetidentidad': registro_especifico.carnetidentidad,
                    'fechanacimiento': registro_especifico.fechanacimiento,
                    'direccion': registro_especifico.direccion
                }
            elif tipo_usuario_id == 2 and registro_especifico:
                response_data['odontologo'] = {
                    'especialidad': registro_especifico.especialidad,
                    'numerolicencia': registro_especifico.nromatricula,
                    'experiencia': registro_especifico.experienciaprofesional
                }
            elif tipo_usuario_id == 3 and registro_especifico:
                response_data['recepcionista'] = {
                    'habilidades': registro_especifico.habilidadessoftware
                }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            # Si algo falla, intentar eliminar el usuario si fue creado
            if 'usuario' in locals():
                usuario.delete()
            
            return Response(
                {'error': f'Error al crear usuario: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PacienteViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de pacientes.
    """
    queryset = Paciente.objects.select_related('codusuario', 'codusuario__idtipousuario').all()
    serializer_class = PacienteSerializer
    permission_classes = [IsAuthenticated]  # Corregido: permitir a usuarios autenticados ver pacientes
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        'codusuario__nombre',
        'codusuario__apellido',
        'codusuario__correoelectronico',
        'carnetidentidad'
    ]
    ordering_fields = ['codusuario__nombre', 'fechanacimiento']
    ordering = ['-codusuario__codigo']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return PacienteCrearSerializer
        return PacienteSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]  # Permitir registro público de pacientes
        return super().get_permissions()
    
    @action(detail=False, methods=['get'])
    def mi_perfil(self, request):
        """
        Obtener perfil del paciente autenticado.
        """
        try:
            # Obtener Usuario a partir del User autenticado
            usuario = Usuario.objects.get(correoelectronico=request.user.email)
            paciente = Paciente.objects.get(codusuario=usuario)
            serializer = self.get_serializer(paciente)
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
    
    @action(detail=True, methods=['get'])
    def historial(self, request, pk=None):
        """
        Obtener historial de consultas del paciente.
        """
        paciente = self.get_object()
        from apps.citas.models import Consulta
        from apps.citas.serializers import ConsultaSerializer
        
        consultas = Consulta.objects.filter(codpaciente=paciente).order_by('-fecha')
        serializer = ConsultaSerializer(consultas, many=True)
        
        return Response(serializer.data)
