"""
Script Poblador (Seeder) de Base de Datos - Clínica Dental
=====================================================

Destruye todos los datos existentes y crea un conjunto completo de datos de prueba.

Ejecución:
    python seed_database.py

ADVERTENCIA: Este script eliminará TODOS los datos de la base de datos.
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
from django.db import transaction
from rest_framework.authtoken.models import Token

# Importar modelos
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
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def destroy_all_data():
    """Elimina TODOS los datos de todas las tablas"""
    print_section("🗑️  DESTRUYENDO TODOS LOS DATOS")
    
    from apps.sistema_pagos.models import PagoEnLinea
    
    with transaction.atomic():
        # Orden CORRECTO de dependencias (de más dependiente a menos dependiente)
        print("Eliminando: Bitácora y Bloqueos...")
        Bitacora.objects.all().delete()
        BloqueoUsuario.objects.all().delete()
        
        print("Eliminando: Pagos en Línea (PROTECT)...")
        PagoEnLinea.objects.all().delete()  # PRIMERO: tiene PROTECT con Consulta
        
        print("Eliminando: Pagos y Facturas...")
        Pago.objects.all().delete()
        Itemdefactura.objects.all().delete()
        Factura.objects.all().delete()
        Estadodefactura.objects.all().delete()
        Tipopago.objects.all().delete()
        
        print("Eliminando: Tratamientos...")
        SesionTratamiento.objects.all().delete()
        HistorialPago.objects.all().delete()
        Procedimiento.objects.all().delete()
        ItemPresupuesto.objects.all().delete()
        Presupuesto.objects.all().delete()
        PlanTratamiento.objects.all().delete()
        
        print("Eliminando: Inventario...")
        AlertaInventario.objects.all().delete()
        MovimientoInventario.objects.all().delete()
        Insumo.objects.all().delete()
        Proveedor.objects.all().delete()
        CategoriaInsumo.objects.all().delete()
        
        print("Eliminando: Historial Clínico...")
        TratamientoOdontologico.objects.all().delete()
        ConsentimientoInformado.objects.all().delete()
        DocumentoClinico.objects.all().delete()
        Odontograma.objects.all().delete()
        Historialclinico.objects.all().delete()
        
        print("Eliminando: Servicios y Combos...")
        ComboServicioDetalle.objects.all().delete()
        ComboServicio.objects.all().delete()
        Servicio.objects.all().delete()
        
        print("Eliminando: Citas y Consultas...")
        Consulta.objects.all().delete()
        Tipodeconsulta.objects.all().delete()
        Estadodeconsulta.objects.all().delete()
        Horario.objects.all().delete()
        
        print("Eliminando: Profesionales...")
        Recepcionista.objects.all().delete()
        Odontologo.objects.all().delete()
        
        print("Eliminando: Pacientes y Usuarios...")
        Paciente.objects.all().delete()
        Usuario.objects.all().delete()
        Tipodeusuario.objects.all().delete()
        
        print("Eliminando: Tokens y Usuarios Django...")
        Token.objects.all().delete()
        # Eliminar TODOS los usuarios Django (incluyendo superusuarios)
        User.objects.all().delete()
    
    # Resetear secuencias de IDs para tablas de catálogo (IMPORTANTE)
    print("Reseteando secuencias de IDs de catálogos...")
    from django.db import connection
    with connection.cursor() as cursor:
        # Secuencias de tablas de catálogo (deben empezar desde 1)
        cursor.execute("ALTER SEQUENCE tipodeusuario_id_seq RESTART WITH 1;")
        cursor.execute("ALTER SEQUENCE estadodeconsulta_id_seq RESTART WITH 1;")
        cursor.execute("ALTER SEQUENCE tipodeconsulta_id_seq RESTART WITH 1;")
        cursor.execute("ALTER SEQUENCE tipopago_id_seq RESTART WITH 1;")
        cursor.execute("ALTER SEQUENCE estadodefactura_id_seq RESTART WITH 1;")
    
    print("✅ Todos los datos eliminados y secuencias reseteadas")


def create_base_data():
    """Crea datos base del sistema"""
    print_section("📋 CREANDO DATOS BASE")
    
    # Tipos de Usuario (IDs FIJOS para consistencia)
    print("Creando tipos de usuario...")
    tipo_admin = Tipodeusuario.objects.create(
        id=1,  # ID FIJO
        rol='Administrador',
        descripcion='Usuario administrador del sistema'
    )
    tipo_odontologo = Tipodeusuario.objects.create(
        id=2,  # ID FIJO
        rol='Odontólogo',
        descripcion='Profesional odontólogo'
    )
    tipo_recepcionista = Tipodeusuario.objects.create(
        id=3,  # ID FIJO
        rol='Recepcionista',
        descripcion='Personal de recepción'
    )
    tipo_paciente = Tipodeusuario.objects.create(
        id=4,  # ID FIJO
        rol='Paciente',
        descripcion='Paciente de la clínica'
    )
    
    # Horarios (8:00 AM - 6:00 PM cada 30 minutos)
    print("Creando horarios...")
    horarios = []
    for hour in range(8, 18):
        for minute in [0, 30]:
            horario = Horario.objects.create(hora=f"{hour:02d}:{minute:02d}:00")
            horarios.append(horario)
    
    # Estados de Consulta (IDs FIJOS)
    print("Creando estados de consulta...")
    estados = {
        'pendiente': Estadodeconsulta.objects.create(id=1, estado='Pendiente'),
        'confirmada': Estadodeconsulta.objects.create(id=2, estado='Confirmada'),
        'en_consulta': Estadodeconsulta.objects.create(id=3, estado='En Consulta'),
        'completada': Estadodeconsulta.objects.create(id=4, estado='Completada'),
        'cancelada': Estadodeconsulta.objects.create(id=5, estado='Cancelada'),
        'no_asistio': Estadodeconsulta.objects.create(id=6, estado='No Asistió'),
    }
    
    # Tipos de Consulta (IDs FIJOS)
    print("Creando tipos de consulta...")
    tipos_consulta = {
        'primera_vez': Tipodeconsulta.objects.create(
            id=1,  # ID FIJO
            nombreconsulta='Primera Vez',
            permite_agendamiento_web=True,
            requiere_aprobacion=False,
            es_urgencia=False,
            duracion_estimada=60
        ),
        'control': Tipodeconsulta.objects.create(
            id=2,  # ID FIJO
            nombreconsulta='Control',
            permite_agendamiento_web=True,
            requiere_aprobacion=False,
            es_urgencia=False,
            duracion_estimada=30
        ),
        'tratamiento': Tipodeconsulta.objects.create(
            id=3,  # ID FIJO
            nombreconsulta='Tratamiento',
            permite_agendamiento_web=False,
            requiere_aprobacion=True,
            es_urgencia=False,
            duracion_estimada=90
        ),
        'urgencia': Tipodeconsulta.objects.create(
            id=4,  # ID FIJO
            nombreconsulta='Urgencia',
            permite_agendamiento_web=True,
            requiere_aprobacion=False,
            es_urgencia=True,
            duracion_estimada=45
        ),
    }
    
    # Tipos de Pago (IDs FIJOS)
    print("Creando tipos de pago...")
    tipo_efectivo = Tipopago.objects.create(id=1, nombrepago='Efectivo')
    tipo_tarjeta = Tipopago.objects.create(id=2, nombrepago='Tarjeta')
    tipo_transferencia = Tipopago.objects.create(id=3, nombrepago='Transferencia')
    tipo_qr = Tipopago.objects.create(id=4, nombrepago='QR')
    
    # Estados de Factura (IDs FIJOS)
    print("Creando estados de factura...")
    estado_pendiente = Estadodefactura.objects.create(id=1, estado='Pendiente')
    estado_pagada = Estadodefactura.objects.create(id=2, estado='Pagada')
    estado_anulada = Estadodefactura.objects.create(id=3, estado='Anulada')
    
    print("✅ Datos base creados")
    
    return {
        'tipos_usuario': {
            'admin': tipo_admin,
            'odontologo': tipo_odontologo,
            'recepcionista': tipo_recepcionista,
            'paciente': tipo_paciente
        },
        'horarios': horarios,
        'estados_consulta': estados,
        'tipos_consulta': tipos_consulta,
        'tipos_pago': {
            'efectivo': tipo_efectivo,
            'tarjeta': tipo_tarjeta,
            'transferencia': tipo_transferencia,
            'qr': tipo_qr
        },
        'estados_factura': {
            'pendiente': estado_pendiente,
            'pagada': estado_pagada,
            'anulada': estado_anulada
        }
    }


def create_users(base_data):
    """Crea usuarios del sistema"""
    print_section("👤 CREANDO USUARIOS")
    
    usuarios = {}
    
    # 1. ADMINISTRADOR
    print("Creando administrador...")
    admin_django = User.objects.create_user(
        username='admin@clinica.com',
        email='admin@clinica.com',
        password='admin123',
        is_staff=True,
        is_superuser=True
    )
    admin_usuario = Usuario.objects.create(
        nombre='Admin',
        apellido='Sistema',
        correoelectronico='admin@clinica.com',
        sexo='M',
        telefono='70000000',
        idtipousuario=base_data['tipos_usuario']['admin']
    )
    Token.objects.create(user=admin_django)
    usuarios['admin'] = {'django': admin_django, 'usuario': admin_usuario}
    
    # 2. ODONTÓLOGOS
    print("Creando odontólogos...")
    odontologos_data = [
        {
            'nombre': 'Juan Carlos', 'apellido': 'Pérez López',
            'email': 'dr.perez@clinica.com', 'especialidad': 'Ortodoncia',
            'matricula': 'ODO-001', 'experiencia': '10 años de experiencia en ortodoncia'
        },
        {
            'nombre': 'María Fernanda', 'apellido': 'García Rojas',
            'email': 'dra.garcia@clinica.com', 'especialidad': 'Endodoncia',
            'matricula': 'ODO-002', 'experiencia': '8 años de experiencia en endodoncia'
        },
        {
            'nombre': 'Roberto', 'apellido': 'Martínez Silva',
            'email': 'dr.martinez@clinica.com', 'especialidad': 'Cirugía Oral',
            'matricula': 'ODO-003', 'experiencia': '15 años de experiencia en cirugía'
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
            idtipousuario=base_data['tipos_usuario']['odontologo']
        )
        odontologo = Odontologo.objects.create(
            codusuario=usuario,
            especialidad=data['especialidad'],
            nromatricula=data['matricula'],
            experienciaprofesional=data['experiencia']
        )
        Token.objects.create(user=django_user)
        usuarios[f'odontologo_{idx}'] = {
            'django': django_user,
            'usuario': usuario,
            'odontologo': odontologo
        }
    
    # 3. RECEPCIONISTA
    print("Creando recepcionista...")
    recep_django = User.objects.create_user(
        username='recepcion@clinica.com',
        email='recepcion@clinica.com',
        password='recepcion123'
    )
    recep_usuario = Usuario.objects.create(
        nombre='Laura',
        apellido='Morales Quispe',
        correoelectronico='recepcion@clinica.com',
        sexo='F',
        telefono='70000010',
        idtipousuario=base_data['tipos_usuario']['recepcionista']
    )
    recepcionista = Recepcionista.objects.create(
        codusuario=recep_usuario,
        habilidadessoftware='Microsoft Office, Software de gestión clínica'
    )
    Token.objects.create(user=recep_django)
    usuarios['recepcionista'] = {
        'django': recep_django,
        'usuario': recep_usuario,
        'recepcionista': recepcionista
    }
    
    # 4. PACIENTES
    print("Creando pacientes...")
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
            idtipousuario=base_data['tipos_usuario']['paciente'],
            recibir_notificaciones=True,
            notificaciones_email=True,
            notificaciones_push=False
        )
        paciente = Paciente.objects.create(
            codusuario=usuario,
            carnetidentidad=data['ci'],
            fechanacimiento=data['fecha_nac'],
            direccion=data['direccion']
        )
        Token.objects.create(user=django_user)
        usuarios[f'paciente_{idx}'] = {
            'django': django_user,
            'usuario': usuario,
            'paciente': paciente
        }
    
    print(f"✅ {len(usuarios)} usuarios creados")
    return usuarios


def create_servicios():
    """Crea servicios odontológicos"""
    print_section("🦷 CREANDO SERVICIOS")
    
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
        print(f"  ✓ {data['nombre']}: ${data['costo']}")
    
    # Crear combos
    print("\nCreando combos de servicios...")
    combo1 = ComboServicio.objects.create(
        nombre='Paquete Limpieza Completa',
        descripcion='Limpieza + Blanqueamiento',
        tipo_precio='PORCENTAJE',
        valor_precio=Decimal('15.00'),  # 15% descuento
        activo=True
    )
    ComboServicioDetalle.objects.create(
        combo=combo1,
        servicio=servicios['Limpieza Dental'],
        cantidad=1,
        orden=1
    )
    ComboServicioDetalle.objects.create(
        combo=combo1,
        servicio=servicios['Blanqueamiento Dental'],
        cantidad=1,
        orden=2
    )
    
    print(f"✅ {len(servicios)} servicios y 1 combo creados")
    return servicios


def create_consultas(usuarios, base_data):
    """Crea consultas de prueba"""
    print_section("📅 CREANDO CONSULTAS")
    
    consultas = []
    hoy = datetime.now().date()
    
    # Consulta 1: Paciente 1 con Odontólogo 1 (Completada - hace 3 días)
    consulta1 = Consulta.objects.create(
        fecha=hoy - timedelta(days=3),
        codpaciente=usuarios['paciente_1']['paciente'],
        cododontologo=usuarios['odontologo_1']['odontologo'],
        codrecepcionista=usuarios['recepcionista']['recepcionista'],
        idhorario=base_data['horarios'][4],  # 10:00 AM
        idtipoconsulta=base_data['tipos_consulta']['primera_vez'],
        idestadoconsulta=base_data['estados_consulta']['completada'],
        estado='completada',
        motivo_consulta='Revisión general y limpieza',
        diagnostico='Paciente con buena salud dental. Se realizó limpieza.',
        tratamiento='Limpieza dental completa',
        costo_consulta=Decimal('150.00'),
        requiere_pago=True
    )
    consultas.append(consulta1)
    
    # Consulta 2: Paciente 2 con Odontólogo 2 (Confirmada - mañana)
    consulta2 = Consulta.objects.create(
        fecha=hoy + timedelta(days=1),
        codpaciente=usuarios['paciente_2']['paciente'],
        cododontologo=usuarios['odontologo_2']['odontologo'],
        codrecepcionista=usuarios['recepcionista']['recepcionista'],
        idhorario=base_data['horarios'][8],  # 12:00 PM
        idtipoconsulta=base_data['tipos_consulta']['control'],
        idestadoconsulta=base_data['estados_consulta']['confirmada'],
        estado='confirmada',
        motivo_consulta='Control post-tratamiento de conducto',
        notas_recepcion='Paciente solicita atención preferente'
    )
    consultas.append(consulta2)
    
    # Consulta 3: Paciente 3 con Odontólogo 3 (Pendiente - en 5 días)
    consulta3 = Consulta.objects.create(
        fecha=hoy + timedelta(days=5),
        codpaciente=usuarios['paciente_3']['paciente'],
        cododontologo=usuarios['odontologo_3']['odontologo'],
        idhorario=base_data['horarios'][6],  # 11:00 AM
        idtipoconsulta=base_data['tipos_consulta']['urgencia'],
        idestadoconsulta=base_data['estados_consulta']['pendiente'],
        estado='pendiente',
        motivo_consulta='Dolor intenso en muela',
        tipo_consulta='urgencia'
    )
    consultas.append(consulta3)
    
    # Consulta 4: Paciente 4 con Odontólogo 1 (Cancelada)
    consulta4 = Consulta.objects.create(
        fecha=hoy - timedelta(days=1),
        codpaciente=usuarios['paciente_4']['paciente'],
        cododontologo=usuarios['odontologo_1']['odontologo'],
        idhorario=base_data['horarios'][10],  # 13:00 PM
        idtipoconsulta=base_data['tipos_consulta']['control'],
        idestadoconsulta=base_data['estados_consulta']['cancelada'],
        estado='cancelada',
        motivo_consulta='Control rutinario',
        motivo_cancelacion='Paciente tuvo un imprevisto laboral'
    )
    consultas.append(consulta4)
    
    print(f"✅ {len(consultas)} consultas creadas")
    return consultas


def create_historiales(usuarios, consultas):
    """Crea historiales clínicos"""
    print_section("📋 CREANDO HISTORIALES CLÍNICOS")
    
    historiales = []
    
    # Historial para Paciente 1 (relacionado con consulta completada)
    historial1 = Historialclinico.objects.create(
        pacientecodigo=usuarios['paciente_1']['paciente'],
        motivoconsulta='Revisión general y limpieza dental',
        diagnostico='Paciente con buena salud dental general. Sin caries detectadas.',
        tratamiento='Se realizó limpieza dental profunda con ultrasonido.',
        alergias='Ninguna conocida',
        enfermedades='Ninguna',
        examenbucal='Encías sanas, sin sangrado. Placa dental moderada.',
        receta='Enjuague bucal con clorhexidina 0.12% por 7 días'
    )
    historiales.append(historial1)
    
    # Crear odontograma para Paciente 1
    odontograma1 = Odontograma.objects.create(
        paciente=usuarios['paciente_1']['paciente'],
        odontologo=usuarios['odontologo_1']['odontologo'],
        observaciones_generales='Estado general bueno'
    )
    odontograma1.inicializar_dientes()
    odontograma1.actualizar_diente(18, 'obturacion', ['oclusal'], 'Obturación antigua en buen estado')
    odontograma1.actualizar_diente(36, 'caries', ['oclusal', 'mesial'], 'Caries superficial')
    
    # Historial para Paciente 2
    historial2 = Historialclinico.objects.create(
        pacientecodigo=usuarios['paciente_2']['paciente'],
        motivoconsulta='Control post-endodoncia',
        diagnostico='Evolución favorable del tratamiento de conducto',
        tratamiento='Control radiográfico',
        alergias='Alergia a penicilina',
        enfermedades='Hipertensión controlada',
        examenbucal='Zona tratada sin inflamación ni dolor'
    )
    historiales.append(historial2)
    
    print(f"✅ {len(historiales)} historiales clínicos creados")
    return historiales


def create_planes_tratamiento(usuarios, servicios):
    """Crea planes de tratamiento y presupuestos"""
    print_section("💰 CREANDO PLANES Y PRESUPUESTOS")
    
    # Plan para Paciente 3
    plan1 = PlanTratamiento.objects.create(
        paciente=usuarios['paciente_3']['paciente'],
        odontologo=usuarios['odontologo_3']['odontologo'],
        descripcion='Plan de extracción y restauración',
        diagnostico='Muela con caries profunda y fractura',
        estado='aprobado',
        duracion_estimada_dias=30
    )
    
    # Crear presupuesto para el plan
    presupuesto1 = Presupuesto.objects.create(
        plan_tratamiento=plan1,
        subtotal=Decimal('600.00'),
        descuento=Decimal('50.00'),
        impuesto=Decimal('0.00'),
        total=Decimal('550.00'),
        estado='aprobado',
        fecha_vencimiento=datetime.now().date() + timedelta(days=30)
    )
    
    # Items del presupuesto
    ItemPresupuesto.objects.create(
        presupuesto=presupuesto1,
        servicio=servicios['Extracción Compleja'],
        cantidad=1,
        precio_unitario=Decimal('400.00'),
        total=Decimal('400.00'),
        numero_diente=36
    )
    
    ItemPresupuesto.objects.create(
        presupuesto=presupuesto1,
        servicio=servicios['Obturación (Resina)'],
        cantidad=1,
        precio_unitario=Decimal('250.00'),
        descuento_item=Decimal('50.00'),
        total=Decimal('200.00'),
        numero_diente=37
    )
    
    # Crear procedimientos
    Procedimiento.objects.create(
        plan_tratamiento=plan1,
        servicio=servicios['Extracción Compleja'],
        odontologo=usuarios['odontologo_3']['odontologo'],
        numero_diente=36,
        descripcion='Extracción de muela con caries profunda',
        estado='pendiente',
        fecha_planificada=datetime.now().date() + timedelta(days=7),
        costo_estimado=Decimal('400.00')
    )
    
    # Plan para Paciente 5 (ortodoncia)
    plan2 = PlanTratamiento.objects.create(
        paciente=usuarios['paciente_5']['paciente'],
        odontologo=usuarios['odontologo_1']['odontologo'],
        descripcion='Plan de ortodoncia - 12 meses',
        diagnostico='Maloclusión clase II, apiñamiento dental',
        estado='en_proceso',
        duracion_estimada_dias=365
    )
    
    presupuesto2 = Presupuesto.objects.create(
        plan_tratamiento=plan2,
        subtotal=Decimal('6000.00'),
        descuento=Decimal('500.00'),
        impuesto=Decimal('0.00'),
        total=Decimal('5500.00'),
        estado='aprobado'
    )
    
    ItemPresupuesto.objects.create(
        presupuesto=presupuesto2,
        servicio=servicios['Ortodoncia (Mes)'],
        cantidad=12,
        precio_unitario=Decimal('500.00'),
        descuento_item=Decimal('500.00'),
        total=Decimal('5500.00')
    )
    
    # Registrar pago inicial
    HistorialPago.objects.create(
        plan_tratamiento=plan2,
        presupuesto=presupuesto2,
        monto=Decimal('1500.00'),
        metodo_pago='tarjeta',
        estado='completado',
        numero_comprobante='REC-001',
        registrado_por='Recepcionista Laura Morales'
    )
    
    print("✅ 2 planes de tratamiento con presupuestos creados")


def create_inventario():
    """Crea inventario de insumos"""
    print_section("📦 CREANDO INVENTARIO")
    
    # Categorías
    cat_material = CategoriaInsumo.objects.create(
        nombre='Material Dental',
        descripcion='Materiales de uso odontológico'
    )
    cat_medicamento = CategoriaInsumo.objects.create(
        nombre='Medicamentos',
        descripcion='Medicamentos y anestésicos'
    )
    cat_instrumental = CategoriaInsumo.objects.create(
        nombre='Instrumental',
        descripcion='Instrumental odontológico'
    )
    
    # Proveedores
    prov1 = Proveedor.objects.create(
        nombre='Dental Supply SA',
        ruc='1234567890',
        direccion='Av. Libertador #123',
        telefono='2-2222222',
        email='ventas@dentalsupply.com',
        contacto_nombre='José Pérez',
        contacto_telefono='70123456'
    )
    
    # Insumos
    insumo1 = Insumo.objects.create(
        codigo='INS-001',
        nombre='Resina Composite A2',
        descripcion='Resina fotopolimerizable color A2',
        categoria=cat_material,
        proveedor_principal=prov1,
        stock_actual=Decimal('25.00'),
        stock_minimo=Decimal('10.00'),
        stock_maximo=Decimal('50.00'),
        unidad_medida='unidad',
        precio_compra=Decimal('80.00'),
        precio_venta=Decimal('120.00')
    )
    
    insumo2 = Insumo.objects.create(
        codigo='INS-002',
        nombre='Anestesia Lidocaína 2%',
        descripcion='Anestésico local con epinefrina',
        categoria=cat_medicamento,
        proveedor_principal=prov1,
        stock_actual=Decimal('8.00'),
        stock_minimo=Decimal('15.00'),  # Stock bajo!
        stock_maximo=Decimal('100.00'),
        unidad_medida='caja',
        precio_compra=Decimal('45.00'),
        requiere_vencimiento=True,
        fecha_vencimiento=date(2026, 12, 31)
    )
    
    # Crear alerta de stock bajo
    AlertaInventario.objects.create(
        insumo=insumo2,
        tipo_alerta='stock_bajo',
        mensaje=f'Stock de {insumo2.nombre} por debajo del mínimo (8 < 15)',
        prioridad='alta'
    )
    
    print("✅ Inventario creado con 2 insumos y 1 alerta")


def main():
    """Función principal"""
    print("\n" + "="*60)
    print("  🏥 SEEDER DE BASE DE DATOS - CLÍNICA DENTAL")
    print("="*60)
    
    # Permitir --force para saltar confirmación
    if len(sys.argv) > 1 and sys.argv[1] == '--force':
        print("⚠️  Modo FORCE: Eliminando datos sin confirmación...")
    else:
        print("\n⚠️  ADVERTENCIA: Este script eliminará TODOS los datos")
        print("¿Desea continuar? (s/n): ", end='')
        
        respuesta = input().lower()
        if respuesta != 's':
            print("❌ Operación cancelada")
            return
    
    try:
        with transaction.atomic():
            # 1. Destruir datos
            destroy_all_data()
            
            # 2. Crear datos base
            base_data = create_base_data()
            
            # 3. Crear usuarios
            usuarios = create_users(base_data)
            
            # 4. Crear servicios
            servicios = create_servicios()
            
            # 5. Crear consultas
            consultas = create_consultas(usuarios, base_data)
            
            # 6. Crear historiales
            historiales = create_historiales(usuarios, consultas)
            
            # 7. Crear planes y presupuestos
            create_planes_tratamiento(usuarios, servicios)
            
            # 8. Crear inventario
            create_inventario()
        
        print_section("✅ SEEDER COMPLETADO EXITOSAMENTE")
        print("\n📝 CREDENCIALES DE ACCESO:")
        print("-" * 60)
        print("ADMIN:")
        print("  Email: admin@clinica.com")
        print("  Password: admin123")
        print("\nODONTÓLOGOS:")
        print("  Email: dr.perez@clinica.com | Password: odontologo123")
        print("  Email: dra.garcia@clinica.com | Password: odontologo123")
        print("  Email: dr.martinez@clinica.com | Password: odontologo123")
        print("\nRECEPCIONISTA:")
        print("  Email: recepcion@clinica.com | Password: recepcion123")
        print("\nPACIENTES:")
        print("  Email: ana.lopez@email.com | Password: paciente123")
        print("  Email: carlos.rodriguez@email.com | Password: paciente123")
        print("  Email: beatriz.sanchez@email.com | Password: paciente123")
        print("  Email: diego.torres@email.com | Password: paciente123")
        print("  Email: elena.vargas@email.com | Password: paciente123")
        print("-" * 60)
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
