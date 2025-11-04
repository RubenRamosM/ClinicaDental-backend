# 🌱 Guía: Poblar Base de Datos en Render

## ✅ Estado Actual

Tu aplicación ya está **desplegada y funcionando** en Render:
- ✅ Build exitoso (commit b792804)
- ✅ Servicio LIVE
- ✅ Base de datos PostgreSQL funcionando
- ✅ Tablas creadas (`comun_clinica`, `comun_dominio`)
- ⚠️ **Sin datos** (por eso los 404 son normales)

## 🎯 Objetivo

Ejecutar el script `seed_render.py` que:
1. ✅ Crea el tenant público
2. ✅ Crea la clínica "clinica1" 
3. ✅ Registra dominios (Render + psicoadmin.xyz)
4. ✅ Puebla datos de prueba completos (usuarios, servicios, citas, etc.)

---

## 📋 Paso a Paso

### **Paso 1: Acceder al Shell de Render**

1. Ve a tu **Render Dashboard**
2. Selecciona tu servicio: **clinicadental-backend**
3. En el menú superior, haz clic en **"Shell"**
4. Espera a que se abra la terminal

![Render Shell](https://docs.render.com/images/shell-button.png)

---

### **Paso 2: Ejecutar el Script Poblador**

Una vez en el Shell de Render, ejecuta:

```bash
python seed_render.py
```

**Salida esperada:**

```
======================================================================
  🚀 SEEDER PARA RENDER - CLÍNICA DENTAL
======================================================================

Este script creará:
  1. Tenant público (si no existe)
  2. Clínica principal 'clinica1'
  3. Dominios para Render y psicoadmin.xyz
  4. Datos de prueba completos

======================================================================
  🏢 CONFIGURANDO TENANT PÚBLICO
======================================================================
✅ Tenant público creado
   - Schema: public
   - Dominio: clinicadental-backend.onrender.com

======================================================================
  🏥 CREANDO CLÍNICA PRINCIPAL
======================================================================
✅ Clínica principal creada
   - Nombre: Clínica Dental Norte
   - Schema: clinica1
   - NIT: 1234567890
   - Dominios:
     • clinica1.onrender.com
     • clinica1.psicoadmin.xyz (principal)

======================================================================
  📊 POBLANDO DATOS - Clínica Dental Norte
======================================================================
✓ Conectado al schema: clinica1

📋 Creando datos base...
  ✓ 20 horarios creados
  ✓ 6 estados de consulta
  ✓ 4 tipos de consulta
  ✓ 4 tipos de pago
  ✓ 3 estados de factura

👥 Creando usuarios...
  ✓ 1 administrador
  ✓ 3 odontólogos
  ✓ 1 recepcionista
  ✓ 5 pacientes

🦷 Creando servicios...
  ✓ 10 servicios creados

📅 Creando consultas de ejemplo...
  ✓ 3 consultas creadas

📦 Creando inventario básico...
  ✓ 1 categoría, 1 proveedor, 1 insumo

✅ Datos poblados exitosamente en schema 'clinica1'

======================================================================
  ✅ PROCESO COMPLETADO EXITOSAMENTE
======================================================================
```

---

### **Paso 3: Verificar que ya no hay 404**

1. **Refresca los logs** de Render (pestaña "Logs")
2. Deberías ver ahora:
   - ✅ Queries ejecutando correctamente
   - ✅ Respuestas 200 OK (en lugar de 404)
   - ✅ Tenant encontrado para `clinicadental-backend.onrender.com`

**Ejemplo de log exitoso:**

```
[INFO] SELECT * FROM comun_dominio WHERE domain = 'clinicadental-backend.onrender.com'
[INFO] Tenant found: Sistema Central (schema: public)
[INFO] "GET / HTTP/1.1" 200 OK
```

---

### **Paso 4: Probar el API**

#### **4.1. Verificar que el servidor responde**

```bash
curl https://clinicadental-backend.onrender.com/api/
```

**Respuesta esperada:**
```json
{
  "message": "API de Clínica Dental",
  "version": "1.0",
  "tenant": "Sistema Central"
}
```

#### **4.2. Login como Admin**

```bash
curl -X POST https://clinicadental-backend.onrender.com/api/autenticacion/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "correoelectronico": "admin@clinica1.com",
    "password": "admin123"
  }'
```

**Respuesta esperada:**
```json
{
  "token": "a1b2c3d4e5f6...",
  "usuario": {
    "id": 1,
    "nombre": "Admin",
    "apellido": "Sistema",
    "correoelectronico": "admin@clinica1.com",
    "tipo_usuario": "Administrador"
  }
}
```

---

## 📝 Credenciales de Prueba

### 👨‍💼 **Administrador**
- **Email:** `admin@clinica1.com`
- **Password:** `admin123`
- **Permisos:** Acceso completo al sistema

### 👨‍⚕️ **Odontólogos**
1. **Dr. Juan Carlos Pérez** (Ortodoncia)
   - Email: `dr.perez@clinica1.com`
   - Password: `odontologo123`

2. **Dra. María Fernanda García** (Endodoncia)
   - Email: `dra.garcia@clinica1.com`
   - Password: `odontologo123`

3. **Dr. Roberto Martínez** (Cirugía Oral)
   - Email: `dr.martinez@clinica1.com`
   - Password: `odontologo123`

### 👩‍💼 **Recepcionista**
- **Email:** `recepcion@clinica1.com`
- **Password:** `recepcion123`

### 👥 **Pacientes**
1. **Ana López** - `ana.lopez@email.com` / `paciente123`
2. **Carlos Rodríguez** - `carlos.rodriguez@email.com` / `paciente123`
3. **Beatriz Sánchez** - `beatriz.sanchez@email.com` / `paciente123`
4. **Diego Torres** - `diego.torres@email.com` / `paciente123`
5. **Elena Vargas** - `elena.vargas@email.com` / `paciente123`

---

## 🌐 Dominios Configurados

Después de ejecutar el script, tendrás:

### **1. Dominio Público (Tenant Shared)**
- **URL:** `https://clinicadental-backend.onrender.com`
- **Tenant:** Sistema Central (público)
- **Schema:** `public`
- **Uso:** Landing page, registro de nuevas clínicas

### **2. Dominio Clínica 1 (Render)**
- **URL:** `https://clinica1.onrender.com`
- **Tenant:** Clínica Dental Norte
- **Schema:** `clinica1`
- **Estado:** ⏸️ Pendiente configurar en Render

### **3. Dominio Clínica 1 (Producción)**
- **URL:** `https://clinica1.psicoadmin.xyz`
- **Tenant:** Clínica Dental Norte
- **Schema:** `clinica1`
- **Estado:** ⏸️ Pendiente DNS

---

## 🔧 Próximos Pasos Opcionales

### **Opción 1: Agregar Dominio Personalizado en Render**

1. Ve a **Render Dashboard** → Tu servicio
2. Clic en **"Settings"** → **"Custom Domains"**
3. Agregar: `clinica1.psicoadmin.xyz`
4. Render te dará instrucciones de DNS
5. Agregar CNAME en tu proveedor DNS:
   ```
   clinica1.psicoadmin.xyz → clinicadental-backend.onrender.com
   ```
6. Esperar certificado SSL (automático, 5-15 min)

### **Opción 2: Crear Segunda Clínica**

Puedes ejecutar este script Python en el Shell:

```python
from apps.comun.models_tenant import Clinica, Dominio

# Crear clínica 2
clinica2 = Clinica.objects.create(
    schema_name='clinica2',
    nombre='Clínica Dental Sur',
    nit='9876543210',
    direccion='Av. Cristo Redentor #789',
    telefono='3-3334455',
    email='contacto@clinica2.psicoadmin.xyz',
    activo=True
)

# Registrar dominios
Dominio.objects.create(
    domain='clinica2.psicoadmin.xyz',
    tenant=clinica2,
    is_primary=True
)

print(f"✅ Clínica creada: {clinica2.nombre}")
```

---

## ❓ Solución de Problemas

### **Problema: "ModuleNotFoundError: No module named 'apps.comun.models_tenant'"**

**Solución:**
```bash
# Verifica que el archivo exista
ls apps/comun/models_tenant.py

# Si no existe, crea el archivo con los modelos Clinica y Dominio
```

### **Problema: "relation 'public.comun_clinica' does not exist"**

**Solución:**
```bash
# Ejecutar migraciones manualmente
python manage.py migrate_schemas --shared
```

### **Problema: "IntegrityError: duplicate key value"**

**Causa:** El script ya se ejecutó antes.

**Solución:**
```bash
# Eliminar datos anteriores (CUIDADO: borra todo)
python manage.py shell
>>> from apps.comun.models_tenant import Clinica, Dominio
>>> Clinica.objects.filter(schema_name='clinica1').delete()
>>> exit()

# Ejecutar de nuevo
python seed_render.py
```

---

## 🎉 Resultado Final

Después de completar estos pasos:

✅ Base de datos poblada con:
- 1 tenant público
- 1 clínica operativa (clinica1)
- 10 usuarios (admin + odontólogos + recepcionista + pacientes)
- 10 servicios odontológicos
- 3 citas de ejemplo
- Inventario básico

✅ API funcionando en:
- `https://clinicadental-backend.onrender.com` (público)
- `https://clinica1.psicoadmin.xyz` (clínica 1, después de DNS)

✅ Sin más errores 404

---

## 📞 Soporte

Si tienes problemas:
1. Revisa los **logs** en Render Dashboard
2. Verifica que las **migraciones** estén aplicadas
3. Comprueba que la **DATABASE_URL** esté configurada

**Comando útil para debugging:**
```bash
# Ver tenants creados
python manage.py shell
>>> from apps.comun.models_tenant import Clinica, Dominio
>>> print(Clinica.objects.all())
>>> print(Dominio.objects.all())
```

---

**¡Listo para producción! 🚀**
