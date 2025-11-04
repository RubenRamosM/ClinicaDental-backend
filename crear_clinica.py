"""
Script para crear nuevas clínicas (tenants)

Uso:
    python crear_clinica.py <subdominio> <nombre> <ruc> <admin_email>

Ejemplo:
    python crear_clinica.py clinica1 "Clínica Dental Sonrisas" 20123456789 admin@clinica1.com
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.comun.models_tenant import Clinica, Dominio


def crear_clinica(subdominio, nombre, ruc, admin_email, plan='profesional'):
    """
    Crea una nueva clínica con su subdominio
    
    Args:
        subdominio: ej. 'clinica1' (se convertirá en clinica1.localhost:8001)
        nombre: ej. 'Clínica Dental Sonrisas'
        ruc: ej. '20123456789'
        admin_email: ej. 'admin@clinica1.com'
        plan: ej. 'basico', 'profesional', 'empresarial'
    """
    
    # Validar que el subdominio no exista
    if Clinica.objects.filter(schema_name=subdominio).exists():
        print(f"❌ ERROR: El subdominio '{subdominio}' ya existe")
        return False
    
    # Validar que el dominio no exista
    dominio_local = f'{subdominio}.localhost'
    if Dominio.objects.filter(domain=dominio_local).exists():
        print(f"❌ ERROR: El dominio '{dominio_local}' ya existe")
        return False
    
    print(f"🔧 Creando clínica '{nombre}'...")
    print(f"   Subdominio: {subdominio}")
    print(f"   RUC: {ruc}")
    print(f"   Plan: {plan}")
    print("")
    
    # Crear tenant (esto crea automáticamente el esquema en PostgreSQL)
    try:
        clinica = Clinica.objects.create(
            schema_name=subdominio,  # ← Nombre del esquema en BD
            nombre=nombre,
            ruc=ruc,
            direccion='Por definir',
            telefono='000-000-0000',
            admin_nombre='Administrador',
            admin_email=admin_email,
            plan=plan,
            activa=True,
            max_usuarios=20 if plan == 'basico' else 50 if plan == 'profesional' else 1000,
            max_pacientes=100 if plan == 'basico' else 500 if plan == 'profesional' else 10000
        )
        
        print(f"✅ Clínica creada en base de datos")
        print(f"   ID: {clinica.id}")
        print(f"   Schema PostgreSQL: {subdominio}")
        print("")
        
    except Exception as e:
        print(f"❌ ERROR al crear clínica: {e}")
        return False
    
    # Crear dominio para LOCALHOST (desarrollo)
    try:
        dominio = Dominio.objects.create(
            domain=dominio_local,
            tenant=clinica,
            is_primary=True
        )
        
        print(f"✅ Dominio creado:")
        print(f"   URL desarrollo: http://{dominio_local}:8001")
        print("")
        
    except Exception as e:
        print(f"❌ ERROR al crear dominio: {e}")
        # Revertir creación de clínica
        clinica.delete()
        return False
    
    print("=" * 60)
    print("✅ ¡CLÍNICA CREADA EXITOSAMENTE!")
    print("=" * 60)
    print(f"Nombre:     {nombre}")
    print(f"RUC:        {ruc}")
    print(f"Plan:       {plan}")
    print(f"Admin:      {admin_email}")
    print(f"Schema BD:  {subdominio}")
    print("")
    print("🌐 ACCESO EN DESARROLLO:")
    print(f"   http://{dominio_local}:8001")
    print("")
    print("📝 SIGUIENTE PASO:")
    print("   1. Iniciar el servidor: python manage.py runserver 8001")
    print(f"   2. Acceder en el navegador a: http://{dominio_local}:8001")
    print("")
    print("💡 TIP: Para acceder desde subdominios en localhost:")
    print("   Agregar a C:\\Windows\\System32\\drivers\\etc\\hosts:")
    print(f"   127.0.0.1  {dominio_local}")
    print("")
    
    return True


if __name__ == '__main__':
    if len(sys.argv) < 5:
        print("=" * 60)
        print("CREAR NUEVA CLÍNICA (TENANT)")
        print("=" * 60)
        print("")
        print("Uso:")
        print("  python crear_clinica.py <subdominio> <nombre> <ruc> <admin_email> [plan]")
        print("")
        print("Parámetros:")
        print("  subdominio    - Identificador único (ej: clinica1, dental_norte, etc.)")
        print("  nombre        - Nombre completo (usar comillas si tiene espacios)")
        print("  ruc           - RUC/NIT de la clínica")
        print("  admin_email   - Email del administrador")
        print("  plan          - Opcional: basico, profesional, empresarial (default: profesional)")
        print("")
        print("Ejemplos:")
        print('  python crear_clinica.py clinica1 "Clínica Dental Sonrisas" 20123456789 admin@clinica1.com')
        print('  python crear_clinica.py norte "Dental Norte" 20987654321 admin@norte.com profesional')
        print('  python crear_clinica.py sur "Clínica del Sur" 20555666777 admin@sur.com empresarial')
        print("")
        sys.exit(1)
    
    subdominio = sys.argv[1]
    nombre = sys.argv[2]
    ruc = sys.argv[3]
    admin_email = sys.argv[4]
    plan = sys.argv[5] if len(sys.argv) > 5 else 'profesional'
    
    # Validar plan
    if plan not in ['basico', 'profesional', 'empresarial']:
        print(f"❌ ERROR: Plan '{plan}' no válido. Use: basico, profesional o empresarial")
        sys.exit(1)
    
    crear_clinica(subdominio, nombre, ruc, admin_email, plan)
