# 🧪 Pruebas Automatizadas - Scripts Python

Este directorio contiene scripts de pruebas automatizadas para el backend de la clínica dental.

## 📋 Descripción

Los scripts están organizados por flujos (flows) que representan diferentes funcionalidades del sistema. Cada script ejecuta un conjunto de pruebas relacionadas y muestra el resultado en formato detallado similar al **Network tab de DevTools** del navegador.

## 🎯 Características

- **Output Descriptivo**: Muestra request y response completos con análisis de tipos
- **Colores y Formato**: Usa Rich para output bonito con colores y sintaxis JSON
- **Ejecución 1x1**: Un flujo a la vez para minimizar errores
- **Análisis de Tipos**: Identifica si los datos son object, array, string, etc.
- **Información Completa**: Headers, body, status codes, todo visible

## 📁 Estructura

```
pruebas_py/
├── http_logger.py                 # Helper para logging HTTP detallado
├── flujo_00_seeder.py            # Verificación de datos del seeder ✅
├── flujo_01_autenticacion.py     # Login, logout, perfiles ✅
├── flujo_02_citas.py             # CRUD de citas ✅
├── flujo_03_historiales.py       # Historiales clínicos ✅
├── flujo_04_tratamientos.py      # Tratamientos y presupuestos ✅
├── flujo_05_facturacion.py       # Facturas y pagos ✅
├── flujo_06_respaldos.py         # Respaldos de base de datos (requiere fix clinica_id) ⚠️
├── flujo_07_chatbot.py           # Chatbot inteligente ✅
├── ejecutar_prueba.ps1           # Script PowerShell para ejecutar fácilmente
└── requirements_pruebas.txt      # Dependencias necesarias
```

## 🚀 Instalación

### 1. Instalar dependencias:

```powershell
# Opción A: Usando pip directamente
pip install -r pruebas_py/requirements_pruebas.txt

# Opción B: Usando el Python global (si .venv está corrupto)
& "C:\Users\asus\AppData\Local\Programs\Python\Python313\python.exe" -m pip install -r pruebas_py/requirements_pruebas.txt
```

### 2. Asegúrate de que el servidor Django esté corriendo:

```powershell
python manage.py runserver

# O con Python global:
& "C:\Users\asus\AppData\Local\Programs\Python\Python313\python.exe" manage.py runserver
```

### 3. Asegúrate de que la base de datos tenga datos de prueba:

```powershell
python seed_database.py --force

# O con Python global:
& "C:\Users\asus\AppData\Local\Programs\Python\Python313\python.exe" seed_database.py --force
```

## 📝 Uso

### Ejecutar un flujo específico:

```powershell
# Navegar al directorio de pruebas
cd pruebas_py

# Ejecutar flujo de seeder
python flujo_00_seeder.py

# O con Python global:
& "C:\Users\asus\AppData\Local\Programs\Python\Python313\python.exe" flujo_00_seeder.py
```

### Orden recomendado de ejecución:

1. **flujo_00_seeder.py** - Verifica que el seeder funcionó correctamente
2. **flujo_01_autenticacion.py** - Prueba login/logout/perfiles
3. **flujo_02_citas.py** - CRUD de citas
4. **flujo_03_historiales.py** - Historiales clínicos
5. **flujo_04_tratamientos.py** - Tratamientos y presupuestos
6. **flujo_05_facturacion.py** - Facturas y pagos
7. **flujo_06_respaldos.py** - Sistema de respaldos
8. **flujo_07_chatbot.py** - Chatbot inteligente

## 🎨 Formato de Output

Cada prueba muestra:

### 📤 REQUEST
- **Método HTTP**: GET, POST, PUT, DELETE, etc.
- **URL completa**: Endpoint al que se hace la petición
- **Headers**: Todos los headers enviados
- **Body**: Cuerpo de la petición con tipo identificado (object, array, string)

### 📥 RESPONSE
- **Status Code**: Con colores (verde=200s, rojo=errores)
- **Headers**: Headers de la respuesta
- **Body**: Respuesta del servidor con tipo identificado
- **Análisis**: Cantidad de elementos, propiedades, longitud, etc.

### Ejemplo de output:

```
═══ Login como Admin ═══

📤 REQUEST
POST http://localhost:8000/api/v1/auth/login/

Headers:
Content-Type: application/json

Body Type: object (2 propiedades)
┌─ Request Body ─────────────────┐
│ {                              │
│   "correo": "admin@clinica.com"│
│   "password": "admin123"       │
│ }                              │
└────────────────────────────────┘

📥 RESPONSE
✅ Status: 200

Body Type: object (3 propiedades)
┌─ Response Body ────────────────┐
│ {                              │
│   "mensaje": "Login exitoso",  │
│   "usuario": {...},            │
│   "token": "abc123..."         │
│ }                              │
└────────────────────────────────┘
```

## 🔧 Helper Module: http_logger.py

Proporciona funciones para logging detallado:

- **print_http_transaction()**: Imprime request/response completo
- **print_seccion()**: Título de sección
- **print_exito()**: Mensaje de éxito (verde)
- **print_error()**: Mensaje de error (rojo)
- **print_warning()**: Mensaje de advertencia (amarillo)
- **print_info()**: Mensaje informativo (cyan)
- **analizar_tipo()**: Analiza tipo de dato (object, array, string, etc.)

## 📊 Datos de Prueba del Seeder

### Usuarios disponibles:

| Rol | Correo | Password |
|-----|--------|----------|
| Admin | admin@clinica.com | admin123 |
| Odontólogo | dr.perez@clinica.com | odontologo123 |
| Paciente | ana.lopez@email.com | paciente123 |

## ⚠️ Notas Importantes

1. **Servidor debe estar corriendo**: Los scripts requieren que Django esté en http://localhost:8000
2. **Base de datos debe tener datos**: Ejecuta `seed_database.py --force` antes de las pruebas
3. **Python global vs .venv**: Si tu .venv está corrupto, usa el Python global con la ruta completa
4. **Orden de ejecución**: Ejecuta flujo_00 primero para verificar que todo está listo

## 🐛 Troubleshooting

### Error: "ModuleNotFoundError: No module named 'requests'"
```powershell
pip install -r pruebas_py/requirements_pruebas.txt
```

### Error: "ConnectionRefusedError"
- Asegúrate de que Django esté corriendo: `python manage.py runserver`

### Error: Login falla con 400
- Verifica que ejecutaste `seed_database.py --force`
- Revisa que los datos de login sean correctos

## 📚 Flujos Disponibles

- [x] **Flujo 00**: Verificación de seeder ✅
- [x] **Flujo 01**: Autenticación (login, logout, perfiles) ✅
- [x] **Flujo 02**: Gestión de citas ✅
- [x] **Flujo 03**: Historiales clínicos ✅
- [x] **Flujo 04**: Tratamientos y presupuestos ✅
- [x] **Flujo 05**: Facturación y pagos ✅
- [ ] **Flujo 06**: Respaldos en la nube (requiere fix de clinica_id en User) ⚠️
- [x] **Flujo 07**: Chatbot inteligente ✅

---

**Autor**: Sistema de Pruebas Automatizadas - Clínica Dental  
**Última actualización**: 2025
