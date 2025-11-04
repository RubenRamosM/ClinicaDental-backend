# 🏢 Estado de Preparación Multi-Tenancy

**Fecha de verificación:** 3 de Noviembre, 2025  
**Estado:** ✅ PREPARADO PERO NO IMPLEMENTADO

---

## 📊 Resumen Ejecutivo

El proyecto **está preparado para Multi-Tenancy** pero actualmente funciona como **clínica única**. Todos los componentes necesarios están diseñados y comentados, listos para activar cuando sea necesario.

### ✅ Componentes Preparados

1. **Settings configurados**
   - `SAAS_BASE_DOMAIN = "localhost"` (desarrollo) / `"clinicadental.com"` (producción)
   - `SAAS_PUBLIC_URL = "http://localhost:8000"` (desarrollo)
   - CORS configurado para subdominios: `^http://[\w-]+\.localhost:\d+$`
   - Header `x-tenant-subdomain` permitido

2. **Modelos Base Listos**
   - `ModeloPreparadoMultiClinica` creado en `apps/comun/models.py`
   - Campo `clinica` comentado, listo para descomentar
   - Documentación clara con TODOs

3. **Managers Preparados**
   - `QuerySetMultiClinica` comentado
   - `ManagerMultiClinica` comentado
   - Filtros por clínica implementados pero desactivados

4. **Permisos Preparados**
   - `EsMismaClinica` comentado
   - Lógica de verificación de clínica lista

5. **URL Patterns Separados**
   - `urlpatterns_public` - Endpoints públicos
   - `urlpatterns_tenant` - Endpoints por tenant

---

## ⏸️ Componentes Pendientes

### 1. App 'tenancy'

**Estado:** NO EXISTE  
**Prioridad:** ALTA  

Crear app con:

```python
# apps/tenancy/models.py
class Clinica(ModeloConFechas):
    """
    Modelo para representar una clínica en el sistema multi-tenant.
    """
    nombre = models.CharField(max_length=200)
    subdominio = models.SlugField(max_length=50, unique=True)
    activo = models.BooleanField(default=True)
    logo = models.ImageField(upload_to='clinicas/logos/', null=True, blank=True)
    
    # Datos de contacto
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    direccion = models.TextField(blank=True)
    
    # Configuración
    timezone = models.CharField(max_length=50, default='America/La_Paz')
    
    class Meta:
        db_table = 'clinica'
        verbose_name = 'Clínica'
        verbose_name_plural = 'Clínicas'
    
    def __str__(self):
        return self.nombre
```

### 2. Middlewares

**Estado:** COMENTADOS EN SETTINGS, ARCHIVOS NO EXISTEN  
**Prioridad:** ALTA

#### a) `config/middleware_routing.py`

```python
class TenantRoutingMiddleware:
    """
    Detecta el tenant desde el subdominio y lo asigna al request.
    """
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Extraer subdominio
        host = request.get_host().split(':')[0]
        subdomain = self._extract_subdomain(host)
        
        if subdomain:
            # Buscar clinica por subdominio
            from apps.tenancy.models import Clinica
            try:
                request.tenant = Clinica.objects.get(
                    subdominio=subdomain, 
                    activo=True
                )
            except Clinica.DoesNotExist:
                request.tenant = None
        else:
            request.tenant = None
        
        return self.get_response(request)
    
    def _extract_subdomain(self, host):
        from django.conf import settings
        base_domain = settings.SAAS_BASE_DOMAIN
        
        # En desarrollo: norte.localhost → 'norte'
        # En producción: norte.clinicadental.com → 'norte'
        if host.endswith(base_domain) and host != base_domain:
            return host.replace(f'.{base_domain}', '')
        return None
```

#### b) `api/middleware_tenant.py`

```python
class TenantMiddleware:
    """
    Inyecta el tenant en thread local para acceso global.
    """
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        from threading import local
        _thread_locals = local()
        
        if hasattr(request, 'tenant'):
            _thread_locals.tenant = request.tenant
        
        response = self.get_response(request)
        
        if hasattr(_thread_locals, 'tenant'):
            delattr(_thread_locals, 'tenant')
        
        return response
```

#### c) `api/middleware_admin_diagnostic.py`

```python
class AdminTenantDiagnosticMiddleware:
    """
    Muestra información de debugging para superadmins.
    """
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        if request.user.is_superuser:
            tenant_info = getattr(request, 'tenant', None)
            if tenant_info:
                response['X-Tenant-Debug'] = str(tenant_info.nombre)
        
        return response
```

### 3. Activación en Modelos

**Estado:** COMENTADO  
**Prioridad:** MEDIA

En cada modelo que necesite multi-tenancy, descomentar:

```python
# apps/comun/models.py
class ModeloPreparadoMultiClinica(ModeloConFechas):
    
    clinica = models.ForeignKey(  # ← DESCOMENTAR
        'tenancy.Clinica',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        db_index=True,
        related_name='%(class)s_set',
    )
```

Y hacer que los modelos de las apps hereden de `ModeloPreparadoMultiClinica`:

```python
# Ejemplo: apps/citas/models.py
from apps.comun.models import ModeloPreparadoMultiClinica

class Consulta(ModeloPreparadoMultiClinica):  # ← Cambiar a este modelo base
    # ... resto del código
```

### 4. Activación de Managers

**Estado:** COMENTADO  
**Prioridad:** MEDIA

```python
# apps/comun/managers.py
# Descomentar QuerySetMultiClinica y ManagerMultiClinica

# Luego usar en modelos:
class Consulta(ModeloPreparadoMultiClinica):
    objects = ManagerMultiClinica()  # ← Agregar
    # ...
```

### 5. Activación de Permisos

**Estado:** COMENTADO  
**Prioridad:** BAJA

```python
# apps/comun/permisos.py
# Descomentar EsMismaClinica

# Usar en viewsets:
class ConsultaViewSet(viewsets.ModelViewSet):
    permission_classes = [
        permissions.IsAuthenticated,
        EsMismaClinica,  # ← Agregar
    ]
```

### 6. Activación en Settings

**Estado:** COMENTADO  
**Prioridad:** ALTA

```python
# config/settings.py
MIDDLEWARE = [
    # ... middlewares existentes ...
    "config.middleware_routing.TenantRoutingMiddleware",  # ← DESCOMENTAR
    "api.middleware_tenant.TenantMiddleware",  # ← DESCOMENTAR
    "api.middleware_admin_diagnostic.AdminTenantDiagnosticMiddleware",  # ← DESCOMENTAR
]

INSTALLED_APPS = [
    # ... apps existentes ...
    'apps.tenancy',  # ← AGREGAR
]
```

---

## 🚀 Plan de Activación (Cuando sea Necesario)

### Fase 1: Preparación (2-3 horas)

1. ✅ Crear app `tenancy`
2. ✅ Crear modelo `Clinica`
3. ✅ Crear middlewares (3 archivos)
4. ✅ Registrar app en `INSTALLED_APPS`

### Fase 2: Migraciones (1 hora)

5. ✅ Ejecutar `python manage.py makemigrations tenancy`
6. ✅ Ejecutar `python manage.py migrate`
7. ✅ Crear clínica inicial desde admin

### Fase 3: Activación Gradual (3-4 horas)

8. ✅ Descomentar campo `clinica` en `ModeloPreparadoMultiClinica`
9. ✅ Migrar modelos críticos a heredar de `ModeloPreparadoMultiClinica`:
   - `Consulta` (citas)
   - `Usuario` (usuarios)
   - `Paciente` (profesionales)
   - `Odontologo` (profesionales)
   - `Servicio` (administracion_clinica)
10. ✅ Ejecutar migraciones para agregar campo `clinica`
11. ✅ Asignar clínica a datos existentes (script de migración)

### Fase 4: Managers y Permisos (2 horas)

12. ✅ Descomentar managers en `apps/comun/managers.py`
13. ✅ Asignar `ManagerMultiClinica` a modelos relevantes
14. ✅ Descomentar `EsMismaClinica` en permisos
15. ✅ Agregar permiso a viewsets

### Fase 5: Middlewares (1 hora)

16. ✅ Descomentar middlewares en `settings.py`
17. ✅ Probar con subdominio de prueba
18. ✅ Verificar filtrado por clínica

### Fase 6: Testing y Validación (2-3 horas)

19. ✅ Crear segunda clínica de prueba
20. ✅ Verificar aislamiento de datos
21. ✅ Probar accesos cruzados (deben fallar)
22. ✅ Ajustes finales

**Total estimado:** 12-15 horas

---

## 🔧 Modelos que Necesitan Multitenancy

### Alta Prioridad (Datos core)

- ✅ `Consulta` (apps/citas)
- ✅ `Paciente` (apps/profesionales)
- ✅ `Odontologo` (apps/profesionales)
- ✅ `Recepcionista` (apps/profesionales)
- ✅ `Usuario` (apps/usuarios)
- ✅ `Servicio` (apps/administracion_clinica)
- ✅ `Tratamiento` (apps/tratamientos)

### Media Prioridad

- ✅ `Horario` (apps/citas)
- ✅ `HistorialClinico` (apps/historial_clinico)
- ✅ `Pago` (apps/sistema_pagos)
- ✅ `Producto` (apps/inventario)

### Baja Prioridad (Datos compartibles)

- `Tipoconsulta` (puede ser global o por clínica)
- `Estadoconsulta` (puede ser global)
- `Tipousuario` (puede ser global)

---

## 📝 Archivos Clave

### Modificar

- ✅ `apps/comun/models.py` - Descomentar campo clinica
- ✅ `apps/comun/managers.py` - Descomentar managers
- ✅ `apps/comun/permisos.py` - Descomentar EsMismaClinica
- ✅ `config/settings.py` - Descomentar middlewares

### Crear

- ⏸️ `apps/tenancy/` - Nueva app completa
- ⏸️ `config/middleware_routing.py`
- ⏸️ `api/middleware_tenant.py`
- ⏸️ `api/middleware_admin_diagnostic.py`

---

## ✅ Ventajas de la Preparación Actual

1. **Sin Deuda Técnica:** Cuando se active, solo descomentar código
2. **Retrocompatible:** Funciona perfectamente como clínica única
3. **Documentado:** TODOs claros en todos los archivos
4. **CORS Listo:** Ya acepta subdominios
5. **Headers Configurados:** `x-tenant-subdomain` permitido
6. **URL Patterns Separados:** Fácil diferenciar público/tenant

---

## 🎯 Estado Actual: ÓPTIMO

El sistema funciona como **clínica única** pero está **arquitectónicamente preparado** para multi-tenancy. No hay código innecesario activo, solo estructuras comentadas esperando ser activadas.

**Tiempo estimado de activación:** 12-15 horas de trabajo técnico + testing.

**Riesgo de activación:** BAJO (todo está preparado y documentado)

---

## 📞 Contacto para Activación

Cuando decidas activar multi-tenancy, sigue el "Plan de Activación" paso a paso. Todos los componentes necesarios están identificados y listos.

---

**Última verificación:** Script `verificar_multitenancy.py`  
**Próxima revisión:** Cuando se planifique implementar multi-tenancy
