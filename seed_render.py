"""
Script Poblador para Render - Clínica Dental
=============================================

Crea la clínica principal y puebla todos los datos de prueba.
Compatible con Render (PostgreSQL en la nube).

Ejecución en Render Shell:
    python seed_render.py

Características:
- ✅ Crea tenant "public" si no existe
- ✅ Crea clínica principal "clinica1" 
- ✅ Registra dominios (Render + psicoadmin.xyz)
- ✅ Puebla datos de prueba completos
"""

import os
import django
import sys
from datetime import datetime, timedelta, date
from decimal import Decimal

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from django.db import transaction, connection
from rest_framework.authtoken.models import Token

# Importar modelos SHARED (multi-tenancy)
from apps.comun.models_tenant import Clinica, Dominio

# Importar modelos TENANT
from apps.usuarios.models import Tipodeusuario, Usuario, Paciente
from apps.profesionales.models import Odontologo, Recepcionista
from apps.citas.models import Horario, Estadodeconsulta, Tipodeconsulta, Consulta
from apps.administracion_clinica.models import Servicio, ComboServicio, ComboServicioDetalle
from apps.historial_clinico.models import (
    Historialclinico, DocumentoClinico, Odontograma, 
    TratamientoOdontologico, ConsentimientoInformado
)
from apps.historial_clinico.models_inventario import (
    CategoriaInsumo, Proveedor, Insumo, MovimientoInventario, AlertaInventario
)
from apps.tratamientos.models import (
    PlanTratamiento, Presupuesto, ItemPresupuesto, 
    Procedimiento, HistorialPago, SesionTratamiento
)
from apps.sistema_pagos.models import Tipopago, Estadodefactura, Factura, Itemdefactura, Pago
from apps.auditoria.models import Bitacora
from apps.autenticacion.models import BloqueoUsuario


def print_section(title):
    """Imprime un título de sección"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def crear_tenant_public():
    """Crea el tenant público (shared schema) si no existe"""
    print_section("🏢 CONFIGURANDO TENANT PÚBLICO")
    
    # Verificar si ya existe
    if Clinica.objects.filter(schema_name='public').exists():
        public_tenant = Clinica.objects.get(schema_name='public')
        print("✅ Tenant público ya existe")
        print(f"   - Nombre: {public_tenant.nombre}")
        print(f"   - RUC: {public_tenant.ruc}")
        return public_tenant
    
    # Crear tenant público
    public_tenant = Clinica.objects.create(
        schema_name='public',
        nombre='Sistema Central',
        ruc='0000000000',
        direccion='Santa Cruz, Bolivia',
        telefono='00000000',
        email='sistema@psicoadmin.xyz',
        admin_nombre='Administrador Sistema',
        admin_email='admin@psicoadmin.xyz',
        activa=True,
        plan='empresarial'
    )
    
    # Crear dominio para el tenant público (Render)
    Dominio.objects.create(
        domain='clinicadental-backend.onrender.com',
        tenant=public_tenant,
        is_primary=True
    )
    
    print("✅ Tenant público creado")
    print(f"   - Schema: {public_tenant.schema_name}")
    print(f"   - Dominio: clinicadental-backend.onrender.com")
    
    return public_tenant


def crear_clinica_principal():
    """Crea la clínica principal (primer tenant real)"""
    print_section("🏥 CREANDO CLÍNICA PRINCIPAL")
    
    # Verificar si ya existe
    if Clinica.objects.filter(schema_name='clinica1').exists():
        clinica = Clinica.objects.get(schema_name='clinica1')
        print("✅ Clínica principal ya existe")
        print(f"   - Nombre: {clinica.nombre}")
        print(f"   - Schema: {clinica.schema_name}")
        return clinica
    
    # Crear clínica
    clinica = Clinica.objects.create(
        schema_name='clinica1',
        nombre='Clínica Dental Norte',
        ruc='1234567890',
        direccion='Av. San Martin #456, Santa Cruz',
        telefono='3-3456789',
        email='contacto@clinica1.psicoadmin.xyz',
        admin_nombre='Dr. Juan Pérez',
        admin_email='admin@clinica1.psicoadmin.xyz',
        admin_telefono='70000000',
        activa=True,
        plan='profesional',
        max_usuarios=20,
        max_pacientes=500
    )
    
    # Crear dominios
    # 1. Dominio en Render (para testing inicial)
    Dominio.objects.create(
        domain='clinica1.onrender.com',
        tenant=clinica,
        is_primary=False
    )
    
    # 2. Dominio en psicoadmin.xyz (producción)
    Dominio.objects.create(
        domain='clinica1.psicoadmin.xyz',
        tenant=clinica,
        is_primary=True
    )
    
    print("✅ Clínica principal creada")
    print(f"   - Nombre: {clinica.nombre}")
    print(f"   - Schema: {clinica.schema_name}")
    print(f"   - RUC: {clinica.ruc}")
    print(f"   - Dominios:")
    print(f"     • clinica1.onrender.com")
    print(f"     • clinica1.psicoadmin.xyz (principal)")
    
    return clinica


def poblar_datos_clinica(clinica):
    """Puebla datos de prueba en el schema de la clínica"""
    print_section(f"📊 POBLANDO DATOS - {clinica.nombre}")
    
    # Cambiar al schema de la clínica
    connection.set_tenant(clinica)
    print(f"✓ Conectado al schema: {clinica.schema_name}")
    
    # ==================== DATOS BASE ====================
    print("\n📋 Creando datos base...")
    
    # Tipos de Usuario
    tipo_admin = Tipodeusuario.objects.create(
        id=1, rol='Administrador',
        descripcion='Usuario administrador del sistema'
    )
    tipo_odontologo = Tipodeusuario.objects.create(
        id=2, rol='Odontólogo',
        descripcion='Profesional odontólogo'
    )
    tipo_recepcionista = Tipodeusuario.objects.create(
        id=3, rol='Recepcionista',
        descripcion='Personal de recepción'
    )
    tipo_paciente = Tipodeusuario.objects.create(
        id=4, rol='Paciente',
        descripcion='Paciente de la clínica'
    )
    
    # Horarios (8:00 AM - 6:00 PM cada 30 minutos)
    horarios = []
    for hour in range(8, 18):
        for minute in [0, 30]:
            horario = Horario.objects.create(hora=f"{hour:02d}:{minute:02d}:00")
            horarios.append(horario)
    
    # Estados de Consulta
    estados = {
        'pendiente': Estadodeconsulta.objects.create(id=1, estado='Pendiente'),
        'confirmada': Estadodeconsulta.objects.create(id=2, estado='Confirmada'),
        'en_consulta': Estadodeconsulta.objects.create(id=3, estado='En Consulta'),
        'completada': Estadodeconsulta.objects.create(id=4, estado='Completada'),
        'cancelada': Estadodeconsulta.objects.create(id=5, estado='Cancelada'),
        'no_asistio': Estadodeconsulta.objects.create(id=6, estado='No Asistió'),
    }
    
    # Tipos de Consulta
    tipos_consulta = {
        'primera_vez': Tipodeconsulta.objects.create(
            id=1, nombreconsulta='Primera Vez',
            permite_agendamiento_web=True, requiere_aprobacion=False,
            es_urgencia=False, duracion_estimada=60
        ),
        'control': Tipodeconsulta.objects.create(
            id=2, nombreconsulta='Control',
            permite_agendamiento_web=True, requiere_aprobacion=False,
            es_urgencia=False, duracion_estimada=30
        ),
        'tratamiento': Tipodeconsulta.objects.create(
            id=3, nombreconsulta='Tratamiento',
            permite_agendamiento_web=False, requiere_aprobacion=True,
            es_urgencia=False, duracion_estimada=90
        ),
        'urgencia': Tipodeconsulta.objects.create(
            id=4, nombreconsulta='Urgencia',
            permite_agendamiento_web=True, requiere_aprobacion=False,
            es_urgencia=True, duracion_estimada=45
        ),
    }
    
    # Tipos de Pago
    Tipopago.objects.create(id=1, nombrepago='Efectivo')
    Tipopago.objects.create(id=2, nombrepago='Tarjeta')
    Tipopago.objects.create(id=3, nombrepago='Transferencia')
    Tipopago.objects.create(id=4, nombrepago='QR')
    
    # Estados de Factura
    Estadodefactura.objects.create(id=1, estado='Pendiente')
    Estadodefactura.objects.create(id=2, estado='Pagada')
    Estadodefactura.objects.create(id=3, estado='Anulada')
    
    print(f"  ✓ {len(horarios)} horarios creados")
    print(f"  ✓ {len(estados)} estados de consulta")
    print(f"  ✓ {len(tipos_consulta)} tipos de consulta")
    print(f"  ✓ 4 tipos de pago")
    print(f"  ✓ 3 estados de factura")
    
    # ==================== USUARIOS ====================
    print("\n👥 Creando usuarios...")
    
    # ADMINISTRADOR
    admin_django = User.objects.create_user(
        username='admin@clinica1.com',
        email='admin@clinica1.com',
        password='admin123',
        is_staff=True,
        is_superuser=True
    )
    admin_usuario = Usuario.objects.create(
        nombre='Admin',
        apellido='Sistema',
        correoelectronico='admin@clinica1.com',
        sexo='M',
        telefono='70000000',
        idtipousuario=tipo_admin
    )
    Token.objects.create(user=admin_django)
    
    # ODONTÓLOGOS
    odontologos = []
    odontologos_data = [
        {
            'nombre': 'Juan Carlos', 'apellido': 'Pérez López',
            'email': 'dr.perez@clinica1.com', 'especialidad': 'Ortodoncia',
            'matricula': 'ODO-001', 'experiencia': '10 años en ortodoncia'
        },
        {
            'nombre': 'María Fernanda', 'apellido': 'García Rojas',
            'email': 'dra.garcia@clinica1.com', 'especialidad': 'Endodoncia',
            'matricula': 'ODO-002', 'experiencia': '8 años en endodoncia'
        },
        {
            'nombre': 'Roberto', 'apellido': 'Martínez Silva',
            'email': 'dr.martinez@clinica1.com', 'especialidad': 'Cirugía Oral',
            'matricula': 'ODO-003', 'experiencia': '15 años en cirugía'
        },
    ]
    
    for idx, data in enumerate(odontologos_data, 1):
        django_user = User.objects.create_user(
            username=data['email'],
            email=data['email'],
            password='odontologo123'
        )
        usuario = Usuario.objects.create(
            nombre=data['nombre'],
            apellido=data['apellido'],
            correoelectronico=data['email'],
            sexo='M' if idx % 2 == 1 else 'F',
            telefono=f'7000000{idx}',
            idtipousuario=tipo_odontologo
        )
        odontologo = Odontologo.objects.create(
            codusuario=usuario,
            especialidad=data['especialidad'],
            nromatricula=data['matricula'],
            experienciaprofesional=data['experiencia']
        )
        Token.objects.create(user=django_user)
        odontologos.append(odontologo)
    
    # RECEPCIONISTA
    recep_django = User.objects.create_user(
        username='recepcion@clinica1.com',
        email='recepcion@clinica1.com',
        password='recepcion123'
    )
    recep_usuario = Usuario.objects.create(
        nombre='Laura',
        apellido='Morales Quispe',
        correoelectronico='recepcion@clinica1.com',
        sexo='F',
        telefono='70000010',
        idtipousuario=tipo_recepcionista
    )
    recepcionista = Recepcionista.objects.create(
        codusuario=recep_usuario,
        habilidadessoftware='Microsoft Office, Software de gestión clínica'
    )
    Token.objects.create(user=recep_django)
    
    # PACIENTES
    pacientes = []
    pacientes_data = [
        {
            'nombre': 'Ana', 'apellido': 'López Fernández',
            'email': 'ana.lopez@email.com', 'ci': '1234567',
            'fecha_nac': date(1990, 5, 15), 'direccion': 'Av. Brasil #123'
        },
        {
            'nombre': 'Carlos', 'apellido': 'Rodríguez Mamani',
            'email': 'carlos.rodriguez@email.com', 'ci': '2345678',
            'fecha_nac': date(1985, 8, 20), 'direccion': 'Calle Sucre #456'
        },
        {
            'nombre': 'Beatriz', 'apellido': 'Sánchez Quispe',
            'email': 'beatriz.sanchez@email.com', 'ci': '3456789',
            'fecha_nac': date(1995, 3, 10), 'direccion': 'Av. 6 de Agosto #789'
        },
        {
            'nombre': 'Diego', 'apellido': 'Torres Vega',
            'email': 'diego.torres@email.com', 'ci': '4567890',
            'fecha_nac': date(1988, 11, 25), 'direccion': 'Calle Potosí #321'
        },
        {
            'nombre': 'Elena', 'apellido': 'Vargas Castro',
            'email': 'elena.vargas@email.com', 'ci': '5678901',
            'fecha_nac': date(1992, 7, 30), 'direccion': 'Av. Arce #654'
        },
    ]
    
    for idx, data in enumerate(pacientes_data, 1):
        django_user = User.objects.create_user(
            username=data['email'],
            email=data['email'],
            password='paciente123'
        )
        usuario = Usuario.objects.create(
            nombre=data['nombre'],
            apellido=data['apellido'],
            correoelectronico=data['email'],
            sexo='F' if idx % 2 == 1 else 'M',
            telefono=f'7000001{idx}',
            idtipousuario=tipo_paciente,
            recibir_notificaciones=True,
            notificaciones_email=True
        )
        paciente = Paciente.objects.create(
            codusuario=usuario,
            carnetidentidad=data['ci'],
            fechanacimiento=data['fecha_nac'],
            direccion=data['direccion']
        )
        Token.objects.create(user=django_user)
        pacientes.append(paciente)
    
    print(f"  ✓ 1 administrador")
    print(f"  ✓ {len(odontologos)} odontólogos")
    print(f"  ✓ 1 recepcionista")
    print(f"  ✓ {len(pacientes)} pacientes")
    
    # ==================== SERVICIOS ====================
    print("\n🦷 Creando servicios...")
    
    servicios_data = [
        {'nombre': 'Limpieza Dental', 'costo': 150.00, 'duracion': 30},
        {'nombre': 'Extracción Simple', 'costo': 200.00, 'duracion': 45},
        {'nombre': 'Extracción Compleja', 'costo': 400.00, 'duracion': 90},
        {'nombre': 'Obturación (Resina)', 'costo': 250.00, 'duracion': 60},
        {'nombre': 'Endodoncia', 'costo': 800.00, 'duracion': 120},
        {'nombre': 'Corona de Porcelana', 'costo': 1500.00, 'duracion': 90},
        {'nombre': 'Blanqueamiento Dental', 'costo': 600.00, 'duracion': 60},
        {'nombre': 'Ortodoncia (Mes)', 'costo': 500.00, 'duracion': 30},
        {'nombre': 'Implante Dental', 'costo': 3000.00, 'duracion': 180},
        {'nombre': 'Prótesis Total', 'costo': 2500.00, 'duracion': 90},
    ]
    
    servicios = {}
    for data in servicios_data:
        servicio = Servicio.objects.create(
            nombre=data['nombre'],
            descripcion=f"Servicio de {data['nombre'].lower()}",
            costobase=Decimal(str(data['costo'])),
            duracion=data['duracion'],
            activo=True
        )
        servicios[data['nombre']] = servicio
    
    print(f"  ✓ {len(servicios)} servicios creados")
    
    # ==================== CONSULTAS ====================
    print("\n📅 Creando consultas de ejemplo...")
    
    hoy = datetime.now().date()
    
    # Consulta completada
    consulta1 = Consulta.objects.create(
        fecha=hoy - timedelta(days=3),
        codpaciente=pacientes[0],
        cododontologo=odontologos[0],
        codrecepcionista=recepcionista,
        idhorario=horarios[4],
        idtipoconsulta=tipos_consulta['primera_vez'],
        idestadoconsulta=estados['completada'],
        estado='completada',
        motivo_consulta='Revisión general y limpieza',
        diagnostico='Paciente con buena salud dental',
        tratamiento='Limpieza dental completa',
        costo_consulta=Decimal('150.00')
    )
    
    # Consulta confirmada (mañana)
    consulta2 = Consulta.objects.create(
        fecha=hoy + timedelta(days=1),
        codpaciente=pacientes[1],
        cododontologo=odontologos[1],
        codrecepcionista=recepcionista,
        idhorario=horarios[8],
        idtipoconsulta=tipos_consulta['control'],
        idestadoconsulta=estados['confirmada'],
        estado='confirmada',
        motivo_consulta='Control post-tratamiento'
    )
    
    # Consulta pendiente
    consulta3 = Consulta.objects.create(
        fecha=hoy + timedelta(days=5),
        codpaciente=pacientes[2],
        cododontologo=odontologos[2],
        idhorario=horarios[6],
        idtipoconsulta=tipos_consulta['urgencia'],
        idestadoconsulta=estados['pendiente'],
        estado='pendiente',
        motivo_consulta='Dolor intenso en muela'
    )
    
    print(f"  ✓ 3 consultas creadas")
    
    # ==================== INVENTARIO ====================
    print("\n📦 Creando inventario básico...")
    
    cat_material = CategoriaInsumo.objects.create(
        nombre='Material Dental',
        descripcion='Materiales de uso odontológico'
    )
    
    prov1 = Proveedor.objects.create(
        nombre='Dental Supply SA',
        ruc='1234567890',
        direccion='Av. Libertador #123',
        telefono='2-2222222',
        email='ventas@dentalsupply.com'
    )
    
    insumo1 = Insumo.objects.create(
        codigo='INS-001',
        nombre='Resina Composite A2',
        descripcion='Resina fotopolimerizable color A2',
        categoria=cat_material,
        proveedor_principal=prov1,
        stock_actual=Decimal('25.00'),
        stock_minimo=Decimal('10.00'),
        unidad_medida='unidad',
        precio_compra=Decimal('80.00')
    )
    
    print(f"  ✓ 1 categoría, 1 proveedor, 1 insumo")
    
    print(f"\n✅ Datos poblados exitosamente en schema '{clinica.schema_name}'")


def main():
    """Función principal"""
    print("\n" + "="*70)
    print("  🚀 SEEDER PARA RENDER - CLÍNICA DENTAL")
    print("="*70)
    print("\nEste script creará:")
    print("  1. Tenant público (si no existe)")
    print("  2. Clínica principal 'clinica1'")
    print("  3. Dominios para Render y psicoadmin.xyz")
    print("  4. Datos de prueba completos")
    
    try:
        with transaction.atomic():
            # Paso 1: Crear tenant público
            public_tenant = crear_tenant_public()
            
            # Paso 2: Crear clínica principal
            clinica = crear_clinica_principal()
            
            # Paso 3: Poblar datos
            poblar_datos_clinica(clinica)
        
        print_section("✅ PROCESO COMPLETADO EXITOSAMENTE")
        
        print("\n📝 INFORMACIÓN DE ACCESO:")
        print("-" * 70)
        print("\n🌐 DOMINIOS CONFIGURADOS:")
        print("  • Público: https://clinicadental-backend.onrender.com")
        print("  • Clínica1 (Render): https://clinica1.onrender.com")
        print("  • Clínica1 (Producción): https://clinica1.psicoadmin.xyz")
        
        print("\n👤 CREDENCIALES DE PRUEBA:")
        print("  ADMIN:")
        print("    Email: admin@clinica1.com")
        print("    Password: admin123")
        print("\n  ODONTÓLOGOS:")
        print("    Email: dr.perez@clinica1.com | Password: odontologo123")
        print("    Email: dra.garcia@clinica1.com | Password: odontologo123")
        print("    Email: dr.martinez@clinica1.com | Password: odontologo123")
        print("\n  RECEPCIONISTA:")
        print("    Email: recepcion@clinica1.com | Password: recepcion123")
        print("\n  PACIENTES:")
        print("    Email: ana.lopez@email.com | Password: paciente123")
        print("    Email: carlos.rodriguez@email.com | Password: paciente123")
        
        print("\n💡 PRÓXIMOS PASOS:")
        print("  1. Agregar dominios personalizados en Render:")
        print("     - Ir a Dashboard → Settings → Custom Domains")
        print("     - Agregar: clinica1.psicoadmin.xyz")
        print("  2. Configurar DNS en tu proveedor:")
        print("     - CNAME clinica1.psicoadmin.xyz → clinicadental-backend.onrender.com")
        print("  3. Esperar certificado SSL (automático)")
        print("-" * 70)
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
