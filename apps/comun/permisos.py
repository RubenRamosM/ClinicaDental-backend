"""
Sistema de permisos personalizados para la aplicación.
"""
from rest_framework import permissions


class EsSuperAdministrador(permissions.BasePermission):
    """
    Permiso: Solo superadministradores del sistema.
    """
    message = "Solo los superadministradores pueden realizar esta acción."
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_superuser


class EsAdministrador(permissions.BasePermission):
    """
    Permiso: Usuarios con rol de Administrador.
    """
    message = "Solo los administradores pueden realizar esta acción."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser:
            return True
        
        try:
            from apps.usuarios.models import Usuario
            usuario = Usuario.objects.select_related('idtipousuario').get(
                correoelectronico=request.user.username
            )
            return usuario.idtipousuario.rol == 'Administrador'
        except Usuario.DoesNotExist:
            return False
        except Exception:
            return False


class EsOdontologo(permissions.BasePermission):
    """
    Permiso: Usuarios con rol de Odontólogo.
    """
    message = "Solo los odontólogos pueden realizar esta acción."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        try:
            # El request.user es el Django User, debemos buscar en Usuario por correoelectronico
            from apps.usuarios.models import Usuario
            usuario = Usuario.objects.select_related('idtipousuario').get(
                correoelectronico=request.user.username
            )
            return usuario.idtipousuario.rol == 'Odontólogo'
        except Usuario.DoesNotExist:
            return False
        except Exception:
            return False


class EsRecepcionista(permissions.BasePermission):
    """
    Permiso: Usuarios con rol de Recepcionista.
    """
    message = "Solo los recepcionistas pueden realizar esta acción."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        try:
            from apps.usuarios.models import Usuario
            usuario = Usuario.objects.select_related('idtipousuario').get(
                correoelectronico=request.user.username
            )
            return usuario.idtipousuario.rol == 'Recepcionista'
        except Usuario.DoesNotExist:
            return False
        except Exception:
            return False


class EsStaff(permissions.BasePermission):
    """
    Permiso: Usuarios staff (Administrador, Odontólogo o Recepcionista).
    """
    message = "Solo el personal de la clínica puede realizar esta acción."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser:
            return True
        
        try:
            from apps.usuarios.models import Usuario
            usuario = Usuario.objects.select_related('idtipousuario').get(
                correoelectronico=request.user.username
            )
            rol = usuario.idtipousuario.rol
            return rol in ['Administrador', 'Odontólogo', 'Recepcionista']
        except Usuario.DoesNotExist:
            return False
        except Exception:
            return False


class EsPaciente(permissions.BasePermission):
    """
    Permiso: Usuarios con rol de Paciente.
    """
    message = "Esta acción es solo para pacientes."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        try:
            from apps.usuarios.models import Usuario
            usuario = Usuario.objects.select_related('idtipousuario').get(
                correoelectronico=request.user.username
            )
            return usuario.idtipousuario.rol == 'Paciente'
        except Usuario.DoesNotExist:
            return False
        except Exception:
            return False


class EsPropietarioOSoloLectura(permissions.BasePermission):
    """
    Permiso: Solo el propietario puede editar, otros solo pueden leer.
    """
    
    def has_object_permission(self, request, view, obj):
        # Permitir GET, HEAD, OPTIONS (lectura)
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Verificar propiedad según el tipo de objeto
        if hasattr(obj, 'usuario'):
            return obj.usuario == request.user
        
        if hasattr(obj, 'codpaciente'):
            try:
                return obj.codpaciente.codusuario == request.user
            except:
                return False
        
        if hasattr(obj, 'codusuario'):
            return obj.codusuario == request.user
        
        return False


class EsPropietarioOStaff(permissions.BasePermission):
    """
    Permiso: El propietario del objeto o cualquier staff puede acceder.
    """
    
    def has_object_permission(self, request, view, obj):
        # Staff siempre tiene acceso
        if request.user.is_superuser:
            return True
        
        try:
            from apps.usuarios.models import Usuario
            usuario = Usuario.objects.select_related('idtipousuario').get(
                correoelectronico=request.user.username
            )
            rol = usuario.idtipousuario.rol
            if rol in ['Administrador', 'Odontólogo', 'Recepcionista']:
                return True
        except (Usuario.DoesNotExist, Exception):
            pass
        
        # Verificar propiedad
        if hasattr(obj, 'usuario'):
            return obj.usuario == request.user
        
        if hasattr(obj, 'codpaciente'):
            try:
                return obj.codpaciente.codusuario == request.user
            except:
                return False
        
        if hasattr(obj, 'codusuario'):
            return obj.codusuario == request.user
        
        return False


# TODO (Multi-clínica): Descomentar cuando se implemente multi-tenancy
# class EsMismaClinica(permissions.BasePermission):
#     """
#     Permiso: Usuario pertenece a la misma clínica que el objeto.
#     """
#     message = "No tienes acceso a los datos de otra clínica."
#     
#     def has_object_permission(self, request, view, obj):
#         if not hasattr(request, 'tenant') or not hasattr(obj, 'clinica'):
#             return True  # Sin multi-tenancy, permitir
#         
#         return obj.clinica == request.tenant
