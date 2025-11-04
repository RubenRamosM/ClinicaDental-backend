# 🦷 Sistema de Gestión de Clínica Dental - Backend

Sistema completo de gestión para clínicas dentales desarrollado con Django REST Framework y PostgreSQL.

## 📋 Características Principales

### 👥 Gestión de Usuarios
- Sistema de autenticación con tokens JWT
- 4 roles: Administrador, Odontólogo, Recepcionista, Paciente
- Permisos granulares por rol
- Auditoría automática de acciones

### 📅 Sistema de Citas
- Agendamiento de citas por pacientes
- Gestión de horarios disponibles por odontólogo
- Tipos de consulta configurables
- Estados de cita (Pendiente, Confirmada, En Consulta, Completada, Cancelada, No Asistió)
- Filtrado automático de horarios ocupados

### 🏥 Gestión Clínica
- Historial clínico de pacientes
- Odontograma digital
- Planes de tratamiento con procedimientos
- Sesiones de tratamiento
- Evolución y seguimiento

### 💰 Sistema de Pagos
- Registro de pagos por sesión
- Métodos de pago configurables
- Tracking de deudas y saldos
- Reportes de ingresos

### 📦 Inventario
- Gestión de productos y materiales
- Control de stock
- Alertas de stock mínimo
- Categorías de productos

### 👨‍⚕️ Profesionales
- Perfiles de odontólogos
- Especialidades
- Horarios de atención
- Asignación de pacientes

## 🛠️ Tecnologías

- **Framework:** Django 4.2 + Django REST Framework 3.14
- **Base de Datos:** PostgreSQL 14+
- **Autenticación:** Token-based (DRF Token Auth)
- **API:** RESTful API
- **Documentación:** OpenAPI/Swagger (auto-generada)

## 📁 Estructura del Proyecto

```
ClinicaDental-backend/
├── apps/
│   ├── administracion_clinica/   # Servicios, configuración general
│   ├── auditoria/                # Log de acciones
│   ├── autenticacion/            # Login, logout, tokens
│   ├── citas/                    # Consultas y horarios
│   ├── comun/                    # Modelos base, permisos, utils
│   ├── historial_clinico/        # Fichas clínicas, odontogramas
│   ├── inventario/               # Productos, stock
│   ├── profesionales/            # Odontólogos, recepcionistas
│   ├── sistema_pagos/            # Pagos, métodos de pago
│   ├── tratamientos/             # Planes, procedimientos, sesiones
│   └── usuarios/                 # Usuarios, pacientes, tipos
├── config/
│   ├── settings.py               # Configuración principal
│   ├── urls.py                   # URLs raíz
│   └── url_patterns.py           # Patrones de URL organizados
├── docs/                         # Documentación adicional
├── logs/                         # Logs de aplicación
├── media/                        # Archivos subidos
└── requirements.txt              # Dependencias Python
```

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone <url-repositorio>
cd ClinicaDental-backend
```

### 2. Crear entorno virtual

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar base de datos

Crear base de datos PostgreSQL:

```sql
CREATE DATABASE clinica_dental;
CREATE USER clinica_user WITH PASSWORD 'tu_password';
GRANT ALL PRIVILEGES ON DATABASE clinica_dental TO clinica_user;
```

Configurar en `config/settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'clinica_dental',
        'USER': 'clinica_user',
        'PASSWORD': 'tu_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### 5. Ejecutar migraciones

```bash
python manage.py migrate
```

### 6. Crear superusuario

```bash
python manage.py createsuperuser
```

### 7. Poblar base de datos (opcional)

```bash
python seed_database.py
```

### 8. Ejecutar servidor

```bash
python manage.py runserver
```

API disponible en: `http://localhost:8000/api/v1/`

## 📚 Endpoints Principales

### Autenticación
- `POST /api/v1/autenticacion/login/` - Iniciar sesión
- `POST /api/v1/autenticacion/logout/` - Cerrar sesión
- `POST /api/v1/autenticacion/registro/` - Registrar paciente

### Usuarios
- `GET/POST /api/v1/usuarios/` - Listar/crear usuarios
- `GET/PUT/PATCH/DELETE /api/v1/usuarios/{id}/` - Detalle de usuario
- `GET /api/v1/usuarios/pacientes/` - Listar pacientes

### Profesionales
- `GET /api/v1/profesionales/odontologos/` - Listar odontólogos
- `GET /api/v1/profesionales/recepcionistas/` - Listar recepcionistas

### Citas
- `GET/POST /api/v1/citas/` - Listar/crear citas
- `GET /api/v1/citas/horarios/disponibles/` - Horarios disponibles
- `GET /api/v1/citas/tipos-consulta/` - Tipos de consulta

### Tratamientos
- `GET/POST /api/v1/tratamientos/planes/` - Planes de tratamiento
- `GET/POST /api/v1/tratamientos/procedimientos/` - Procedimientos
- `GET/POST /api/v1/tratamientos/sesiones/` - Sesiones

### Pagos
- `GET/POST /api/v1/pagos/` - Listar/registrar pagos
- `GET /api/v1/pagos/metodos/` - Métodos de pago

### Administración
- `GET /api/v1/administracion/servicios/` - Servicios de la clínica

## 🔐 Autenticación

El sistema usa autenticación basada en tokens:

```bash
# Login
POST /api/v1/autenticacion/login/
{
  "correoelectronico": "usuario@clinica.com",
  "password": "contraseña"
}

# Respuesta
{
  "token": "abc123...",
  "user": {...}
}

# Usar token en requests
Headers:
  Authorization: Token abc123...
```

## 👤 Roles y Permisos

### Administrador
- Acceso completo al sistema
- Gestión de usuarios
- Configuración general
- Reportes

### Odontólogo
- Ver y crear citas
- Gestión de pacientes asignados
- Historial clínico
- Planes de tratamiento
- Registrar procedimientos

### Recepcionista
- Agendar citas
- Gestión de pacientes
- Registro de pagos
- Consulta de horarios

### Paciente
- Agendar citas propias
- Ver historial clínico
- Ver planes de tratamiento
- Consultar pagos

## 🧪 Scripts Útiles

### Poblar base de datos de prueba
```bash
python seed_database.py
```

### Ejecutar flujo E2E
```bash
python ejecutar_flujo_e2e.py
```

### Generar documentación API
```bash
python generar_documentacion_api.py
```

### Ver auditoría
```bash
python ver_auditoria.py
```

### Verificar multi-tenancy
```bash
python verificar_multitenancy.py
```

## 📊 Modelos Principales

### Usuario
- Modelo personalizado extendiendo Django User
- Campos: nombre, apellido, correo, teléfono, dirección
- Relación con TipoUsuario (rol)

### Paciente
- Hereda de Usuario
- Campos adicionales: fecha_nacimiento, sexo, ocupación
- Relación con Consultas, Tratamientos

### Odontólogo
- Hereda de Usuario
- Especialidad
- Horarios de atención

### Consulta
- Fecha, horario
- Paciente, Odontólogo
- Tipo de consulta
- Estado de la consulta

### PlanTratamiento
- Paciente
- Fecha inicio/fin
- Estado
- Monto total
- Procedimientos asociados

### Pago
- Monto
- Fecha
- Método de pago
- Sesión de tratamiento asociada

## 🏗️ Multi-Tenancy

El sistema está **preparado para multi-tenancy** pero actualmente funciona como clínica única.

Ver documentación completa en: [`MULTITENANCY_PREPARACION.md`](./MULTITENANCY_PREPARACION.md)

### Estado Actual
- ✅ Settings configurados (localhost en desarrollo)
- ✅ CORS para subdominios locales (norte.localhost, sur.localhost, etc.)
- ✅ Modelos base preparados
- ✅ Managers comentados (listos)
- ✅ Permisos comentados (listos)
- ⏸️ App 'tenancy' pendiente de crear
- ⏸️ Middlewares pendientes

### Ejemplos de Subdominios
**Desarrollo (localhost):**
- http://localhost:8000 (sitio principal)
- http://norte.localhost:8000 (clínica Norte)
- http://sur.localhost:8000 (clínica Sur)
- http://este.localhost:8000 (clínica Este)
- http://oeste.localhost:8000 (clínica Oeste)

**Producción:**
- https://clinicadental.com (sitio principal)
- https://norte.clinicadental.com
- https://sur.clinicadental.com
- https://este.clinicadental.com
- https://oeste.clinicadental.com

### Activación
Tiempo estimado: 12-15 horas  
Ver plan detallado en documentación de multitenancy.

## 🔄 Auditoría

Todas las acciones importantes se registran automáticamente:

- Usuario que realizó la acción
- Timestamp
- Endpoint accedido
- Método HTTP
- IP del cliente
- Datos enviados (en algunos casos)

Ver auditoría: `python ver_auditoria.py`

## 📝 Documentación Adicional

- [`MULTITENANCY_PREPARACION.md`](./MULTITENANCY_PREPARACION.md) - Estado y plan de multitenancy
- [`README_PRUEBAS_E2E.md`](./README_PRUEBAS_E2E.md) - Guía de pruebas end-to-end
- `GUIA_*.md` - Guías específicas de implementación (frontend)

## 🐛 Testing

### Pruebas con archivos .http

Archivos en raíz:
- `api_tests.http` - Tests completos de API
- `test_admin.http` - Tests de administrador
- `test_odontologo.http` - Tests de odontólogo
- `test_paciente.http` - Tests de paciente
- `pruebas_flujo_completo.http` - Flujo E2E

Usar extensión REST Client en VS Code.

### Pruebas E2E

```bash
python ejecutar_flujo_e2e.py
```

## 🚨 Errores Comunes

### Error: Cannot read properties of undefined (reading 'nombre')
**Solución:** Verificar que serializers incluyan campos anidados necesarios.

### Error: 404 en endpoints
**Solución:** Verificar URLs en `config/url_patterns.py` y reiniciar Django.

### Error: 400 Bad Request con IDs
**Solución:** Verificar que IDs existan en BD (ej: idestadoconsulta debe ser 295, no 1).

## 🔧 Mantenimiento

### Limpiar logs antiguos
```bash
python manage.py clearlogs --days 30
```

### Backup de base de datos
```bash
python manage.py dumpdata > backup.json
```

### Restaurar backup
```bash
python manage.py loaddata backup.json
```

## 📞 Soporte

Para problemas o preguntas, revisar:
1. Esta documentación
2. Logs en `logs/`
3. Auditoría con `ver_auditoria.py`
4. Archivos de guía específicos

## 📄 Licencia

[Especificar licencia]

## 👨‍💻 Desarrollo

**Versión:** 1.0.0  
**Python:** 3.11+  
**Django:** 4.2+  
**PostgreSQL:** 14+

---

**Última actualización:** Noviembre 3, 2025
