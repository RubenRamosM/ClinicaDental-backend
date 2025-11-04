# 🚀 PASOS RÁPIDOS PARA DESPLEGAR EN RENDER

## ✅ PASO 1: CONFIGURAR DNS EN NAMECHEAP (5 minutos)

1. Ve a: https://ap.www.namecheap.com/domains/domaincontrolpanel/psicoadmin.xyz/advancedns

2. Elimina todos los registros DNS existentes

3. Agrega estos 3 registros:

```
Tipo: A Record
Host: @
Valor: 216.24.57.1
TTL: Automatic

Tipo: CNAME Record  
Host: www
Valor: psicoadmin.xyz
TTL: Automatic

Tipo: A Record
Host: *
Valor: 216.24.57.1
TTL: Automatic
```

✅ Listo! El DNS está configurado para Render

---

## 🎨 PASO 2: CREAR CUENTA EN RENDER (2 minutos)

1. Ve a https://render.com
2. Clic en "Get Started"
3. Conecta con GitHub
4. Autoriza acceso a tu repositorio `RubenRamosM/ClinicaDental-backend`

---

## 🗄️ PASO 3: CREAR BASE DE DATOS POSTGRESQL (3 minutos)

1. En Dashboard de Render → "New +" → "PostgreSQL"
2. Configurar:
   - Name: `clinicadental-db`
   - Database: `clinicadental`
   - Region: Oregon (US West)
   - Plan: **Free**
3. Clic "Create Database"
4. **⚠️ IMPORTANTE:** Copia la "Internal Database URL" (la necesitarás en el siguiente paso)
postgresql://clinicadental_kx8i_user:9xb0k96HTwrKtPhkOTo7kn3P1KAM0Gkm@dpg-d44o7juuk2gs73fj3o0g-a/clinicadental_kx8i
---

## 🚀 PASO 4: CREAR WEB SERVICE (10 minutos)

1. En Dashboard → "New +" → "Web Service"
2. Selecciona tu repo `ClinicaDental-backend`
3. Configurar:
   - Name: `clinicadental-backend`
   - Region: Oregon (US West)
   - Branch: `main`
   - Runtime: Python 3
   - Build Command: `./build.sh`
   - Start Command: `gunicorn config.wsgi:application`
   - Plan: **Free**

4. Haz clic en "Advanced" y agrega estas **Environment Variables**:

```bash
# Básicas
DEBUG=False
PYTHON_VERSION=3.13.7
DJANGO_SETTINGS_MODULE=config.settings

# Seguridad (haz clic en "Generate" para SECRET_KEY)
SECRET_KEY=[Generate]

# Base de Datos (pega la URL que copiaste del paso anterior)
DATABASE_URL=postgresql://clinicadental_user:XXXXX@dpg-XXXXX.oregon-postgres.render.com/clinicadental

# Dominios
ALLOWED_HOSTS=.onrender.com,.psicoadmin.xyz,psicoadmin.xyz,www.psicoadmin.xyz

CORS_ALLOWED_ORIGINS=https://psicoadmin.xyz,https://www.psicoadmin.xyz

CSRF_TRUSTED_ORIGINS=https://psicoadmin.xyz,https://www.psicoadmin.xyz,https://*.psicoadmin.xyz,https://*.onrender.com

# Multitenancy
SAAS_BASE_DOMAIN=psicoadmin.xyz
SAAS_PUBLIC_URL=https://psicoadmin.xyz

# AWS S3 (reemplaza con tus credenciales)
AWS_ACCESS_KEY_ID=tu_access_key_aqui
AWS_SECRET_ACCESS_KEY=tu_secret_key_aqui
AWS_STORAGE_BUCKET_NAME=clinica-dental-bucket
AWS_S3_REGION_NAME=us-east-1

# Stripe (opcional)
STRIPE_SECRET_KEY=sk_test_XXXXX
STRIPE_PUBLISHABLE_KEY=pk_test_XXXXX

# OpenAI (para chatbot)
OPENAI_API_KEY=sk-XXXXX
```

5. Clic "Create Web Service"
6. Espera 5-10 minutos mientras Render construye y despliega

---

## 🌍 PASO 5: AGREGAR CUSTOM DOMAIN (5 minutos)

1. Ve a tu servicio → "Settings" → "Custom Domains"
2. Clic "Add Custom Domain"
3. Agrega uno por uno:
   - `psicoadmin.xyz` → Verify
   - `www.psicoadmin.xyz` → Verify
   - `*.psicoadmin.xyz` → Verify (wildcard para subdominios)

**⚠️ NOTA:** Render verificará automáticamente que los DNS apunten correctamente. Puede tardar hasta 1 hora (normalmente es instantáneo).

---

## ✅ PASO 6: VERIFICAR DESPLIEGUE (2 minutos)

1. Espera a que el servicio muestre **"Live"** en verde

2. Prueba estos URLs en tu navegador:

```
https://clinicadental-backend.onrender.com/admin/
https://psicoadmin.xyz/admin/
```

Deberías ver la página de login de Django Admin.

---

## 🏥 PASO 7: CREAR PRIMERA CLÍNICA (opcional)

Desde Postman o Thunder Client:

```http
POST https://psicoadmin.xyz/api/v1/clinicas/
Content-Type: application/json
Authorization: Bearer tu_token_aqui

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
  "plan": "profesional"
}
```

La clínica estará disponible en: `https://clinica1.psicoadmin.xyz`

---

## 🔧 TROUBLESHOOTING

### "Application failed to start"
→ Ve a Dashboard → tu servicio → "Logs" para ver el error específico

### "Database connection failed"  
→ Verifica que DATABASE_URL esté correcta y que incluya la Internal Database URL de Render

### "DisallowedHost at /"
→ Agrega el dominio a la variable ALLOWED_HOSTS

### Subdominios no funcionan
→ Espera propagación DNS (hasta 48 horas, normalmente 1-2 horas)
→ Verifica que `*.psicoadmin.xyz` esté en Custom Domains de Render

---

## 📊 RESUMEN

| Paso | Tiempo | Status |
|------|--------|--------|
| 1. Configurar DNS Namecheap | 5 min | ⏳ |
| 2. Cuenta Render | 2 min | ⏳ |
| 3. PostgreSQL Database | 3 min | ⏳ |
| 4. Web Service + Variables | 10 min | ⏳ |
| 5. Custom Domains | 5 min | ⏳ |
| 6. Verificar | 2 min | ⏳ |
| **TOTAL** | **~30 min** | ⏳ |

---

## 🎯 TU APLICACIÓN ESTARÁ EN:

- **Backend API:** https://psicoadmin.xyz/api/v1/
- **Admin Django:** https://psicoadmin.xyz/admin/
- **Clínica 1:** https://clinica1.psicoadmin.xyz/api/v1/
- **Clínica 2:** https://clinica2.psicoadmin.xyz/api/v1/
- **Etc...**

---

**¡Listo! Sigue los pasos y avísame si tienes algún problema.** 🚀
