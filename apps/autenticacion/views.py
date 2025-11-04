"""
Views para autenticación.
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authtoken.models import Token
from django.contrib.auth import logout
from django.contrib.auth import authenticate
from django.contrib.auth.models import User

from .serializers import (
    LoginSerializer,
    RecuperarPasswordSerializer,
    CambiarPasswordSerializer,
    TokenSerializer,
    ActualizarPerfilSerializer,
    RegistroSerializer
)
from .models import BloqueoUsuario
from apps.auditoria.utils import registrar_login, registrar_logout


class LoginView(APIView):
    """
    Vista para login de usuarios.
    
    POST /api/v1/auth/login/
    Body: { "correo": "email@example.com", "password": "password123" }
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():
            usuario = serializer.validated_data['usuario']
            django_user = serializer.validated_data.get('django_user')

            # Verificar si el usuario está bloqueado
            bloqueo_activo = BloqueoUsuario.objects.filter(
                usuario=usuario,
                activo=True
            ).first()

            if bloqueo_activo:
                return Response({
                    'error': 'Usuario bloqueado',
                    'motivo': bloqueo_activo.motivo,
                    'fecha_fin': bloqueo_activo.fecha_fin
                }, status=status.HTTP_403_FORBIDDEN)

            # Crear/obtener token de autenticación ligado al Django User autenticado
            token, created = Token.objects.get_or_create(user=django_user)

            # Registrar login exitoso en auditoría
            registrar_login(request, usuario.correoelectronico, exitoso=True)

            from apps.usuarios.serializers import UsuarioDetalleSerializer
            return Response({
                'mensaje': 'Login exitoso',
                'usuario': UsuarioDetalleSerializer(usuario).data,
                'token': token.key
            }, status=status.HTTP_200_OK)

        # Registrar login fallido
        correo = request.data.get('correo', 'desconocido')
        registrar_login(request, correo, exitoso=False)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """
    Vista para logout de usuarios.
    
    POST /api/v1/auth/logout/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # Registrar logout en auditoría
        try:
            from apps.usuarios.models import Usuario
            usuario = Usuario.objects.get(correoelectronico=request.user.email)
            registrar_logout(request, usuario.correoelectronico)
        except:
            pass
        
        # Eliminar token asociado al usuario autenticado (si existe)
        try:
            request.user.auth_token.delete()
        except Exception:
            pass

        logout(request)
        return Response({
            'mensaje': 'Sesión cerrada exitosamente'
        }, status=status.HTTP_200_OK)


class RecuperarPasswordView(APIView):
    """
    Vista para solicitar recuperación de contraseña.
    
    POST /api/v1/auth/recuperar-password/
    Body: { "correo": "email@example.com" }
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = RecuperarPasswordSerializer(data=request.data)
        
        if serializer.is_valid():
            correo = serializer.validated_data['correo']
            
            # TODO: Generar token de recuperación y enviar email
            # from django.core.mail import send_mail
            # token = generate_password_reset_token(usuario)
            # send_mail(...)
            
            return Response({
                'mensaje': f'Se ha enviado un correo a {correo} con instrucciones para recuperar su contraseña.'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CambiarPasswordView(APIView):
    """
    Vista para cambiar contraseña del usuario autenticado.
    
    POST /api/v1/auth/cambiar-password/
    Body: {
        "password_actual": "old123",
        "password_nuevo": "new123456",
        "password_confirmacion": "new123456"
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = CambiarPasswordSerializer(data=request.data)
        
        if serializer.is_valid():
            user = request.user
            
            # Verificar password actual
            if not user.check_password(serializer.validated_data['password_actual']):
                return Response({
                    'error': 'Contraseña actual incorrecta'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Cambiar contraseña
            user.set_password(serializer.validated_data['password_nuevo'])
            user.save()
            
            # Regenerar token después de cambiar contraseña
            try:
                Token.objects.filter(user=user).delete()
                new_token = Token.objects.create(user=user)
                
                return Response({
                    'mensaje': 'Contraseña cambiada exitosamente',
                    'token': new_token.key  # Nuevo token
                }, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({
                    'mensaje': 'Contraseña cambiada pero hubo error al regenerar token',
                    'error': str(e)
                }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerificarTokenView(APIView):
    """
    Vista para verificar si un token es válido.
    
    GET /api/v1/auth/verificar-token/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        from apps.usuarios.serializers import UsuarioDetalleSerializer

        # Si llegó aquí, el token es válido (IsAuthenticated)
        # Mapear el Django User a nuestro modelo Usuario por correo
        usuario = None
        try:
            if request.user and request.user.email:
                from apps.usuarios.models import Usuario
                usuario = Usuario.objects.filter(correoelectronico=request.user.email).first()
        except Exception:
            usuario = None

        return Response({
            'valido': True,
            'usuario': UsuarioDetalleSerializer(usuario).data if usuario else None
        }, status=status.HTTP_200_OK)


class PerfilView(APIView):
    """
    Vista para ver y actualizar el perfil del usuario autenticado.
    
    GET /api/v1/auth/perfil/
    Retorna los datos del perfil del usuario autenticado
    
    PATCH /api/v1/auth/perfil/
    Body: { "nombre": "Nuevo Nombre", "telefono": "12345678", etc }
    Actualiza los datos del perfil
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Obtener datos del perfil del usuario autenticado."""
        from apps.usuarios.models import Usuario
        from apps.usuarios.serializers import UsuarioDetalleSerializer
        
        try:
            usuario = Usuario.objects.get(correoelectronico=request.user.email)
            return Response(
                UsuarioDetalleSerializer(usuario).data,
                status=status.HTTP_200_OK
            )
        except Usuario.DoesNotExist:
            return Response({
                'error': 'Usuario no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def patch(self, request):
        """Actualizar datos del perfil del usuario autenticado."""
        from apps.usuarios.models import Usuario, Paciente
        from apps.usuarios.serializers import UsuarioDetalleSerializer
        
        serializer = ActualizarPerfilSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            usuario = Usuario.objects.get(correoelectronico=request.user.email)
            
            # Actualizar campos del usuario
            if 'nombre' in serializer.validated_data:
                usuario.nombre = serializer.validated_data['nombre']
            
            if 'apellido' in serializer.validated_data:
                usuario.apellido = serializer.validated_data['apellido']
            
            if 'telefono' in serializer.validated_data:
                usuario.telefono = serializer.validated_data['telefono']
            
            if 'notificaciones_email' in serializer.validated_data:
                usuario.notificaciones_email = serializer.validated_data['notificaciones_email']
            
            if 'notificaciones_push' in serializer.validated_data:
                usuario.notificaciones_push = serializer.validated_data['notificaciones_push']
            
            usuario.save()
            
            # Si es paciente, actualizar campos específicos
            if 'direccion' in serializer.validated_data:
                try:
                    paciente = Paciente.objects.get(codusuario=usuario)
                    paciente.direccion = serializer.validated_data['direccion']
                    paciente.save()
                except Paciente.DoesNotExist:
                    pass  # No es paciente, ignorar
            
            return Response({
                'mensaje': 'Perfil actualizado exitosamente',
                'usuario': UsuarioDetalleSerializer(usuario).data
            }, status=status.HTTP_200_OK)
            
        except Usuario.DoesNotExist:
            return Response({
                'error': 'Usuario no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': f'Error al actualizar perfil: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RegistroView(APIView):
    """
    Vista para registro de nuevos usuarios.
    
    POST /api/v1/auth/registro/
    Body: {
        "nombre": "Juan",
        "apellido": "Pérez",
        "correo": "juan.perez@email.com",
        "telefono": "70123456",
        "password": "password123",
        "password_confirmacion": "password123",
        "tipo_usuario": "Paciente",
        "sexo": "Masculino",  // opcional
        "carnet": "12345678",  // opcional, recomendado para pacientes
        "fecha_nacimiento": "1990-01-15",  // opcional, recomendado para pacientes
        "direccion": "Av. Principal #123"  // opcional, recomendado para pacientes
    }
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        from apps.usuarios.models import Usuario, Tipodeusuario, Paciente
        from apps.usuarios.serializers import UsuarioDetalleSerializer
        from django.db import transaction
        
        serializer = RegistroSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        
        try:
            with transaction.atomic():
                # 1. Crear usuario de Django (para autenticación)
                django_user = User.objects.create_user(
                    username=data['correo'],
                    email=data['correo'],
                    password=data['password'],
                    first_name=data['nombre'],
                    last_name=data['apellido']
                )
                
                # 2. Obtener tipo de usuario
                tipo_usuario = Tipodeusuario.objects.get(rol__iexact=data['tipo_usuario'])
                
                # 3. Crear usuario personalizado
                usuario = Usuario.objects.create(
                    nombre=data['nombre'],
                    apellido=data['apellido'],
                    correoelectronico=data['correo'],
                    telefono=data['telefono'],
                    sexo=data.get('sexo', ''),
                    idtipousuario=tipo_usuario,
                    recibir_notificaciones=True,
                    notificaciones_email=True,
                    notificaciones_push=False
                )
                
                # 4. Si es paciente, crear registro adicional
                if data['tipo_usuario'].lower() == 'paciente':
                    Paciente.objects.create(
                        codusuario=usuario,
                        carnetidentidad=data.get('carnet', ''),
                        fechanacimiento=data.get('fecha_nacimiento'),
                        direccion=data.get('direccion', '')
                    )
                
                # 5. Generar token de autenticación
                token = Token.objects.create(user=django_user)
                
                # 6. Registrar en auditoría (si está habilitado)
                try:
                    from apps.auditoria.models import Auditoria
                    Auditoria.objects.create(
                        accion='REGISTRO',
                        tabla='usuario',
                        detalle=f'Nuevo usuario registrado: {usuario.correoelectronico}',
                        ip_address=request.META.get('REMOTE_ADDR', ''),
                        usuario_agente=request.META.get('HTTP_USER_AGENT', '')
                    )
                except:
                    pass  # Si no existe el modelo de auditoría, continuar
                
                return Response({
                    'mensaje': 'Usuario registrado exitosamente',
                    'usuario': UsuarioDetalleSerializer(usuario).data,
                    'token': token.key
                }, status=status.HTTP_201_CREATED)
                
        except Tipodeusuario.DoesNotExist:
            return Response({
                'error': f"Tipo de usuario '{data['tipo_usuario']}' no encontrado en la base de datos."
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Si algo falla, la transacción se revierte automáticamente
            return Response({
                'error': f'Error al registrar usuario: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

