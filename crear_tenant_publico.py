"""
Script para crear el tenant público (super admin)
Este debe ejecutarse DESPUÉS de migrate_schemas --shared
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.comun.models_tenant import Clinica, Dominio

def crear_tenant_publico():
    """Crea el tenant público para super administración"""
    
    # Verificar si ya existe
    if Clinica.objects.filter(schema_name='public').exists():
        print("⚠️  El tenant público ya existe")
        tenant_publico = Clinica.objects.get(schema_name='public')
        print(f"   Nombre: {tenant_publico.nombre}")
        print(f"   Schema: {tenant_publico.schema_name}")
        return
    
    # Crear tenant público (para super admin)
    tenant_publico = Clinica.objects.create(
        schema_name='public',
        nombre='PSICOADMIN - Super Administración',
        ruc='0000000000',
        direccion='Oficina Central',
        telefono='000-000-0000',
        admin_nombre='Super Administrador',
        admin_email='admin@psicoadmin.xyz',
        plan='empresarial',
        activa=True,
        max_usuarios=1000,
        max_pacientes=100000
    )
    
    # Crear dominio principal - LOCALHOST
    Dominio.objects.create(
        domain='localhost',  # Para desarrollo
        tenant=tenant_publico,
        is_primary=True
    )
    
    print("✅ Tenant público creado exitosamente")
    print(f"   Nombre: {tenant_publico.nombre}")
    print(f"   Dominio: localhost (desarrollo)")
    print(f"   Schema: public")
    print(f"   Admin: {tenant_publico.admin_email}")
    print("")
    print("📝 SIGUIENTE PASO:")
    print("   Crear clínicas con: python crear_clinica.py <subdominio> <nombre> <ruc> <email>")


if __name__ == '__main__':
    crear_tenant_publico()
