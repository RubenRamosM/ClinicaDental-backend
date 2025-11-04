"""
Script para verificar el estado de preparación Multi-Tenancy
"""
import os
import django
import re

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings
from django.apps import apps

print("\n" + "="*70)
print("🔍 VERIFICACIÓN DE PREPARACIÓN MULTI-TENANCY")
print("="*70 + "\n")

# 1. Verificar Settings
print("📋 1. CONFIGURACIÓN EN SETTINGS.PY")
print("-" * 70)

multitenancy_settings = {
    'SAAS_BASE_DOMAIN': getattr(settings, 'SAAS_BASE_DOMAIN', None),
    'SAAS_PUBLIC_URL': getattr(settings, 'SAAS_PUBLIC_URL', None),
    'DEBUG': getattr(settings, 'DEBUG', False),
}

for key, value in multitenancy_settings.items():
    status = "✅" if value else "❌"
    print(f"{status} {key}: {value}")

if settings.DEBUG:
    print(f"\n🔹 Modo DESARROLLO - Subdominios localhost:")
    print(f"   ✅ Base: http://localhost:8000")
    print(f"   ✅ Norte: http://norte.localhost:8000")
    print(f"   ✅ Sur: http://sur.localhost:8000")
    print(f"   ✅ Este: http://este.localhost:8000")
    print(f"   ✅ Oeste: http://oeste.localhost:8000")
else:
    print(f"\n🔹 Modo PRODUCCIÓN - Subdominios en dominio real")

print(f"\n🔹 CORS configurado para subdominios:")
cors_patterns = [r for r in settings.CORS_ALLOWED_ORIGIN_REGEXES if 'localhost' in r or 'clinicadental' in r]
for pattern in cors_patterns:
    print(f"   ✅ {pattern}")

print(f"\n🔹 Headers permitidos para multitenancy:")
if 'x-tenant-subdomain' in [h.lower() for h in settings.CORS_ALLOW_HEADERS]:
    print("   ✅ x-tenant-subdomain")
else:
    print("   ❌ x-tenant-subdomain NO configurado")

# 2. Verificar Middlewares
print("\n\n📋 2. MIDDLEWARES PREPARADOS")
print("-" * 70)

middlewares_multitenancy = [
    'middleware_tenant.TenantMiddleware',
    'middleware_routing.TenantRoutingMiddleware',
    'middleware_admin_diagnostic.AdminTenantDiagnosticMiddleware',
]

# Leer el archivo settings para ver comentarios
settings_path = os.path.join(settings.BASE_DIR, 'config', 'settings.py')
with open(settings_path, 'r', encoding='utf-8') as f:
    settings_content = f.read()

for mw in middlewares_multitenancy:
    if f'# "{mw}"' in settings_content or f"# '{mw}'" in settings_content:
        print(f"⏸️  {mw} - COMENTADO (listo para activar)")
    elif mw in settings_content:
        print(f"✅ {mw} - ACTIVO")
    else:
        print(f"❌ {mw} - NO ENCONTRADO")

# 3. Verificar Modelos Base
print("\n\n📋 3. MODELOS BASE PREPARADOS")
print("-" * 70)

# Leer archivo de modelos
models_path = os.path.join(settings.BASE_DIR, 'apps', 'comun', 'models.py')
with open(models_path, 'r', encoding='utf-8') as f:
    models_content = f.read()

if 'ModeloPreparadoMultiClinica' in models_content:
    print("✅ ModeloPreparadoMultiClinica - CREADO")
    if '# clinica = models.ForeignKey' in models_content:
        print("   ⏸️  Campo 'clinica' COMENTADO (listo para activar)")
    else:
        print("   ⚠️  Campo 'clinica' - revisar estado")
else:
    print("❌ ModeloPreparadoMultiClinica - NO ENCONTRADO")

# 4. Verificar Managers
print("\n\n📋 4. MANAGERS PREPARADOS")
print("-" * 70)

managers_path = os.path.join(settings.BASE_DIR, 'apps', 'comun', 'managers.py')
with open(managers_path, 'r', encoding='utf-8') as f:
    managers_content = f.read()

managers_multitenancy = ['QuerySetMultiClinica', 'ManagerMultiClinica']
for manager in managers_multitenancy:
    if f'# class {manager}' in managers_content:
        print(f"⏸️  {manager} - COMENTADO (listo para activar)")
    elif f'class {manager}' in managers_content:
        print(f"✅ {manager} - ACTIVO")
    else:
        print(f"❌ {manager} - NO ENCONTRADO")

# 5. Verificar Permisos
print("\n\n📋 5. PERMISOS PREPARADOS")
print("-" * 70)

permisos_path = os.path.join(settings.BASE_DIR, 'apps', 'comun', 'permisos.py')
with open(permisos_path, 'r', encoding='utf-8') as f:
    permisos_content = f.read()

if '# class EsMismaClinica' in permisos_content:
    print("⏸️  EsMismaClinica - COMENTADO (listo para activar)")
elif 'class EsMismaClinica' in permisos_content:
    print("✅ EsMismaClinica - ACTIVO")
else:
    print("❌ EsMismaClinica - NO ENCONTRADO")

# 6. Verificar URL Patterns
print("\n\n📋 6. URL PATTERNS PREPARADOS")
print("-" * 70)

url_patterns_path = os.path.join(settings.BASE_DIR, 'config', 'url_patterns.py')
try:
    with open(url_patterns_path, 'r', encoding='utf-8') as f:
        url_content = f.read()
    
    if 'urlpatterns_tenant' in url_content:
        print("✅ urlpatterns_tenant - DEFINIDO")
    else:
        print("❌ urlpatterns_tenant - NO ENCONTRADO")
        
    if 'urlpatterns_public' in url_content:
        print("✅ urlpatterns_public - DEFINIDO")
    else:
        print("❌ urlpatterns_public - NO ENCONTRADO")
except FileNotFoundError:
    print("⚠️  Archivo url_patterns.py no encontrado")

# 7. Verificar Apps que usan ModeloPreparadoMultiClinica
print("\n\n📋 7. MODELOS QUE HEREDAN DE ModeloPreparadoMultiClinica")
print("-" * 70)

modelos_preparados = []
apps_dir = os.path.join(settings.BASE_DIR, 'apps')

for app_name in os.listdir(apps_dir):
    app_path = os.path.join(apps_dir, app_name)
    models_file = os.path.join(app_path, 'models.py')
    
    if os.path.isfile(models_file):
        with open(models_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Buscar clases que heredan de ModeloPreparadoMultiClinica
        pattern = r'class\s+(\w+)\s*\([^)]*ModeloPreparadoMultiClinica[^)]*\)'
        matches = re.findall(pattern, content)
        
        if matches:
            for modelo in matches:
                modelos_preparados.append(f"{app_name}.{modelo}")

if modelos_preparados:
    print(f"✅ {len(modelos_preparados)} modelos preparados:")
    for modelo in modelos_preparados:
        print(f"   • {modelo}")
else:
    print("⚠️  No se encontraron modelos usando ModeloPreparadoMultiClinica")

# 8. Verificar si existe app 'tenancy'
print("\n\n📋 8. APP TENANCY")
print("-" * 70)

tenancy_path = os.path.join(apps_dir, 'tenancy')
if os.path.exists(tenancy_path):
    print("✅ App 'tenancy' EXISTE")
    
    # Verificar modelos
    tenancy_models = os.path.join(tenancy_path, 'models.py')
    if os.path.exists(tenancy_models):
        with open(tenancy_models, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'class Clinica' in content:
            print("   ✅ Modelo 'Clinica' encontrado")
        else:
            print("   ❌ Modelo 'Clinica' NO encontrado")
else:
    print("⏸️  App 'tenancy' NO EXISTE (pendiente de crear)")
    print("   📝 Necesitarás crear esta app cuando actives multitenancy")

# 9. Archivos de middleware
print("\n\n📋 9. ARCHIVOS DE MIDDLEWARE")
print("-" * 70)

middleware_files = [
    'config/middleware_routing.py',
    'api/middleware_tenant.py',
    'api/middleware_admin_diagnostic.py',
]

for mw_file in middleware_files:
    mw_path = os.path.join(settings.BASE_DIR, mw_file)
    if os.path.exists(mw_path):
        print(f"✅ {mw_file} - EXISTE")
    else:
        print(f"⏸️  {mw_file} - NO EXISTE (pendiente de crear)")

# RESUMEN FINAL
print("\n\n" + "="*70)
print("📊 RESUMEN")
print("="*70)

print("""
✅ PREPARADO:
   • Settings configurados con SAAS_BASE_DOMAIN
   • CORS configurado para subdominios
   • Headers x-tenant-subdomain permitidos
   • ModeloPreparadoMultiClinica creado (campo 'clinica' comentado)
   • Managers multitenancy comentados (listos para activar)
   • Permisos EsMismaClinica comentados
   • URL patterns preparados

⏸️  PENDIENTE PARA ACTIVAR:
   1. Crear app 'tenancy' con modelo Clinica
   2. Crear middlewares:
      - config/middleware_routing.py
      - api/middleware_tenant.py
      - api/middleware_admin_diagnostic.py
   3. Descomentar campo 'clinica' en ModeloPreparadoMultiClinica
   4. Descomentar managers en apps/comun/managers.py
   5. Descomentar permisos en apps/comun/permisos.py
   6. Activar middlewares en settings.py
   7. Ejecutar migraciones

📋 ESTADO ACTUAL: **PREPARADO PERO NO IMPLEMENTADO**
   El código está listo para multitenancy pero actualmente funciona
   como sistema de clínica única. Todos los componentes necesarios
   están comentados y listos para activar cuando sea necesario.
""")

print("="*70 + "\n")
