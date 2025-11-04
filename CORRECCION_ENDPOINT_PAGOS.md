# Correcciones al Endpoint de Pagos en Línea

## Problema Identificado

El endpoint `GET /api/v1/pagos/pagos-online/` retornaba 404 Error, impidiendo que los pacientes puedan ver su historial de pagos. Este endpoint es crítico para la funcionalidad de Stripe ya que los pacientes necesitan ver la confirmación de sus pagos realizados.

## Root Cause Analysis

### 1. Problema de Routing (CRÍTICO - Ya Corregido)

**Archivo**: `apps/sistema_pagos/urls.py`

**Problema**: El router tenía registrado `PagoViewSet` con prefijo vacío (`r''`) **ANTES** de `PagoEnLineaViewSet` con prefijo `pagos-online`. Esto causaba que todas las peticiones fueran capturadas por el ViewSet vacío antes de llegar a `pagos-online`.

**Código Original (Incorrecto)**:
```python
router = DefaultRouter()
router.register(r'tipos-pago', views.TipopagoViewSet, basename='tipo-pago')
router.register(r'estados-factura', views.EstadodefacturaViewSet, basename='estado-factura')
router.register(r'facturas', views.FacturaViewSet, basename='factura')
router.register(r'', views.PagoViewSet, basename='pago')  # ❌ ANTES (captura todo)
router.register(r'pagos-online', views.PagoEnLineaViewSet, basename='pago-online')  # ❌ Nunca se alcanza
```

**Código Corregido**:
```python
router = DefaultRouter()
router.register(r'tipos-pago', views.TipopagoViewSet, basename='tipo-pago')
router.register(r'estados-factura', views.EstadodefacturaViewSet, basename='estado-factura')
router.register(r'facturas', views.FacturaViewSet, basename='factura')
router.register(r'pagos-online', views.PagoEnLineaViewSet, basename='pago-online')  # ✅ ANTES
# Registrar sin prefijo para que las acciones estén en /api/v1/pagos/pendientes/ etc
# IMPORTANTE: Debe ir al final para que no capture las rutas anteriores
router.register(r'', views.PagoViewSet, basename='pago')  # ✅ AL FINAL
```

**Justificación**: Los routers de DRF procesan las rutas en orden de registro. Un prefijo vacío captura TODAS las peticiones, por lo que debe ir al final.

### 2. Problema de Permisos/Filtrado (Ya Corregido)

**Archivo**: `apps/sistema_pagos/views.py`

**Problema**: El `PagoEnLineaViewSet` mostraba TODOS los pagos a TODOS los usuarios sin filtrar por usuario autenticado.

**Código Original (Incorrecto)**:
```python
class PagoEnLineaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para pagos en línea.
    
    GET /api/v1/pagos/pagos-online/
    """
    queryset = PagoEnLinea.objects.all()  # ❌ Todos los pagos para todos
    serializer_class = PagoEnLineaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['estado', 'metodo_pago']
    ordering_fields = ['fecha_creacion']
    ordering = ['-fecha_creacion']
```

**Código Corregido**:
```python
class PagoEnLineaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para pagos en línea.
    
    GET /api/v1/pagos/pagos-online/
    """
    serializer_class = PagoEnLineaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['estado', 'metodo_pago']
    ordering_fields = ['fecha_creacion']
    ordering = ['-fecha_creacion']

    def get_queryset(self):
        """
        Filtra pagos según el tipo de usuario:
        - Pacientes: solo sus propios pagos (a través de consulta.codpaciente.codusuario)
        - Administradores/Odontólogos: todos los pagos
        """
        user = self.request.user
        
        # Verificar si el usuario tiene perfil de paciente
        if hasattr(user, 'paciente'):
            # Filtrar solo pagos del paciente autenticado
            return PagoEnLinea.objects.filter(
                consulta__codpaciente__codusuario=user
            ).select_related('consulta', 'consulta__codpaciente', 'consulta__cododontologo')
        
        # Si es admin u odontólogo, mostrar todos los pagos
        return PagoEnLinea.objects.all().select_related('consulta', 'consulta__codpaciente', 'consulta__cododontologo')
```

**Justificación**: 
- Los pacientes solo deben ver sus propios pagos (privacidad)
- Admin/Odontólogos necesitan ver todos los pagos (gestión)
- La relación es: `PagoEnLinea → consulta (FK) → codpaciente (FK) → codusuario (OneToOne) → Usuario`
- `select_related()` optimiza la query reduciendo queries adicionales

## Cadena de Relaciones del Modelo

```
PagoEnLinea.consulta 
    → Consulta.codpaciente 
        → Paciente.codusuario (OneToOne)
            → Usuario (request.user)
```

**Verificación**:
- `hasattr(user, 'paciente')` → True si el usuario tiene perfil de paciente
- `consulta__codpaciente__codusuario=user` → Filtra pagos donde la consulta pertenece al usuario autenticado

## Resultado Esperado

Después de estas correcciones:

### Para Pacientes:
```http
GET /api/v1/pagos/pagos-online/
Authorization: Token {token_paciente}

Response: 200 OK
[
  {
    "id": 13,
    "codigo_pago": "CITA-FA21EB4B",
    "monto": 100.00,
    "moneda": "BOB",
    "estado": "aprobado",
    "consulta": {
      "id": 449,
      "fecha": "2025-11-10",
      ...
    },
    ...
  }
]
```

### Para Admin:
```http
GET /api/v1/pagos/pagos-online/
Authorization: Token {token_admin}

Response: 200 OK
[
  ... todos los pagos de todos los pacientes ...
]
```

## Testing

### Test Manual (HTTP):
```http
### 1. Login como paciente
POST http://127.0.0.1:8000/api/v1/auth/login/
Content-Type: application/json

{
  "correo": "ana.lopez@email.com",
  "password": "paciente123"
}

### 2. Listar pagos del paciente
GET http://127.0.0.1:8000/api/v1/pagos/pagos-online/
Authorization: Token {{token}}
```

### Test con Flujo 09:
```bash
cd pruebas_py
python flujo_09_stripe.py
```

La Sección 7 del Flujo 09 ahora debería pasar exitosamente.

## Archivos Modificados

1. ✅ `apps/sistema_pagos/urls.py` - Reordenado registro de routers
2. ✅ `apps/sistema_pagos/views.py` - Agregado método `get_queryset()` con filtrado por usuario

## Impacto en Flujo 09

**Antes**: 
- Sección 7: ❌ Falla (404 Error)
- Tasa de éxito: 71.43% (5/7)

**Después**: 
- Sección 7: ✅ Debería pasar
- Tasa de éxito esperada: 85.71% (6/7) o 100% (7/7) si se corrige la Sección 6

## Problemas Pendientes

1. **Flujo 09 Sección 6**: La verificación de vinculación muestra `consulta_id: null` en el response de creación de cita, aunque en la base de datos el ID 449 existe correctamente. Esto puede ser un problema del serializer que no retorna el ID en la respuesta.

2. **Virtual Environment**: Existe un problema con `pyvenv.cfg` que impide ejecutar comandos de Python. Este es un problema del entorno, no del código, y debe ser reparado recreando el virtual environment.

## Comandos de Verificación

Una vez que el servidor esté corriendo con los cambios aplicados:

```powershell
# Test rápido con PowerShell
$body = '{"correo":"ana.lopez@email.com","password":"paciente123"}'
$response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/v1/auth/login/" -Method POST -ContentType "application/json" -Body $body
$token = ($response.Content | ConvertFrom-Json).token
$headers = @{Authorization="Token $token"}
$pagos = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/v1/pagos/pagos-online/" -Headers $headers
Write-Host "Status: $($pagos.StatusCode)"
$pagos.Content | ConvertFrom-Json | Format-List
```

## Próximos Pasos

1. Reparar el virtual environment (`.venv`) del backend
2. Reiniciar el servidor Django
3. Re-ejecutar Flujo 09 completo
4. Verificar que Sección 7 ahora pasa exitosamente
5. Investigar Sección 6 (consulta_id null en response)
