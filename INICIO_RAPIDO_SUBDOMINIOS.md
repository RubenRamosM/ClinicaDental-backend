# 🚀 INICIO RÁPIDO - SUBDOMINIOS

## ✅ EL SERVIDOR YA ESTÁ CORRIENDO

El servidor está funcionando en: **http://0.0.0.0:8001/**

---

## 📝 PASOS PARA HABILITAR SUBDOMINIOS

### PASO 1: Configurar Archivo Hosts (OBLIGATORIO)

**OPCIÓN A: Automático (Recomendado)**
```powershell
# Abrir PowerShell COMO ADMINISTRADOR
# Click derecho en PowerShell → Ejecutar como administrador

# Ejecutar el script
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\configurar_hosts.ps1
```

**OPCIÓN B: Manual**
1. Abrir Bloc de Notas **como Administrador**
2. Abrir: `C:\Windows\System32\drivers\etc\hosts`
3. Agregar al final:
   ```
   127.0.0.1 localhost
   127.0.0.1 clinica1.localhost
   127.0.0.1 clinica2.localhost
   127.0.0.1 clinica3.localhost
   ```
4. Guardar

---

### PASO 2: Probar en el Navegador

Abre estas URLs en tu navegador:

**Tenant Público:**
```
http://localhost:8001/api/
```

**Clínica 1:**
```
http://clinica1.localhost:8001/api/
```

**Admin Público:**
```
http://localhost:8001/admin/
```

**Admin Clínica 1:**
```
http://clinica1.localhost:8001/admin/
```

---

### PASO 3: Verificar en los Logs

Mira la terminal donde está corriendo el servidor. Deberías ver:

**Cuando accedes a localhost:**
```
SELECT ... WHERE "comun_dominio"."domain" = 'localhost'
SET search_path = 'public'
```

**Cuando accedes a clinica1.localhost:**
```
SELECT ... WHERE "comun_dominio"."domain" = 'clinica1.localhost'  
SET search_path = 'clinica1'
```

✅ Si ves esto, **¡el multitenancy está funcionando!**

---

## 🔧 SI ALGO NO FUNCIONA

### Error: "Este sitio no puede proporcionar una conexión segura"

**Causa:** Archivo hosts no configurado

**Solución:**
1. Ejecuta como administrador: `.\configurar_hosts.ps1`
2. O edita manualmente el archivo hosts (ver PASO 1 opción B)
3. Luego ejecuta: `ipconfig /flushdns`

### Error: "No se puede acceder a este sitio"

**Causa:** El servidor no está corriendo o está en 127.0.0.1 en vez de 0.0.0.0

**Solución:**
```powershell
# Detén el servidor actual (Ctrl+C si está corriendo)
# Inicia con 0.0.0.0
python manage.py runserver 0.0.0.0:8001 --noreload
```

### El subdominio muestra "Tenant not found"

**Causa:** El dominio no existe en la base de datos

**Solución:**
```powershell
# Ver dominios configurados
python verificar_multitenancy.py

# Si falta clinica1, créala
python crear_clinica.py
```

---

## 📋 COMANDOS ÚTILES

```powershell
# Ver tenants configurados
python verificar_multitenancy.py

# Crear nueva clínica
python crear_clinica.py

# Limpiar caché DNS (después de editar hosts)
ipconfig /flushdns

# Verificar que el servidor esté corriendo
netstat -ano | findstr ":8001"

# Probar conexión a subdominios
ping clinica1.localhost
```

---

## 🎯 ESTADO ACTUAL

✅ Servidor corriendo en puerto 8001  
✅ Multitenancy configurado  
✅ Tenant público: `localhost`  
✅ Clínica 1: `clinica1.localhost`  

### Para completar:
- [ ] Configurar archivo hosts (PASO 1)
- [ ] Probar en navegador (PASO 2)
- [ ] Verificar logs (PASO 3)

---

## 📚 MÁS INFORMACIÓN

Ver guía completa: **GUIA_DESPLIEGUE_SUBDOMINIOS.md**

---

**Última actualización:** 04 de Noviembre, 2025
