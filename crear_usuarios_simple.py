"""
Script simple para crear usuarios en clinica1
Ejecutar en Render Shell: python crear_usuarios_simple.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from apps.comun.models import Clinica
from apps.usuarios.models import Usuario, Tipodeusuario
from apps.profesionales.models import Odontologo
from django.db import connection

def crear_usuarios():
    print("\n" + "="*70)
    print("  🚀 CREANDO USUARIOS PARA CLINICA1")
    print("="*70)
    
    # Obtener clinica1
    try:
        clinica = Clinica.objects.get(schema_name='clinica1')
        print(f"\n✓ Clínica encontrada: {clinica.nombre}")
    except Clinica.DoesNotExist:
        print("\n❌ ERROR: No existe el tenant clinica1")
        return
    
    # Cambiar al schema de clinica1
    connection.set_tenant(clinica)
    print(f"✓ Conectado al schema: {clinica.schema_name}\n")
    
    # Obtener o crear tipos de usuario
    tipo_admin, _ = Tipodeusuario.objects.get_or_create(
        id=1,
        defaults={'rol': 'Administrador', 'descripcion': 'Administrador del sistema'}
    )
    tipo_odontologo, _ = Tipodeusuario.objects.get_or_create(
        id=2,
        defaults={'rol': 'Odontólogo', 'descripcion': 'Profesional odontólogo'}
    )
    tipo_paciente, _ = Tipodeusuario.objects.get_or_create(
        id=4,
        defaults={'rol': 'Paciente', 'descripcion': 'Paciente de la clínica'}
    )
    
    usuarios_creados = []
    
    # ==================== ADMINISTRADOR ====================
    print("👤 Creando Administrador...")
    admin_django, created = User.objects.get_or_create(
        username='admin@clinica1.com',
        defaults={
            'email': 'admin@clinica1.com',
            'is_staff': True,
            'is_superuser': True
        }
    )
    if created or not admin_django.has_usable_password():
        admin_django.set_password('admin123')
        admin_django.save()
        print("  ✓ Usuario Django creado/actualizado")
    
    admin_usuario, created = Usuario.objects.get_or_create(
        correoelectronico='admin@clinica1.com',
        defaults={
            'nombre': 'Admin',
            'apellido': 'Sistema',
            'sexo': 'M',
            'telefono': '70000000',
            'idtipousuario': tipo_admin
        }
    )
    Token.objects.get_or_create(user=admin_django)
    usuarios_creados.append({
        'email': 'admin@clinica1.com',
        'password': 'admin123',
        'rol': 'Administrador'
    })
    print("  ✓ Administrador listo\n")
    
    # ==================== ODONTÓLOGO ====================
    print("👨‍⚕️ Creando Odontólogo...")
    odon_django, created = User.objects.get_or_create(
        username='dr.perez@clinica1.com',
        defaults={'email': 'dr.perez@clinica1.com'}
    )
    if created or not odon_django.has_usable_password():
        odon_django.set_password('odontologo123')
        odon_django.save()
        print("  ✓ Usuario Django creado/actualizado")
    
    odon_usuario, created = Usuario.objects.get_or_create(
        correoelectronico='dr.perez@clinica1.com',
        defaults={
            'nombre': 'Juan Carlos',
            'apellido': 'Pérez López',
            'sexo': 'M',
            'telefono': '70000001',
            'idtipousuario': tipo_odontologo
        }
    )
    
    odontologo, created = Odontologo.objects.get_or_create(
        codusuario=odon_usuario,
        defaults={
            'especialidad': 'Ortodoncia',
            'nromatricula': 'ODO-001',
            'experienciaprofesional': '10 años en ortodoncia'
        }
    )
    Token.objects.get_or_create(user=odon_django)
    usuarios_creados.append({
        'email': 'dr.perez@clinica1.com',
        'password': 'odontologo123',
        'rol': 'Odontólogo'
    })
    print("  ✓ Odontólogo listo\n")
    
    # ==================== PACIENTE ====================
    print("🧑 Creando Paciente...")
    pac_django, created = User.objects.get_or_create(
        username='ana.lopez@email.com',
        defaults={'email': 'ana.lopez@email.com'}
    )
    if created or not pac_django.has_usable_password():
        pac_django.set_password('paciente123')
        pac_django.save()
        print("  ✓ Usuario Django creado/actualizado")
    
    pac_usuario, created = Usuario.objects.get_or_create(
        correoelectronico='ana.lopez@email.com',
        defaults={
            'nombre': 'Ana María',
            'apellido': 'López García',
            'sexo': 'F',
            'telefono': '70000020',
            'idtipousuario': tipo_paciente
        }
    )
    Token.objects.get_or_create(user=pac_django)
    usuarios_creados.append({
        'email': 'ana.lopez@email.com',
        'password': 'paciente123',
        'rol': 'Paciente'
    })
    print("  ✓ Paciente listo\n")
    
    # ==================== RESUMEN ====================
    print("\n" + "="*70)
    print("  ✅ USUARIOS CREADOS EXITOSAMENTE")
    print("="*70)
    print("\n📋 Credenciales para login:\n")
    for u in usuarios_creados:
        print(f"  {u['rol']:15} → {u['email']:30} / {u['password']}")
    
    print("\n" + "="*70)
    print("  🌐 Prueba el login en: https://clinica1.dentaabcxy.store")
    print("="*70 + "\n")

if __name__ == '__main__':
    try:
        crear_usuarios()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
