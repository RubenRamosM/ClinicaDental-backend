# 🚀 Guía: Deploy Frontend en Vercel con Multi-Tenancy

## 🎯 Objetivo

Desplegar el frontend React/Vue en Vercel con soporte para:
- ✅ Subdominios wildcard (`*.psicoadmin.xyz`)
- ✅ Detección automática de tenant
- ✅ SSL automático
- ✅ Deploy automático desde Git

---

## 📋 Tabla de Contenidos

1. [Preparación del Proyecto](#1-preparación-del-proyecto)
2. [Configuración de Vercel](#2-configuración-de-vercel)
3. [Configuración DNS](#3-configuración-dns)
4. [Variables de Entorno](#4-variables-de-entorno)
5. [Deploy y Verificación](#5-deploy-y-verificación)
6. [Testing](#6-testing)
7. [Troubleshooting](#7-troubleshooting)

---

## 1. Preparación del Proyecto

### **1.1. Estructura del Proyecto Frontend**

```
frontend/
├── src/
│   ├── utils/
│   │   └── tenant.js          # ← Copiar de docs/FRONTEND_TENANT_UTILS.js
│   ├── services/
│   │   └── api.js             # ← Copiar de docs/FRONTEND_API_SERVICE.js
│   ├── components/
│   │   ├── LoginPage.jsx
│   │   └── TenantNotFound.jsx
│   └── App.jsx
├── public/
├── .env.production            # ← Variables de producción
├── vercel.json                # ← Configuración de Vercel
├── package.json
└── vite.config.js             # ← Configuración de Vite
```

### **1.2. Crear vercel.json**

Crea el archivo `vercel.json` en la raíz de tu proyecto frontend:

```json
{
  "version": 2,
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "framework": "vite",
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ],
  "headers": [
    {
      "source": "/assets/(.*)",
      "headers": [
        {
          "key": "Cache-Control",
          "value": "public, max-age=31536000, immutable"
        }
      ]
    },
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        },
        {
          "key": "X-Frame-Options",
          "value": "DENY"
        },
        {
          "key": "X-XSS-Protection",
          "value": "1; mode=block"
        }
      ]
    }
  ],
  "regions": ["iad1"]
}
```

**Explicación:**
- `rewrites`: Redirige todas las rutas a `index.html` (SPA routing)
- `headers`: Headers de seguridad y caché
- `regions`: Región de deploy (iad1 = US East)

### **1.3. Actualizar vite.config.js**

```javascript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist',
    sourcemap: false, // Desactivar en producción
    minify: 'terser',
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom', 'react-router-dom'],
          axios: ['axios']
        }
      }
    }
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: true
  }
})
```

### **1.4. Crear .env.production**

Crea `.env.production` en la raíz:

```bash
# Backend en Render
VITE_API_BASE_URL=https://clinicadental-backend.onrender.com/api
VITE_DOMAIN_BASE=psicoadmin.xyz
VITE_USE_SUBDOMAIN=true

# Opcional: Analytics, etc.
VITE_APP_VERSION=1.0.0
```

**⚠️ IMPORTANTE:** No incluyas secretos aquí. Las variables `VITE_*` son públicas.

### **1.5. Actualizar package.json**

```json
{
  "name": "clinica-dental-frontend",
  "version": "1.0.0",
  "scripts": {
    "dev": "vite --host 0.0.0.0",
    "build": "vite build",
    "preview": "vite preview",
    "lint": "eslint src --ext js,jsx"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "axios": "^1.6.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.2.0",
    "vite": "^5.0.0"
  }
}
```

---

## 2. Configuración de Vercel

### **2.1. Crear Cuenta en Vercel**

1. Ve a [vercel.com](https://vercel.com)
2. Clic en **"Sign Up"**
3. Conecta con **GitHub** (recomendado)
4. Autoriza acceso a tus repositorios

### **2.2. Importar Proyecto**

#### **Opción A: Desde Dashboard Web**

1. Dashboard → **"Add New Project"**
2. Selecciona tu repositorio frontend
3. Configuración detectada automáticamente:
   ```
   Framework Preset: Vite
   Build Command: npm run build
   Output Directory: dist
   Install Command: npm install
   ```
4. **NO hagas deploy todavía** (primero configuramos variables)

#### **Opción B: Desde CLI (Recomendado)**

```bash
# Instalar Vercel CLI
npm install -g vercel

# En la carpeta de tu frontend
cd tu-proyecto-frontend

# Login
vercel login

# Inicializar proyecto
vercel

# Seguir prompts:
# - Set up and deploy? Y
# - Which scope? Tu usuario
# - Link to existing project? N
# - Project name? clinica-dental-frontend
# - Directory? ./
# - Override settings? N
```

### **2.3. Configurar Variables de Entorno en Vercel**

#### **Desde Dashboard:**

1. Dashboard → Tu proyecto → **"Settings"** → **"Environment Variables"**

2. Agregar variables:

| Key | Value | Environment |
|-----|-------|-------------|
| `VITE_API_BASE_URL` | `https://clinicadental-backend.onrender.com/api` | Production |
| `VITE_DOMAIN_BASE` | `psicoadmin.xyz` | Production |
| `VITE_USE_SUBDOMAIN` | `true` | Production |

3. Click **"Save"**

#### **Desde CLI:**

```bash
# Agregar variables de entorno
vercel env add VITE_API_BASE_URL production
# Pegar: https://clinicadental-backend.onrender.com/api

vercel env add VITE_DOMAIN_BASE production
# Pegar: psicoadmin.xyz

vercel env add VITE_USE_SUBDOMAIN production
# Pegar: true
```

---

## 3. Configuración DNS

### **3.1. Obtener Información de Vercel**

Después del primer deploy, Vercel te asignará un dominio:
```
https://clinica-dental-frontend-abc123.vercel.app
```

### **3.2. Agregar Dominio Personalizado en Vercel**

1. Dashboard → Tu proyecto → **"Settings"** → **"Domains"**

2. **Agregar dominio principal:**
   - Ingresar: `psicoadmin.xyz`
   - Click **"Add"**
   - Vercel mostrará configuración DNS requerida

3. **Agregar subdominio www (opcional):**
   - Ingresar: `www.psicoadmin.xyz`
   - Click **"Add"**

4. **Agregar wildcard para tenants:**
   - Ingresar: `*.psicoadmin.xyz`
   - Click **"Add"**
   - **IMPORTANTE:** Esto permite `clinica1.psicoadmin.xyz`, `clinica2.psicoadmin.xyz`, etc.

### **3.3. Configurar DNS en tu Proveedor**

#### **Si usas Hostinger:**

1. Ve a tu panel de Hostinger
2. **Dominios** → `psicoadmin.xyz` → **"DNS Records"**

3. **Eliminar registros A existentes** (si los hay)

4. **Agregar registros nuevos:**

**Registro 1: Dominio raíz**
```
Tipo: A
Nombre: @
Valor: 76.76.21.21
TTL: Automático
```

**Registro 2: www**
```
Tipo: CNAME
Nombre: www
Valor: cname.vercel-dns.com
TTL: Automático
```

**Registro 3: Wildcard para subdominios**
```
Tipo: CNAME
Nombre: *
Valor: cname.vercel-dns.com
TTL: Automático
```

#### **Si usas Cloudflare:**

1. Dashboard → Tu dominio → **"DNS"**

2. **Agregar registros:**

**Registro 1: Dominio raíz**
```
Type: A
Name: @
IPv4 address: 76.76.21.21
Proxy status: DNS only (nube gris)
```

**Registro 2: Wildcard**
```
Type: CNAME
Name: *
Target: cname.vercel-dns.com
Proxy status: DNS only (nube gris)
```

**⚠️ IMPORTANTE:** Desactiva el proxy de Cloudflare (nube gris) para que Vercel maneje SSL.

### **3.4. Verificar DNS**

Espera 5-10 minutos y verifica:

```bash
# Verificar dominio principal
nslookup psicoadmin.xyz

# Verificar wildcard
nslookup clinica1.psicoadmin.xyz
nslookup clinica2.psicoadmin.xyz

# Resultado esperado:
# Non-authoritative answer:
# Name: clinica1.psicoadmin.xyz
# Address: 76.76.21.21
```

---

## 4. Variables de Entorno

### **4.1. Variables Requeridas**

Vercel necesita estas variables configuradas:

```bash
# Backend API
VITE_API_BASE_URL=https://clinicadental-backend.onrender.com/api

# Dominio base para detección de tenant
VITE_DOMAIN_BASE=psicoadmin.xyz

# Habilitar multi-tenancy
VITE_USE_SUBDOMAIN=true
```

### **4.2. Variables Opcionales**

```bash
# Versión de la app
VITE_APP_VERSION=1.0.0

# Ambiente
VITE_APP_ENV=production

# Analytics (opcional)
VITE_GOOGLE_ANALYTICS_ID=G-XXXXXXXXXX

# Sentry (opcional)
VITE_SENTRY_DSN=https://...
```

### **4.3. Verificar Variables**

```bash
# Ver variables configuradas
vercel env ls

# Descargar variables a .env.local (para testing)
vercel env pull
```

---

## 5. Deploy y Verificación

### **5.1. Deploy Inicial**

#### **Opción A: Deploy Manual**

```bash
# Desde tu proyecto frontend
vercel --prod

# Vercel mostrará:
# ✅ Production: https://clinica-dental-frontend.vercel.app
# ✅ https://psicoadmin.xyz
# ✅ https://*.psicoadmin.xyz
```

#### **Opción B: Deploy desde Git (Automático)**

1. Push a tu rama principal:
   ```bash
   git add .
   git commit -m "feat: Configurar para deploy en Vercel"
   git push origin main
   ```

2. Vercel detecta el push y despliega automáticamente

3. Monitorea en Dashboard → **"Deployments"**

### **5.2. Verificar Deploy**

#### **A. Verificar dominio principal:**

```bash
curl -I https://psicoadmin.xyz

# Resultado esperado:
HTTP/2 200
server: Vercel
x-vercel-id: iad1::xxxxx
```

#### **B. Verificar subdominios:**

```bash
curl -I https://clinica1.psicoadmin.xyz

# Resultado esperado:
HTTP/2 200
```

#### **C. Verificar detección de tenant:**

Abre en navegador:
- `https://psicoadmin.xyz` → Debería mostrar "Sistema Central"
- `https://clinica1.psicoadmin.xyz` → Debería mostrar "Clínica Clinica1"

### **5.3. Verificar SSL**

Vercel genera certificados SSL automáticamente:

1. Dashboard → Tu proyecto → **"Settings"** → **"Domains"**

2. Verifica que todos los dominios tengan:
   ```
   ✅ SSL Certificate: Valid
   ```

**Tiempo estimado:** 5-15 minutos después de configurar DNS

---

## 6. Testing

### **6.1. Test de Subdominios**

```bash
# Test 1: Dominio público
curl https://psicoadmin.xyz/api/health

# Test 2: Clínica 1
curl https://clinica1.psicoadmin.xyz/api/health

# Test 3: Clínica 2
curl https://clinica2.psicoadmin.xyz/api/health
```

### **6.2. Test de Login**

```bash
# Login en clínica 1
curl -X POST https://clinica1.psicoadmin.xyz/api/autenticacion/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "correoelectronico": "admin@clinica1.com",
    "password": "admin123"
  }'
```

### **6.3. Test desde Navegador**

1. **Test público:**
   - URL: `https://psicoadmin.xyz`
   - Debería: Mostrar "Sistema Central"

2. **Test clínica 1:**
   - URL: `https://clinica1.psicoadmin.xyz`
   - Debería: Mostrar "Clínica Clinica1"
   - Login: `admin@clinica1.com` / `admin123`

3. **Test clínica inexistente:**
   - URL: `https://clinica999.psicoadmin.xyz`
   - Debería: Mostrar error "Clínica no encontrada"

---

## 7. Troubleshooting

### **Problema 1: "This domain is not configured"**

**Causa:** DNS no propagado o configurado incorrectamente

**Solución:**
```bash
# Verificar DNS
nslookup psicoadmin.xyz

# Si no resuelve:
1. Revisa configuración DNS en tu proveedor
2. Espera 10-30 minutos para propagación
3. Limpia caché DNS: ipconfig /flushdns (Windows)
```

### **Problema 2: "ERR_CERT_COMMON_NAME_INVALID"**

**Causa:** Certificado SSL aún no generado

**Solución:**
1. Vercel Dashboard → Domains → Verificar estado SSL
2. Si dice "Pending", espera 15 minutos
3. Si falla, click **"Refresh"** o **"Remove"** y re-agregar

### **Problema 3: "Failed to fetch" en frontend**

**Causa:** CORS o backend no accesible

**Solución:**
```javascript
// Verificar en console del navegador:
console.log('API URL:', import.meta.env.VITE_API_BASE_URL);
// Debería mostrar: https://clinicadental-backend.onrender.com/api

// Verificar backend:
// 1. Ve a Render Dashboard
// 2. Confirma que servicio esté LIVE
// 3. Verifica logs para errores CORS
```

### **Problema 4: Tenant no detectado correctamente**

**Causa:** Configuración incorrecta de tenant.js

**Solución:**
```javascript
// Verificar en console del navegador:
import { getTenantInfo } from './utils/tenant';
console.log(getTenantInfo());

// Resultado esperado en clinica1.psicoadmin.xyz:
// {
//   subdomain: 'clinica1',
//   isPublic: false,
//   tenantId: 'clinica1',
//   ...
// }
```

### **Problema 5: Deploy falla en Vercel**

**Causa:** Error de build

**Solución:**
```bash
# Ver logs de build en Vercel Dashboard → Deployments → Click en el deploy fallido

# Errores comunes:
# 1. Falta dependencia → npm install [paquete]
# 2. Variable de entorno faltante → Agregar en Settings
# 3. Error de sintaxis → Revisar código

# Probar build local:
npm run build

# Si falla local, arreglarlo antes de deploy
```

---

## 8. Deploy Automático (CI/CD)

### **8.1. Configurar Git Integration**

Vercel ya está conectado a tu Git. Cada push despliega automáticamente:

```bash
# Feature branch → Preview deployment
git checkout -b feature/nueva-funcionalidad
git push origin feature/nueva-funcionalidad
# Vercel crea: https://clinica-dental-frontend-git-feature-xxx.vercel.app

# Main branch → Production deployment
git checkout main
git merge feature/nueva-funcionalidad
git push origin main
# Vercel despliega a: https://psicoadmin.xyz
```

### **8.2. Preview Deployments**

Cada pull request crea un deployment de preview:

1. GitHub → Crear Pull Request
2. Vercel comenta automáticamente con URL de preview
3. Revisar cambios en preview antes de mergear
4. Mergear → Deploy automático a producción

---

## 9. Monitoreo y Mantenimiento

### **9.1. Logs en Tiempo Real**

```bash
# Ver logs desde CLI
vercel logs

# O desde Dashboard:
# Dashboard → Tu proyecto → Logs
```

### **9.2. Analytics**

Vercel incluye analytics gratis:

1. Dashboard → Tu proyecto → **"Analytics"**
2. Ver:
   - Visitas por página
   - Performance (Web Vitals)
   - Errores 4xx/5xx
   - Tráfico por país

### **9.3. Rollback (Si algo falla)**

```bash
# Ver deployments anteriores
vercel ls

# Promover deployment anterior a producción
vercel promote [deployment-url]

# O desde Dashboard:
# Deployments → Click en deployment anterior → "Promote to Production"
```

---

## 10. Checklist Final

Antes de considerar el deploy completo, verifica:

- [ ] **DNS configurado:**
  - [ ] A record para `@` → `76.76.21.21`
  - [ ] CNAME para `*` → `cname.vercel-dns.com`

- [ ] **Dominios en Vercel:**
  - [ ] `psicoadmin.xyz` agregado
  - [ ] `*.psicoadmin.xyz` agregado
  - [ ] SSL válido en todos

- [ ] **Variables de entorno:**
  - [ ] `VITE_API_BASE_URL` configurada
  - [ ] `VITE_DOMAIN_BASE` configurada
  - [ ] `VITE_USE_SUBDOMAIN=true`

- [ ] **Código frontend:**
  - [ ] `tenant.js` implementado
  - [ ] `api.js` configurado
  - [ ] `vercel.json` creado
  - [ ] `.env.production` configurado

- [ ] **Testing:**
  - [ ] Login funciona en `clinica1.psicoadmin.xyz`
  - [ ] Detección de tenant correcta
  - [ ] Redirección a tenant correcto
  - [ ] Error 404 para tenant inexistente

- [ ] **Backend (Render):**
  - [ ] Servicio LIVE
  - [ ] Seeder ejecutado (`python seed_render.py`)
  - [ ] CORS configurado para `*.psicoadmin.xyz`

---

## 🎉 ¡Deploy Completado!

Tu aplicación ahora está disponible en:

### **URLs Públicas:**
- 🌐 Sistema Central: `https://psicoadmin.xyz`
- 🏥 Clínica 1: `https://clinica1.psicoadmin.xyz`
- 🏥 Clínica 2: `https://clinica2.psicoadmin.xyz`

### **URLs de Desarrollo:**
- 🧪 Vercel App: `https://clinica-dental-frontend.vercel.app`
- 🔧 Preview: `https://clinica-dental-frontend-git-xxx.vercel.app`

---

## 📚 Recursos Adicionales

- [Documentación Vercel](https://vercel.com/docs)
- [Wildcard Domains en Vercel](https://vercel.com/docs/concepts/projects/domains/wildcard-domains)
- [Environment Variables](https://vercel.com/docs/concepts/projects/environment-variables)
- [Deploy Hooks](https://vercel.com/docs/concepts/git/deploy-hooks)

---

## 🆘 Soporte

Si tienes problemas:

1. **Vercel Logs:** Dashboard → Logs
2. **Browser Console:** F12 → Console (ver errores JS)
3. **Network Tab:** F12 → Network (ver requests fallidos)
4. **DNS Checker:** [whatsmydns.net](https://www.whatsmydns.net)

**Comandos útiles:**
```bash
# Verificar versión desplegada
vercel inspect [url]

# Ver información del proyecto
vercel project ls

# Re-deployar
vercel --prod --force
```

---

**¡Tu aplicación multi-tenant está lista para producción! 🚀**
