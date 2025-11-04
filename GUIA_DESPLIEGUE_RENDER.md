# 🚀 GUÍA DE DESPLIEGUE EN RENDER

## 📋 PASO 1: PREPARAR ARCHIVOS

✅ Ya creados:
- `render.yaml` - Configuración de servicios
- `build.sh` - Script de construcción

---

## 🌐 PASO 2: CONFIGURAR DOMINIO EN NAMECHEAP

### A. Accede a tu panel de Namecheap
👉 https://ap.www.namecheap.com/domains/domaincontrolpanel/psicoadmin.xyz/advancedns

### B. Configurar DNS Records

Elimina todos los registros existentes y agrega estos:

#### 1️⃣ Para el dominio principal (psicoadmin.xyz)
```
Type: A Record
Host: @
Value: 216.24.57.1
TTL: Automatic
```

#### 2️⃣ Para www (www.psicoadmin.xyz)
```
Type: CNAME Record
Host: www
Value: psicoadmin.xyz
TTL: Automatic
```

#### 3️⃣ Para subdominios de clínicas (*.psicoadmin.xyz)
```
Type: A Record
Host: *
Value: 216.24.57.1
TTL: Automatic
```

**⚠️ IMPORTANTE:** 
- `216.24.57.1` es la IP de Render para custom domains
- El wildcard `*` permite que todos los subdominios funcionen (clinica1.psicoadmin.xyz, clinica2.psicoadmin.xyz, etc.)

### C. Configuración final en Namecheap
```
NAMESERVER SETTINGS: Namecheap BasicDNS (no cambiar)
```

Tu Advanced DNS debería verse así:
```
Type        Host    Value               TTL
A Record    @       216.24.57.1         Automatic
CNAME       www     psicoadmin.xyz      Automatic
A Record    *       216.24.57.1         Automatic
```

---

## 🎨 PASO 3: CREAR CUENTA EN RENDER

### A. Registrarse
1. Ve a https://render.com
2. Haz clic en "Get Started"
3. Conecta con GitHub (recomendado)

### B. Conectar Repositorio
1. En el Dashboard, clic en "New +"
2. Selecciona "Blueprint"
3. Conecta tu repositorio de GitHub: `RubenRamosM/ClinicaDental-backend`
4. Autoriza a Render para acceder al repositorio

---

## 🗄️ PASO 4: CREAR BASE DE DATOS POSTGRESQL

### A. Desde el Dashboard de Render
1. Clic en "New +" → "PostgreSQL"
2. Configura:
   ```
   Name: clinicadental-db
   Database: clinicadental
   User: clinicadental_user
   Region: Oregon (US West)
   Plan: Free
   ```
3. Clic en "Create Database"
4. **IMPORTANTE:** Guarda la `Internal Database URL` que aparecerá

---

## 🚀 PASO 5: CREAR WEB SERVICE

### A. Desde el Dashboard de Render
1. Clic en "New +" → "Web Service"
2. Selecciona tu repositorio `ClinicaDental-backend`
3. Configura:

```
Name: clinicadental-backend
Region: Oregon (US West)
Branch: main
Runtime: Python 3
Build Command: ./build.sh
Start Command: gunicorn config.wsgi:application
Plan: Free
```

### B. Variables de Entorno (Environment Variables)

Haz clic en "Advanced" y agrega estas variables:

#### Variables Básicas
```
DEBUG=False
PYTHON_VERSION=3.13.7
DJANGO_SETTINGS_MODULE=config.settings
SECRET_KEY=(haz clic en "Generate" para crear una automática)
```

#### Base de Datos
```
DATABASE_URL=(pega la Internal Database URL que guardaste)
```

#### Dominios Permitidos
```
ALLOWED_HOSTS=.onrender.com,.psicoadmin.xyz,psicoadmin.xyz,www.psicoadmin.xyz,localhost

CORS_ALLOWED_ORIGINS=https://psicoadmin.xyz,https://www.psicoadmin.xyz,https://clinicadental-backend.onrender.com

CSRF_TRUSTED_ORIGINS=https://psicoadmin.xyz,https://www.psicoadmin.xyz,https://clinicadental-backend.onrender.com,https://*.psicoadmin.xyz
```

#### Multitenancy
```
SAAS_BASE_DOMAIN=psicoadmin.xyz
SAAS_PUBLIC_URL=https://psicoadmin.xyz
```

#### AWS S3 (para archivos estáticos)
```
AWS_ACCESS_KEY_ID=(tu access key de AWS)
AWS_SECRET_ACCESS_KEY=(tu secret key de AWS)
AWS_STORAGE_BUCKET_NAME=clinica-dental-bucket
AWS_S3_REGION_NAME=us-east-1
```

#### Stripe (opcional, si ya lo configuraste)
```
STRIPE_SECRET_KEY=(tu secret key de Stripe)
STRIPE_PUBLISHABLE_KEY=(tu publishable key de Stripe)
STRIPE_WEBHOOK_SECRET=(tu webhook secret de Stripe)
```

#### OpenAI (para chatbot)
```
OPENAI_API_KEY=(tu API key de OpenAI)
```

### C. Hacer Deploy
1. Haz clic en "Create Web Service"
2. Render comenzará a construir y desplegar automáticamente
3. Espera 5-10 minutos

---

## 🌍 PASO 6: CONFIGURAR CUSTOM DOMAIN EN RENDER

### A. Agregar dominio principal
1. Ve a tu servicio web en Render
2. Clic en "Settings" → "Custom Domains"
3. Clic en "Add Custom Domain"
4. Ingresa: `psicoadmin.xyz`
5. Clic en "Verify"
6. Repite para `www.psicoadmin.xyz`

### B. Agregar wildcard para subdominios
1. En "Custom Domains", clic en "Add Custom Domain"
2. Ingresa: `*.psicoadmin.xyz`
3. Clic en "Verify"

**⚠️ IMPORTANTE:** Render verificará que los DNS apunten correctamente. Esto puede tardar hasta 48 horas, pero normalmente es instantáneo.

---

## 🔧 PASO 7: CONFIGURAR settings.py PARA PRODUCCIÓN

Ya está configurado en tu código, pero verifica que tenga esto:

```python
# En config/settings.py

# Detectar si estamos en Render
IS_RENDER = os.environ.get('RENDER', False)

# Debug
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# Hosts permitidos
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost').split(',')

# Base de datos
if IS_RENDER or not DEBUG:
    DATABASES = {
        'default': dj_database_url.parse(os.environ.get('DATABASE_URL'))
    }

# Dominios multitenancy
SAAS_BASE_DOMAIN = os.environ.get('SAAS_BASE_DOMAIN', 'psicoadmin.xyz')
SAAS_PUBLIC_URL = os.environ.get('SAAS_PUBLIC_URL', f'https://{SAAS_BASE_DOMAIN}')
```

---

## 📦 PASO 8: COMMIT Y PUSH

```bash
git add .
git commit -m "feat: Configuración para despliegue en Render con dominio psicoadmin.xyz"
git push origin main
```

Render detectará el push y automáticamente redesplegará.

---

## ✅ PASO 9: VERIFICAR DESPLIEGUE

### A. Verificar que el servicio esté corriendo
1. Ve a tu Dashboard de Render
2. El servicio debe mostrar "Live" en verde
3. Haz clic en el servicio para ver los logs

### B. Probar endpoints
```bash
# Desde tu navegador o Postman

# Dominio de Render (temporal)
https://clinicadental-backend.onrender.com/admin/

# Tu dominio personalizado
https://psicoadmin.xyz/admin/

# Subdominios (después de crear clínicas)
https://clinica1.psicoadmin.xyz/api/v1/pacientes/
```

---

## 🏥 PASO 10: CREAR PRIMERA CLÍNICA

### A. Accede al admin de Django
```
https://psicoadmin.xyz/admin/
```

### B. O usa la API
```bash
POST https://psicoadmin.xyz/api/v1/clinicas/
{
  "schema_name": "clinica1",
  "nombre": "Clínica Dental Norte",
  "ruc": "20123456789",
  "direccion": "Av. Principal 123",
  "telefono": "987654321",
  "email": "admin@clinica1.com",
  "admin_nombre": "Juan Pérez",
  "admin_email": "juan@clinica1.com",
  "dominio": "clinica1",
  "plan": "profesional",
  "max_usuarios": 10,
  "max_pacientes": 500
}
```

La clínica estará disponible en: `https://clinica1.psicoadmin.xyz`

---

## 🔍 TROUBLESHOOTING

### Error: "Application failed to start"
**Solución:** Revisa los logs en Render Dashboard → tu servicio → "Logs"

### Error: "Database connection failed"
**Solución:** Verifica que DATABASE_URL esté correctamente configurada

### Error: "DisallowedHost"
**Solución:** Agrega el dominio a ALLOWED_HOSTS en las variables de entorno

### Subdominios no funcionan
**Solución:** 
1. Verifica que el wildcard `*.psicoadmin.xyz` esté en Namecheap
2. Verifica que `*.psicoadmin.xyz` esté en Custom Domains de Render
3. Espera propagación DNS (hasta 48 horas)

### SSL/HTTPS no funciona
**Solución:** Render genera certificados SSL automáticamente para custom domains. Espera 5-10 minutos después de agregar el dominio.

---

## 📊 RESUMEN DE CONFIGURACIÓN DNS

### En Namecheap (Advanced DNS)

| Type | Host | Value | TTL |
|------|------|-------|-----|
| A Record | @ | 216.24.57.1 | Automatic |
| CNAME | www | psicoadmin.xyz | Automatic |
| A Record | * | 216.24.57.1 | Automatic |

### En Render (Custom Domains)

| Domain | Status |
|--------|--------|
| psicoadmin.xyz | ✅ Verified |
| www.psicoadmin.xyz | ✅ Verified |
| *.psicoadmin.xyz | ✅ Verified |

---

## 🎯 VENTAJAS DE RENDER SOBRE AWS EB

✅ **Gratis:** Plan gratuito generoso  
✅ **Simple:** No necesitas `eb init` ni configuraciones complejas  
✅ **Auto-deploy:** Push a GitHub = deploy automático  
✅ **SSL gratis:** Certificados SSL automáticos  
✅ **PostgreSQL gratis:** Base de datos incluida  
✅ **Logs en tiempo real:** Dashboard con logs claros  
✅ **Rollback fácil:** Un clic para volver a versión anterior  

---

## 🚀 PRÓXIMOS PASOS

1. ✅ Desplegar backend en Render
2. ✅ Configurar dominio psicoadmin.xyz
3. ⏳ Crear primera clínica de prueba
4. ⏳ Desplegar frontend (React/Next.js) en Vercel o Render
5. ⏳ Conectar frontend con backend
6. ⏳ Configurar webhooks de Stripe para producción
7. ⏳ Configurar backups automáticos

---

**¿Listo para empezar?** Sigue los pasos en orden y cualquier duda, me avisas. 🚀
