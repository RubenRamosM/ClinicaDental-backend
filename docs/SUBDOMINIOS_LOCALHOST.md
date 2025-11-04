# 🌐 Configuración de Subdominios en Localhost

## 📋 Información General

Para desarrollo local, el sistema está configurado para usar subdominios en localhost:

- **Base:** `http://localhost:8000`
- **Clínica Norte:** `http://norte.localhost:8000`
- **Clínica Sur:** `http://sur.localhost:8000`
- **Clínica Este:** `http://este.localhost:8000`
- **Clínica Oeste:** `http://oeste.localhost:8000`

---

## ✅ Funcionamiento Automático

La mayoría de navegadores modernos **reconocen automáticamente** subdominios de localhost sin configuración adicional:

- ✅ **Chrome** - Funciona nativamente
- ✅ **Firefox** - Funciona nativamente
- ✅ **Edge** - Funciona nativamente
- ✅ **Safari** - Funciona nativamente

---

## 🔧 Configuración Opcional (Archivo hosts)

Si por alguna razón los subdominios no funcionan automáticamente, puedes agregar manualmente al archivo `hosts`:

### Windows
**Ubicación:** `C:\Windows\System32\drivers\etc\hosts`

```
127.0.0.1   localhost
127.0.0.1   norte.localhost
127.0.0.1   sur.localhost
127.0.0.1   este.localhost
127.0.0.1   oeste.localhost
```

### Linux / macOS
**Ubicación:** `/etc/hosts`

```bash
127.0.0.1   localhost
127.0.0.1   norte.localhost
127.0.0.1   sur.localhost
127.0.0.1   este.localhost
127.0.0.1   oeste.localhost
```

**Nota:** Necesitas permisos de administrador para editar este archivo.

---

## 🧪 Probar Subdominios

### 1. Iniciar servidor Django
```bash
python manage.py runserver 8000
```

### 2. Acceder desde el navegador

- Principal: http://localhost:8000
- Norte: http://norte.localhost:8000
- Sur: http://sur.localhost:8000
- Este: http://este.localhost:8000
- Oeste: http://oeste.localhost:8000

---

## 🔍 Verificar que Funciona

### Método 1: Desde el navegador
Abre cualquier subdominio y revisa las herramientas de desarrollador:
- **Red/Network:** Debe mostrar peticiones exitosas
- **Consola:** No debe haber errores CORS

### Método 2: Desde PowerShell/Terminal
```powershell
# Probar resolución DNS
ping norte.localhost
ping sur.localhost

# Debería responder:
# Haciendo ping a norte.localhost [127.0.0.1]
```

### Método 3: Curl
```bash
curl http://norte.localhost:8000/api/v1/
curl http://sur.localhost:8000/api/v1/
```

---

## 📡 Frontend con Subdominios

### React/Vite (desarrollo)

Si tu frontend corre en puerto 5173:

```javascript
// config.js
const API_BASE = import.meta.env.DEV 
  ? 'http://localhost:8000/api/v1'
  : 'https://api.clinicadental.com/api/v1';

// Para multi-tenancy
const getSubdomain = () => {
  const hostname = window.location.hostname;
  const parts = hostname.split('.');
  
  if (parts.length > 1 && parts[0] !== 'www') {
    return parts[0]; // 'norte', 'sur', 'este', 'oeste'
  }
  return null;
};

// Usar subdominio en requests
const subdomain = getSubdomain();
if (subdomain) {
  // Agregar header x-tenant-subdomain
  axios.defaults.headers.common['x-tenant-subdomain'] = subdomain;
}
```

### Ejecutar Frontend con Subdominio

```bash
# Frontend normal
npm run dev
# Acceder: http://localhost:5173

# Frontend con subdominio (requiere configuración en vite.config.js)
npm run dev -- --host norte.localhost
# Acceder: http://norte.localhost:5173
```

**Configuración en `vite.config.js`:**
```javascript
export default defineConfig({
  server: {
    host: true, // Permite subdominios
    port: 5173,
  }
})
```

---

## 🛡️ CORS en Desarrollo

El backend está configurado para permitir TODOS los orígenes en modo DEBUG:

```python
# config/settings.py
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True
```

Esto incluye:
- ✅ `http://localhost:5173`
- ✅ `http://norte.localhost:5173`
- ✅ `http://sur.localhost:8000`
- ✅ Cualquier otro subdominio local

---

## 🚀 Producción

En producción, los subdominios funcionarán con tu dominio real:

```
https://clinicadental.com           → Sitio principal
https://norte.clinicadental.com     → Clínica Norte
https://sur.clinicadental.com       → Clínica Sur
https://este.clinicadental.com      → Clínica Este
https://oeste.clinicadental.com     → Clínica Oeste
```

**Requisitos:**
1. Dominio registrado (ej: clinicadental.com)
2. DNS configurado con wildcard subdomain (*) apuntando a tu servidor
3. Certificado SSL wildcard (*.clinicadental.com)

---

## ❓ Solución de Problemas

### Problema: "No se puede acceder a norte.localhost"

**Solución 1:** Usa otro navegador
- Chrome/Firefox suelen funcionar mejor

**Solución 2:** Edita archivo hosts
- Agrega entradas manualmente (ver sección anterior)

**Solución 3:** Usa la IP directamente
```
http://127.0.0.1:8000
```

### Problema: Error CORS

**Verificar:**
```python
# En settings.py
DEBUG = True  # Debe estar en True
CORS_ALLOW_ALL_ORIGINS = True  # Se activa automáticamente si DEBUG=True
```

**Revisar logs del backend:**
```bash
python manage.py runserver
# Ver en consola si hay errores CORS
```

### Problema: Frontend no envía credenciales

**En Axios:**
```javascript
axios.defaults.withCredentials = true;
```

**En Fetch:**
```javascript
fetch(url, {
  credentials: 'include'
})
```

---

## 📚 Referencias

- **Django CORS:** https://github.com/adamchainz/django-cors-headers
- **Vite Server Options:** https://vitejs.dev/config/server-options.html
- **Subdominios en localhost:** Funciona nativamente en navegadores modernos

---

**Última actualización:** Noviembre 3, 2025
