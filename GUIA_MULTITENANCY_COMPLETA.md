# 🏥 GUÍA COMPLETA: MULTITENANCY CON SUBDOMINIOS

## 📌 ARQUITECTURA FINAL

```
psicoadmin.xyz                    → SUPER ADMIN (gestiona todas las clínicas)
├── clinica1.psicoadmin.xyz      → Clínica Dental "Sonrisas"
├── clinica2.psicoadmin.xyz      → Clínica Dental "Dental Care"
└── clinica3.psicoadmin.xyz      → Clínica Dental "OdontoMax"
```

---

## 🎯 PASO 1: CONFIGURAR DJANGO SETTINGS

### 1.1 Actualizar `config/settings.py`

Agrega estas configuraciones:

```python
# =================================================================
# MULTITENANCY CON DJANGO-TENANTS
# =================================================================

# APPS COMPARTIDAS (público - para super admin)
SHARED_APPS = [
    'django_tenants',  # ← DEBE SER LA PRIMERA APP
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    
    # Apps compartidas entre todos los tenants
    'apps.comun',  # Contiene el modelo Clinica (Tenant)
]

# APPS DE TENANTS (cada clínica)
TENANT_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    
    # REST Framework
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'django_filters',
    
    # Apps específicas de cada clínica
    'apps.usuarios',
    'apps.profesionales',
    'apps.citas',
    'apps.administracion_clinica',
    'apps.sistema_pagos',
    'apps.auditoria',
    'apps.autenticacion',
    'apps.historial_clinico',
    'apps.tratamientos',
    'apps.respaldos',
    'apps.chatbot',
]

INSTALLED_APPS = SHARED_APPS + [app for app in TENANT_APPS if app not in SHARED_APPS]

# Modelo de Tenant
TENANT_MODEL = "comun.Clinica"
TENANT_DOMAIN_MODEL = "comun.Dominio"

# Middleware para multitenancy (DEBE SER EL PRIMERO)
MIDDLEWARE = [
    'django_tenants.middleware.main.TenantMainMiddleware',  # ← PRIMERO
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Database router para tenants
DATABASE_ROUTERS = [
    'django_tenants.routers.TenantSyncRouter',
]

# Template context processor para acceder al tenant actual
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django_tenants.context_processors.current_tenant',  # ← AGREGAR
            ],
        },
    },
]
```

---

## 🎯 PASO 2: CREAR MIGRACIONES Y ESQUEMAS

### 2.1 Crear migraciones para el modelo Tenant

```bash
python manage.py makemigrations comun
```

### 2.2 Migrar esquema público (super admin)

```bash
python manage.py migrate_schemas --shared
```

Este comando crea las tablas en el esquema `public`:
- `comun_clinica` (tenants)
- `comun_dominio` (dominios)

---

## 🎯 PASO 3: CREAR CLÍNICA PÚBLICA (SUPER ADMIN)

### 3.1 Crear script para crear tenant público

Crea `crear_tenant_publico.py`:

```python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.comun.models_tenant import Clinica, Dominio

# Crear tenant público (para super admin)
tenant_publico = Clinica.objects.create(
    schema_name='public',
    nombre='PSICOADMIN - Super Administración',
    ruc='0000000000',
    admin_nombre='Super Administrador',
    admin_email='admin@psicoadmin.xyz',
    plan='empresarial',
    activa=True
)

# Crear dominio principal
Dominio.objects.create(
    domain='psicoadmin.xyz',  # Dominio principal
    tenant=tenant_publico,
    is_primary=True
)

print("✅ Tenant público creado exitosamente")
print(f"   Dominio: psicoadmin.xyz")
print(f"   Schema: public")
```

### 3.2 Ejecutar script

```bash
python crear_tenant_publico.py
```

---

## 🎯 PASO 4: CREAR CLÍNICAS (TENANTS)

### 4.1 Crear script para crear clínicas

Crea `crear_clinica.py`:

```python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.comun.models_tenant import Clinica, Dominio

def crear_clinica(subdominio, nombre, ruc, admin_email):
    """
    Crea una nueva clínica con su subdominio
    
    Args:
        subdominio: ej. 'clinica1' (se convertirá en clinica1.psicoadmin.xyz)
        nombre: ej. 'Clínica Dental Sonrisas'
        ruc: ej. '20123456789'
        admin_email: ej. 'admin@clinica1.com'
    """
    
    # Crear tenant (esto crea automáticamente el esquema en PostgreSQL)
    clinica = Clinica.objects.create(
        schema_name=subdominio,  # ← Nombre del esquema en BD
        nombre=nombre,
        ruc=ruc,
        admin_nombre='Administrador',
        admin_email=admin_email,
        plan='profesional',
        activa=True,
        max_usuarios=20,
        max_pacientes=500
    )
    
    # Crear dominio
    Dominio.objects.create(
        domain=f'{subdominio}.psicoadmin.xyz',
        tenant=clinica,
        is_primary=True
    )
    
    print(f"✅ Clínica creada exitosamente:")
    print(f"   Nombre: {nombre}")
    print(f"   Dominio: {subdominio}.psicoadmin.xyz")
    print(f"   Schema BD: {subdominio}")
    print(f"   Admin: {admin_email}")


if __name__ == '__main__':
    if len(sys.argv) < 5:
        print("Uso: python crear_clinica.py <subdominio> <nombre> <ruc> <admin_email>")
        print('Ejemplo: python crear_clinica.py clinica1 "Dental Sonrisas" 20123456789 admin@clinica1.com')
        sys.exit(1)
    
    crear_clinica(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
```

### 4.2 Crear primera clínica

```bash
python crear_clinica.py clinica1 "Clínica Dental Sonrisas" 20123456789 admin@clinica1.com
```

Esto:
1. Crea el esquema `clinica1` en PostgreSQL
2. Ejecuta TODAS las migraciones en ese esquema
3. Crea el subdominio `clinica1.psicoadmin.xyz`

---

## 🎯 PASO 5: CONFIGURAR NAMECHEAP DNS

Ve a: https://ap.www.namecheap.com/domains/domaincontrolpanel/psicoadmin.xyz/advancedns

### 5.1 Agregar registros A

| Type | Host | Value | TTL |
|------|------|-------|-----|
| A Record | @ | `IP_DE_RENDER` | Automatic |
| A Record | * | `IP_DE_RENDER` | Automatic |

El `*` (wildcard) permite que TODOS los subdominios apunten a Render.

### 5.2 Obtener IP de Render

1. Ve a tu servicio en Render: https://dashboard.render.com
2. Click en tu servicio backend
3. Copia la URL (ej: `clinic-backend-abc123.onrender.com`)
4. Ejecuta en terminal: `nslookup clinic-backend-abc123.onrender.com`
5. Copia la IP

**IMPORTANTE**: Si Render usa balanceador de carga, usa registro CNAME en lugar de A:

| Type | Host | Value | TTL |
|------|------|-------|-----|
| CNAME Record | @ | `clinic-backend-abc123.onrender.com.` | Automatic |
| CNAME Record | * | `clinic-backend-abc123.onrender.com.` | Automatic |

---

## 🎯 PASO 6: CONFIGURAR RENDER

### 6.1 Ir a Render Dashboard

https://dashboard.render.com

### 6.2 Configurar Custom Domains

1. Click en tu servicio backend
2. Ve a **Settings** → **Custom Domains**
3. Agrega estos dominios:
   - `psicoadmin.xyz`
   - `*.psicoadmin.xyz` (wildcard para subdominios)

### 6.3 Configurar Variables de Entorno

En **Environment Variables**:

```
DJANGO_SETTINGS_MODULE=config.settings
ALLOWED_HOSTS=psicoadmin.xyz,*.psicoadmin.xyz
CORS_ALLOWED_ORIGINS=https://psicoadmin.xyz,https://*.psicoadmin.xyz
DEBUG=False
DATABASE_URL=postgresql://...
SECRET_KEY=...
```

### 6.4 Configurar SSL/HTTPS

Render automáticamente genera certificados SSL para:
- `psicoadmin.xyz`
- `*.psicoadmin.xyz` (wildcard SSL)

---

## 🎯 PASO 7: DESPLEGAR EN RENDER

### 7.1 Actualizar `render.yaml`

Crea o actualiza `render.yaml`:

```yaml
services:
  - type: web
    name: psicoadmin-backend
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.11
      - key: DJANGO_SETTINGS_MODULE
        value: config.settings
      - key: ALLOWED_HOSTS
        value: psicoadmin.xyz,*.psicoadmin.xyz
    domains:
      - psicoadmin.xyz
      - "*.psicoadmin.xyz"
```

### 7.2 Hacer commit y push

```bash
git add .
git commit -m "Configurar multitenancy con subdominios"
git push origin main
```

Render automáticamente desplegará.

---

## 🎯 PASO 8: PROBAR MULTITENANCY

### 8.1 Acceder al Super Admin

```
https://psicoadmin.xyz
```

Muestra el panel de super administración.

### 8.2 Acceder a Clínica 1

```
https://clinica1.psicoadmin.xyz
```

Muestra el dashboard de la Clínica 1 con sus propios datos.

### 8.3 Verificar aislamiento de datos

```python
# En clinica1.psicoadmin.xyz
from apps.usuarios.models import Usuario
Usuario.objects.all()  # Solo usuarios de clínica1

# En clinica2.psicoadmin.xyz
from apps.usuarios.models import Usuario
Usuario.objects.all()  # Solo usuarios de clínica2
```

---

## 🎯 PASO 9: CREAR ENDPOINT PARA GESTIONAR CLÍNICAS

### 9.1 Crear API para crear clínicas

Crea `apps/comun/views_tenant.py`:

```python
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models_tenant import Clinica, Dominio
from .serializers_tenant import ClinicaSerializer


class ClinicaViewSet(viewsets.ModelViewSet):
    """
    API para gestionar clínicas (solo super admin)
    
    Endpoints:
    - GET /api/v1/clinicas/ - Listar todas las clínicas
    - POST /api/v1/clinicas/ - Crear nueva clínica
    - GET /api/v1/clinicas/{id}/ - Ver clínica
    - PUT /api/v1/clinicas/{id}/ - Actualizar clínica
    - DELETE /api/v1/clinicas/{id}/ - Desactivar clínica
    """
    queryset = Clinica.objects.all().exclude(schema_name='public')
    serializer_class = ClinicaSerializer
    permission_classes = [IsAuthenticated]
    
    def create(self, request):
        """
        Crear nueva clínica con subdominio
        
        Body:
        {
            "subdominio": "clinica1",
            "nombre": "Clínica Dental Sonrisas",
            "ruc": "20123456789",
            "admin_email": "admin@clinica1.com",
            "plan": "profesional"
        }
        """
        subdominio = request.data.get('subdominio')
        
        # Validar que el subdominio no exista
        if Clinica.objects.filter(schema_name=subdominio).exists():
            return Response(
                {'error': 'El subdominio ya existe'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Crear clínica
        clinica = Clinica.objects.create(
            schema_name=subdominio,
            nombre=request.data.get('nombre'),
            ruc=request.data.get('ruc'),
            admin_nombre=request.data.get('admin_nombre', 'Administrador'),
            admin_email=request.data.get('admin_email'),
            plan=request.data.get('plan', 'basico')
        )
        
        # Crear dominio
        Dominio.objects.create(
            domain=f'{subdominio}.psicoadmin.xyz',
            tenant=clinica,
            is_primary=True
        )
        
        serializer = self.get_serializer(clinica)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
```

---

## 📊 RESUMEN DE URLs

```
SUPER ADMIN:
https://psicoadmin.xyz/                    → Panel super admin
https://psicoadmin.xyz/admin/              → Django admin
https://psicoadmin.xyz/api/v1/clinicas/    → API gestionar clínicas

CLÍNICA 1:
https://clinica1.psicoadmin.xyz/           → Dashboard clínica
https://clinica1.psicoadmin.xyz/admin/     → Admin clínica
https://clinica1.psicoadmin.xyz/api/v1/    → API clínica

CLÍNICA 2:
https://clinica2.psicoadmin.xyz/           → Dashboard clínica
https://clinica2.psicoadmin.xyz/api/v1/    → API clínica
```

---

## ✅ CHECKLIST FINAL

- [ ] django-tenants instalado
- [ ] Modelo Clinica y Dominio creados
- [ ] settings.py actualizado (SHARED_APPS, TENANT_APPS, middleware)
- [ ] Migraciones ejecutadas en schema público
- [ ] Tenant público creado
- [ ] Primera clínica creada
- [ ] DNS configurado en Namecheap (A o CNAME con wildcard)
- [ ] Custom domains agregados en Render
- [ ] Variables de entorno configuradas
- [ ] Código desplegado en Render
- [ ] SSL activo para psicoadmin.xyz y *.psicoadmin.xyz
- [ ] Multitenancy funcionando

---

¿Por dónde quieres empezar? Te guío paso a paso 🚀
