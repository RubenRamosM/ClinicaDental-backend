# 🚀 GUÍA PASO A PASO: DESPLIEGUE Y SUBDOMINIOS

## 📋 ÍNDICE
1. [Configurar Archivo Hosts](#paso-1-configurar-archivo-hosts)
2. [Verificar Dominios en Base de Datos](#paso-2-verificar-dominios)
3. [Iniciar Servidor Correctamente](#paso-3-iniciar-servidor)
4. [Probar Subdominios](#paso-4-probar-subdominios)
5. [Crear Nuevas Clínicas](#paso-5-crear-nuevas-clínicas)
6. [Configurar Frontend](#paso-6-configurar-frontend)

---

## PASO 1: Configurar Archivo Hosts

### ¿Por qué?
Windows necesita saber que `clinica1.localhost`, `clinica2.localhost`, etc. apuntan a tu máquina local (127.0.0.1).

### Instrucciones:

1. **Abrir el Bloc de Notas como Administrador**
   - Presiona `Windows + S`
   - Escribe "Bloc de notas"
   - Click derecho → "Ejecutar como administrador"

2. **Abrir el archivo hosts**
   - En el Bloc de notas: Archivo → Abrir
   - Navega a: `C:\Windows\System32\drivers\etc`
   - Cambia el filtro de "Documentos de texto (*.txt)" a "Todos los archivos (*.*)"
   - Selecciona el archivo `hosts` (sin extensión)

3. **Agregar las siguientes líneas al final del archivo**
   ```
   # Django Multitenancy - Clínica Dental
   127.0.0.1 localhost
   127.0.0.1 clinica1.localhost
   127.0.0.1 clinica2.localhost
   127.0.0.1 clinica3.localhost
   ```

4. **Guardar el archivo**
   - Archivo → Guardar
   - Cierra el Bloc de notas

5. **Verificar que funcionó**
   ```powershell
   ping clinica1.localhost
   ```
   Deberías ver: `Haciendo ping a clinica1.localhost [127.0.0.1]`

---

## PASO 2: Verificar Dominios en Base de Datos

### Script para ver los dominios configurados:

Ejecuta en PowerShell:
```powershell
python verificar_multitenancy.py
```

### Deberías ver algo como:
```
=== TENANTS CONFIGURADOS ===
ID: 1 | Schema: public | Nombre: PSICOADMIN - Super Administración
   Dominios: localhost

ID: 2 | Schema: clinica1 | Nombre: Clínica Dental Norte  
   Dominios: clinica1.localhost
```

### Si falta algún dominio:

**Agregar dominio a tenant existente:**
```python
# crear_dominio.py
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.comun.models import Clinica, Dominio

# Agregar dominio a clinica1
clinica = Clinica.objects.get(schema_name='clinica1')
Dominio.objects.create(
    domain='clinica1.localhost',
    tenant=clinica,
    is_primary=True
)
print("✅ Dominio agregado")
```

---

## PASO 3: Iniciar Servidor Correctamente

### Opción A: Sin DEBUG logging (Recomendado para desarrollo)

```powershell
python manage.py runserver 0.0.0.0:8001 --noreload
```

**¿Por qué `0.0.0.0`?**
- Permite conexiones desde `localhost`, `127.0.0.1` Y subdominios
- Con `127.0.0.1` solo funcionaría para esa IP específica

### Opción B: Con autoreload (para desarrollo activo)

Primero crea un archivo `.env` en la raíz:
```env
DEBUG=False
```

Luego ejecuta:
```powershell
python manage.py runserver 0.0.0.0:8001
```

### Verificar que el servidor inició:
Deberías ver:
```
Starting development server at http://0.0.0.0:8001/
```

---

## PASO 4: Probar Subdominios

### 4.1 Probar el Tenant Público (localhost)

**En el navegador:**
```
http://localhost:8001/api/
```

**O con curl en PowerShell:**
```powershell
curl http://localhost:8001/api/
```

**En los logs del servidor deberías ver:**
```
SELECT ... WHERE "comun_dominio"."domain" = 'localhost'
SET search_path = 'public'
```

### 4.2 Probar Clinica1 (subdominio)

**En el navegador:**
```
http://clinica1.localhost:8001/api/
```

**O con curl:**
```powershell
curl http://clinica1.localhost:8001/api/
```

**En los logs deberías ver:**
```
SELECT ... WHERE "comun_dominio"."domain" = 'clinica1.localhost'
SET search_path = 'clinica1'
```

### 4.3 Verificar Aislamiento de Datos

**Crear usuario en clinica1:**
```powershell
# Ejecutar en nueva terminal (mantén el servidor corriendo)
python manage.py shell
```

```python
from django.contrib.auth.models import User
from apps.comun.models import Clinica
from django.db import connection

# Cambiar a clinica1
clinica = Clinica.objects.get(schema_name='clinica1')
connection.set_tenant(clinica)

# Crear usuario
user = User.objects.create_user(
    username='doctor1',
    email='doctor1@clinica1.com',
    password='password123'
)
print(f"✅ Usuario creado en schema: {connection.schema_name}")
```

**Verificar que el usuario NO existe en public:**
```python
from django.db import connection

# Cambiar a public
clinica_public = Clinica.objects.get(schema_name='public')
connection.set_tenant(clinica_public)

# Buscar usuario
from django.contrib.auth.models import User
existe = User.objects.filter(username='doctor1').exists()
print(f"¿Usuario existe en public? {existe}")  # Debería ser False
```

---

## PASO 5: Crear Nuevas Clínicas

### 5.1 Método Interactivo (Recomendado)

```powershell
python crear_clinica.py
```

Responde las preguntas:
```
Nombre del schema (ejemplo: clinica2): clinica2
Nombre de la clínica: Clínica Dental Sur
RUC: 20987654321
Dirección: Av. Sur 456
Teléfono: 987654321
Email: admin@clinica2.com
Dominio (ejemplo: clinica2.localhost): clinica2.localhost
Plan (basico/profesional/empresarial): profesional
Max usuarios [5]: 10
Max pacientes [100]: 500
```

### 5.2 Método por Parámetros

```powershell
python crear_clinica.py clinica2 "Clínica Dental Sur" 20987654321 admin@clinica2.com
```

### 5.3 Verificar que se creó

```powershell
python verificar_multitenancy.py
```

### 5.4 NO OLVIDES agregar al archivo hosts

```
127.0.0.1 clinica2.localhost
```

---

## PASO 6: Configurar Frontend

### 6.1 Detectar Subdominio Actual

**En JavaScript (React/Vue/Angular):**
```javascript
// utils/tenant.js
export function getCurrentTenant() {
  const hostname = window.location.hostname;
  
  // Extraer subdominio
  const parts = hostname.split('.');
  
  if (parts.length >= 2 && parts[0] !== 'localhost') {
    return {
      subdomain: parts[0],
      domain: `${parts[0]}.localhost`,
      isPublic: false
    };
  }
  
  return {
    subdomain: null,
    domain: 'localhost',
    isPublic: true
  };
}

// Ejemplo de uso
const tenant = getCurrentTenant();
console.log('Tenant actual:', tenant);
// En clinica1.localhost:3000 → { subdomain: 'clinica1', domain: 'clinica1.localhost', isPublic: false }
// En localhost:3000 → { subdomain: null, domain: 'localhost', isPublic: true }
```

### 6.2 Configurar API Base URL

```javascript
// config/api.js
import { getCurrentTenant } from '../utils/tenant';

const tenant = getCurrentTenant();
const API_PORT = 8001;

export const API_BASE_URL = `http://${tenant.domain}:${API_PORT}/api`;

console.log('API URL:', API_BASE_URL);
// En clinica1.localhost → http://clinica1.localhost:8001/api
// En localhost → http://localhost:8001/api
```

### 6.3 Axios/Fetch Configuration

```javascript
// services/api.js
import axios from 'axios';
import { API_BASE_URL } from '../config/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true // Para cookies de sesión
});

// Interceptor para agregar token
api.interceptors.request.use(config => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Token ${token}`;
  }
  return config;
});

export default api;
```

### 6.4 Ejemplo de Uso

```javascript
// components/Login.jsx
import api from '../services/api';

async function login(username, password) {
  try {
    const response = await api.post('/autenticacion/login/', {
      username,
      password
    });
    
    localStorage.setItem('token', response.data.token);
    console.log('✅ Login exitoso en tenant actual');
  } catch (error) {
    console.error('❌ Error:', error);
  }
}
```

---

## 🔧 TROUBLESHOOTING

### Problema: "Tenant not found"

**Causa:** El dominio no existe en la base de datos

**Solución:**
```sql
-- Verificar en PostgreSQL
SELECT d.domain, c.schema_name, c.nombre 
FROM comun_dominio d 
JOIN comun_clinica c ON d.tenant_id = c.id;
```

Si falta, crear con:
```powershell
python crear_clinica.py
```

### Problema: "404 Not Found" en todas las URLs

**Causa:** El tenant no tiene las URLs configuradas correctamente

**Solución:** Verificar que `config/urls.py` esté correctamente configurado:
```python
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('config.url_patterns')),
]
```

### Problema: Los subdominios no resuelven

**Causa:** Archivo hosts no configurado

**Solución:**
1. Verificar que el archivo `C:\Windows\System32\drivers\etc\hosts` tenga las entradas
2. Abrir PowerShell como administrador y ejecutar:
   ```powershell
   ipconfig /flushdns
   ```
3. Reiniciar el navegador

### Problema: CORS errors desde frontend

**Causa:** Django no acepta requests desde el subdominio del frontend

**Solución:** En `config/settings.py`:
```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://clinica1.localhost:3000",
    "http://clinica2.localhost:3000",
    # ... agregar más según necesites
]

# O permitir todos los subdominios de localhost (solo desarrollo)
CORS_ALLOW_ALL_ORIGINS = True  # ¡NO en producción!
```

### Problema: El servidor no arranca

**Solución:**
```powershell
# 1. Verificar que las migraciones estén aplicadas
python manage.py migrate_schemas --schema=public

# 2. Verificar cada tenant
python verificar_multitenancy.py

# 3. Iniciar sin autoreload
python manage.py runserver 0.0.0.0:8001 --noreload
```

---

## 📊 RESUMEN DE COMANDOS IMPORTANTES

```powershell
# Crear nueva clínica
python crear_clinica.py

# Verificar tenants
python verificar_multitenancy.py

# Migrar esquema específico
python manage.py migrate_schemas --schema=clinica1

# Iniciar servidor
python manage.py runserver 0.0.0.0:8001 --noreload

# Crear superusuario en un tenant específico
python manage.py tenant_command createsuperuser --schema=clinica1

# Shell con tenant específico
python manage.py tenant_command shell --schema=clinica1

# Limpiar DNS cache (si los subdominios no funcionan)
ipconfig /flushdns
```

---

## 🎯 CHECKLIST FINAL

Antes de considerar que todo está funcionando:

- [ ] Archivo hosts configurado con todos los subdominios
- [ ] Servidor corriendo en `0.0.0.0:8001`
- [ ] `http://localhost:8001/api/` responde
- [ ] `http://clinica1.localhost:8001/api/` responde
- [ ] Los logs muestran `SET search_path = 'clinica1'` cuando accedes a clinica1
- [ ] Los logs muestran `SET search_path = 'public'` cuando accedes a localhost
- [ ] Puedes crear usuarios en clinica1 y NO aparecen en public
- [ ] Frontend detecta correctamente el subdominio
- [ ] Frontend hace requests a la URL correcta según el subdominio

---

## 🚀 PRÓXIMOS PASOS

1. **Desarrollo:**
   - Implementar dashboard por tenant
   - Crear sistema de registro de clínicas
   - Implementar límites por plan (max_usuarios, max_pacientes)

2. **Producción:**
   - Configurar Nginx/Apache para manejar subdominios
   - Usar Gunicorn/uWSGI en lugar de runserver
   - Configurar SSL/HTTPS para cada subdominio
   - Configurar dominios reales (ejemplo: clinica1.tudominio.com)

3. **Optimización:**
   - Cachear la detección de tenant
   - Implementar tenant middleware personalizado
   - Configurar PostgreSQL connection pooling por tenant

---

**Última actualización:** 04 de Noviembre, 2025
**Estado:** ✅ Sistema funcionando con multitenancy completo
