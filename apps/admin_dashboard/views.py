"""
Dashboard administrativo con métricas clave.
CU26: Dashboard Administrativo
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from apps.citas.models import Consulta, Horario
from apps.usuarios.models import Paciente, Usuario
from apps.profesionales.models import Odontologo, Recepcionista
from apps.sistema_pagos.models import Factura, Pago
from apps.historial_clinico.models import Historialclinico
from apps.tratamientos.models import PlanTratamiento


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_general(request):
    """
    Dashboard principal con métricas generales de la clínica.
    
    GET /api/v1/admin/dashboard/
    
    Retorna métricas de:
    - Consultas de hoy y pendientes
    - Ingresos del mes
    - Pacientes activos
    - Odontólogos disponibles
    - Alertas y notificaciones
    """
    hoy = timezone.now().date()
    inicio_mes = hoy.replace(day=1)
    fin_mes = (inicio_mes + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    # === MÉTRICAS DE HOY ===
    consultas_hoy = Consulta.objects.filter(fecha=hoy)
    
    metricas_hoy = {
        'total_consultas': consultas_hoy.count(),
        'completadas': consultas_hoy.filter(estado='completada').count(),
        'pendientes': consultas_hoy.filter(estado='pendiente').count(),
        'en_consulta': consultas_hoy.filter(estado='en_consulta').count(),
        'canceladas': consultas_hoy.filter(estado='cancelada').count(),
        'no_asistio': consultas_hoy.filter(estado='no_asistio').count(),
    }
    
    # === MÉTRICAS DEL MES ===
    consultas_mes = Consulta.objects.filter(fecha__range=[inicio_mes, fin_mes])
    # Corregido: fechaemision en lugar de fechafacturacion
    facturas_mes = Factura.objects.filter(fechaemision__range=[inicio_mes, fin_mes])
    
    metricas_mes = {
        'total_consultas': consultas_mes.count(),
        'consultas_completadas': consultas_mes.filter(estado='completada').count(),
        'ingresos_totales': float(facturas_mes.aggregate(
            total=Sum('montototal')
        )['total'] or 0),
        'facturas_pendientes': facturas_mes.filter(idestadofactura__estado='pendiente').count(),
        'facturas_pagadas': facturas_mes.filter(idestadofactura__estado='pagada').count(),
        'nuevos_pacientes': 0,  # Simplificado: Usuario no tiene timestamp de creación
    }
    
    # === RECURSOS HUMANOS ===
    recursos_humanos = {
        'total_odontologos': Odontologo.objects.count(),
        'odontologos_activos_hoy': consultas_hoy.values('cododontologo').distinct().count(),
        'total_recepcionistas': Recepcionista.objects.count(),
        'total_pacientes': Paciente.objects.count(),
        'pacientes_activos_mes': consultas_mes.values('codpaciente').distinct().count(),
    }
    
    # === PRÓXIMAS CITAS ===
    manana = hoy + timedelta(days=1)
    proximas_citas = Consulta.objects.filter(
        fecha__gte=hoy,
        fecha__lte=manana,
        estado__in=['pendiente', 'confirmada']
    ).select_related(
        'codpaciente__codusuario',
        'cododontologo__codusuario'
    ).order_by('fecha', 'hora_consulta')[:10]
    
    lista_proximas_citas = [
        {
            'id': cita.id,
            'fecha': cita.fecha.isoformat(),
            'hora': cita.hora_consulta.strftime('%H:%M') if cita.hora_consulta else None,
            'paciente': f"{cita.codpaciente.codusuario.nombre} {cita.codpaciente.codusuario.apellido}",
            'odontologo': f"Dr. {cita.cododontologo.codusuario.nombre} {cita.cododontologo.codusuario.apellido}" if cita.cododontologo else None,
            'estado': cita.estado,
            'motivo': cita.motivo_consulta,
        }
        for cita in proximas_citas
    ]
    
    # === ALERTAS ===
    alertas = []
    
    # Alertas de citas sin confirmar
    citas_sin_confirmar = consultas_hoy.filter(estado='pendiente').count()
    if citas_sin_confirmar > 0:
        alertas.append({
            'tipo': 'warning',
            'mensaje': f"{citas_sin_confirmar} cita(s) sin confirmar para hoy",
            'prioridad': 'alta'
        })
    
    # Alertas de facturas pendientes - Corregido: usar idestadofactura en lugar de estadopago
    from apps.sistema_pagos.models import Estadodefactura
    estado_pendiente = Estadodefactura.objects.filter(estado__icontains='pendiente').first()
    if estado_pendiente:
        facturas_pendientes_count = facturas_mes.filter(idestadofactura=estado_pendiente).count()
        if facturas_pendientes_count > 5:
            alertas.append({
                'tipo': 'info',
                'mensaje': f"{facturas_pendientes_count} facturas pendientes de pago este mes",
                'prioridad': 'media'
            })
    
    # Alertas de pacientes no-show
    pacientes_noshow_hoy = consultas_hoy.filter(estado='no_asistio').count()
    if pacientes_noshow_hoy > 0:
        alertas.append({
            'tipo': 'error',
            'mensaje': f"{pacientes_noshow_hoy} paciente(s) no asistió hoy",
            'prioridad': 'alta'
        })
    
    # === ESTADÍSTICAS RÁPIDAS ===
    estadisticas_rapidas = {
        'tasa_asistencia_mes': _calcular_tasa_asistencia(consultas_mes),
        'ticket_promedio': float(facturas_mes.aggregate(
            promedio=Avg('montototal')
        )['promedio'] or 0),
        'consultas_por_dia': round(consultas_mes.count() / hoy.day, 1),
        'ocupacion_odontologos': _calcular_ocupacion_odontologos(consultas_mes),
    }
    
    return Response({
        'fecha': hoy.isoformat(),
        'hoy': metricas_hoy,
        'mes_actual': metricas_mes,
        'recursos_humanos': recursos_humanos,
        'proximas_citas': lista_proximas_citas,
        'alertas': alertas,
        'estadisticas': estadisticas_rapidas,
        'fecha_generacion': timezone.now().isoformat(),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_financiero(request):
    """
    Dashboard financiero con gráficos de ingresos.
    
    GET /api/v1/admin/dashboard/financiero/
    """
    hoy = timezone.now().date()
    inicio_mes = hoy.replace(day=1)
    
    # Ingresos por día del mes actual
    ingresos_diarios = []
    fecha_actual = inicio_mes
    
    while fecha_actual <= hoy:
        ingresos_dia = Factura.objects.filter(
            fechafacturacion=fecha_actual
        ).aggregate(total=Sum('montototal'))['total'] or Decimal('0.00')
        
        ingresos_diarios.append({
            'fecha': fecha_actual.isoformat(),
            'dia': fecha_actual.day,
            'ingresos': float(ingresos_dia),
        })
        
        fecha_actual += timedelta(days=1)
    
    # Ingresos por método de pago
    facturas_mes = Factura.objects.filter(
        fechafacturacion__range=[inicio_mes, hoy]
    )
    
    ingresos_por_metodo = list(
        facturas_mes.values('formapago')
        .annotate(
            total=Sum('montototal'),
            cantidad=Count('id')
        )
        .order_by('-total')
    )
    
    # Top odontólogos por ingresos
    from apps.profesionales.models import Odontologo
    
    top_odontologos = []
    for odontologo in Odontologo.objects.all()[:10]:
        ingresos = Factura.objects.filter(
            codpaciente__consulta__cododontologo=odontologo,
            fechafacturacion__range=[inicio_mes, hoy]
        ).aggregate(total=Sum('montototal'))['total'] or Decimal('0.00')
        
        top_odontologos.append({
            'id': odontologo.codigo,
            'nombre': f"Dr. {odontologo.codusuario.nombre} {odontologo.codusuario.apellido}",
            'ingresos': float(ingresos),
        })
    
    top_odontologos.sort(key=lambda x: x['ingresos'], reverse=True)
    
    return Response({
        'periodo': {
            'inicio': inicio_mes.isoformat(),
            'fin': hoy.isoformat(),
        },
        'ingresos_diarios': ingresos_diarios,
        'ingresos_por_metodo': [
            {
                'metodo': item['formapago'],
                'total': float(item['total']),
                'cantidad': item['cantidad']
            }
            for item in ingresos_por_metodo
        ],
        'top_odontologos': top_odontologos,
        'resumen': {
            'total_mes': sum(d['ingresos'] for d in ingresos_diarios),
            'promedio_diario': sum(d['ingresos'] for d in ingresos_diarios) / len(ingresos_diarios) if ingresos_diarios else 0,
            'mejor_dia': max(ingresos_diarios, key=lambda x: x['ingresos']) if ingresos_diarios else None,
        },
        'fecha_generacion': timezone.now().isoformat(),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_operaciones(request):
    """
    Dashboard operativo con métricas de eficiencia.
    
    GET /api/v1/admin/dashboard/operaciones/
    """
    hoy = timezone.now().date()
    inicio_semana = hoy - timedelta(days=hoy.weekday())
    
    # Consultas por día de la semana
    consultas_semana = []
    fecha_actual = inicio_semana
    
    for i in range(7):
        consultas_dia = Consulta.objects.filter(fecha=fecha_actual)
        
        consultas_semana.append({
            'fecha': fecha_actual.isoformat(),
            'dia_semana': ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'][i],
            'total': consultas_dia.count(),
            'completadas': consultas_dia.filter(estado='completada').count(),
            'canceladas': consultas_dia.filter(estado='cancelada').count(),
            'no_asistio': consultas_dia.filter(estado='no_asistio').count(),
        })
        
        fecha_actual += timedelta(days=1)
    
    # Tiempos promedio
    consultas_mes = Consulta.objects.filter(
        fecha__gte=hoy.replace(day=1),
        hora_inicio_consulta__isnull=False,
        hora_fin_consulta__isnull=False
    )
    
    tiempos_promedio = {
        'duracion_consulta': _calcular_duracion_promedio(consultas_mes),
        'tiempo_espera': 15,  # TODO: Calcular real basado en hora_llegada vs hora_inicio_consulta
        'consultas_por_odontologo': round(
            Consulta.objects.filter(fecha__gte=hoy.replace(day=1)).count() / 
            max(Odontologo.objects.count(), 1), 
            1
        ),
    }
    
    # Tasa de cancelación por motivo
    inicio_mes = hoy.replace(day=1)
    cancelaciones = Consulta.objects.filter(
        fecha__range=[inicio_mes, hoy],
        estado='cancelada',
        motivo_cancelacion__isnull=False
    )
    
    motivos_cancelacion = list(
        cancelaciones.values('motivo_cancelacion')
        .annotate(cantidad=Count('id'))
        .order_by('-cantidad')[:5]
    )
    
    return Response({
        'semana': {
            'inicio': inicio_semana.isoformat(),
            'fin': (inicio_semana + timedelta(days=6)).isoformat(),
            'consultas_por_dia': consultas_semana,
        },
        'eficiencia': tiempos_promedio,
        'cancelaciones': {
            'total_mes': cancelaciones.count(),
            'top_motivos': motivos_cancelacion,
        },
        'fecha_generacion': timezone.now().isoformat(),
    })


# === FUNCIONES AUXILIARES ===

def _calcular_tasa_asistencia(consultas):
    """Calcula porcentaje de asistencia."""
    total = consultas.count()
    if total == 0:
        return 0.0
    
    asistencias = consultas.filter(
        estado__in=['completada', 'en_consulta']
    ).count()
    
    return round((asistencias / total) * 100, 2)


def _calcular_ocupacion_odontologos(consultas):
    """Calcula porcentaje de ocupación de odontólogos."""
    total_odontologos = Odontologo.objects.count()
    if total_odontologos == 0:
        return 0.0
    
    odontologos_activos = consultas.values('cododontologo').distinct().count()
    return round((odontologos_activos / total_odontologos) * 100, 2)


def _calcular_duracion_promedio(consultas):
    """Calcula duración promedio de consultas en minutos."""
    duraciones = []
    
    for consulta in consultas:
        if consulta.hora_inicio_consulta and consulta.hora_fin_consulta:
            diferencia = consulta.hora_fin_consulta - consulta.hora_inicio_consulta
            duraciones.append(diferencia.total_seconds() / 60)
    
    if not duraciones:
        return 0.0
    
    return round(sum(duraciones) / len(duraciones), 1)


# ====================================================================
# CU25: REPORTES
# ====================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def reporte_citas(request):
    """
    Generar reporte de citas por período.
    Query params: 
        - fecha_inicio, fecha_fin: Rango de fechas
        - odontologo: Nombre del odontólogo (búsqueda parcial)
        - estado: Estado de la cita ('completada', 'pendiente', 'cancelada')
        - paciente: Nombre del paciente (búsqueda parcial)
        - tipo_consulta: ID del tipo de consulta
    
    Devuelve estadísticas + listado completo de consultas para la tabla
    """
    from datetime import datetime, timedelta
    
    # Función auxiliar para parsear fechas en múltiples formatos
    def parse_fecha(fecha_str, fecha_default):
        """Intenta parsear fecha en formatos: YYYY-MM-DD, DD/MM/YYYY"""
        if not fecha_str:
            return fecha_default
        
        # Intentar formato ISO (YYYY-MM-DD) - PREFERIDO
        try:
            return datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            pass
        
        # Intentar formato DD/MM/YYYY (por compatibilidad con frontend)
        try:
            return datetime.strptime(fecha_str, '%d/%m/%Y').date()
        except ValueError:
            pass
        
        # Si todo falla, usar default
        return fecha_default
    
    # Obtener rango de fechas (por defecto: último año)
    odontologo_nombre = request.query_params.get('odontologo', '').strip()
    estado_filtro = request.query_params.get('estado', '').strip().lower()  # NUEVO
    paciente_nombre = request.query_params.get('paciente', '').strip()  # NUEVO
    tipo_consulta_id = request.query_params.get('tipo_consulta', '').strip()  # NUEVO
    
    # Parsear fechas con soporte para múltiples formatos
    fecha_fin = parse_fecha(
        request.query_params.get('fecha_fin'),
        timezone.now().date()
    )
    fecha_inicio = parse_fecha(
        request.query_params.get('fecha_inicio'),
        fecha_fin - timedelta(days=365)
    )
    
    # Consultar citas en el rango
    consultas = Consulta.objects.filter(fecha__range=[fecha_inicio, fecha_fin])
    
    # ✅ Filtrar por odontólogo si se especifica (por nombre completo)
    if odontologo_nombre:
        consultas = consultas.filter(
            Q(cododontologo__codusuario__nombre__icontains=odontologo_nombre) |
            Q(cododontologo__codusuario__apellido__icontains=odontologo_nombre)
        )
    
    # ✅ NUEVO: Filtrar por estado
    if estado_filtro:
        consultas = consultas.filter(estado=estado_filtro)
    
    # ✅ NUEVO: Filtrar por paciente
    if paciente_nombre:
        consultas = consultas.filter(
            Q(codpaciente__codusuario__nombre__icontains=paciente_nombre) |
            Q(codpaciente__codusuario__apellido__icontains=paciente_nombre)
        )
    
    # ✅ NUEVO: Filtrar por tipo de consulta
    if tipo_consulta_id:
        consultas = consultas.filter(idtipoconsulta__id=tipo_consulta_id)
    
    # Preparar listado completo de consultas para la tabla
    consultas_lista = consultas.select_related(
        'codpaciente__codusuario',
        'cododontologo__codusuario',
        'idtipoconsulta'
    ).order_by('-fecha', '-hora_consulta')
    
    consultas_data = []
    for consulta in consultas_lista:
        consultas_data.append({
            'idconsulta': consulta.id,
            'fecha': consulta.fecha.isoformat(),
            'hora_inicio': consulta.hora_consulta.strftime('%H:%M') if consulta.hora_consulta else 'Sin hora',
            'paciente_nombre': consulta.codpaciente.codusuario.nombre,
            'paciente_apellido': consulta.codpaciente.codusuario.apellido,
            'paciente_rut': consulta.codpaciente.carnetidentidad or 'Sin CI',
            'odontologo_nombre': consulta.cododontologo.codusuario.nombre if consulta.cododontologo else 'Sin asignar',
            'odontologo_apellido': consulta.cododontologo.codusuario.apellido if consulta.cododontologo else '',
            'tipo_consulta': consulta.idtipoconsulta.nombreconsulta if consulta.idtipoconsulta else 'Sin tipo',
            'estado': consulta.estado or 'pendiente',
        })
    
    reporte = {
        'periodo': {
            'inicio': str(fecha_inicio),
            'fin': str(fecha_fin)
        },
        'total_citas': consultas.count(),
        'por_estado': {
            'completadas': consultas.filter(estado='completada').count(),
            'pendientes': consultas.filter(estado='pendiente').count(),
            'canceladas': consultas.filter(estado='cancelada').count(),
        },
        'por_odontologo': list(consultas.values(
            'cododontologo__codusuario__nombre',
            'cododontologo__codusuario__apellido'
        ).annotate(total=Count('id')).order_by('-total')[:10]),
        # NUEVO: Array de consultas para mostrar en tabla
        'consultas': consultas_data
    }
    
    return Response(reporte)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def reporte_tratamientos(request):
    """
    Generar reporte de tratamientos por período.
    Query params: fecha_inicio, fecha_fin
    """
    from apps.tratamientos.models import Procedimiento
    from datetime import datetime, timedelta
    
    # Obtener rango de fechas
    fecha_fin = request.query_params.get('fecha_fin')
    fecha_inicio = request.query_params.get('fecha_inicio')
    
    if not fecha_fin:
        fecha_fin = timezone.now().date()
    else:
        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
    
    if not fecha_inicio:
        fecha_inicio = fecha_fin - timedelta(days=30)
    else:
        fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
    
    planes = PlanTratamiento.objects.filter(fecha_inicio__range=[fecha_inicio, fecha_fin])
    procedimientos = Procedimiento.objects.filter(fecha_realizado__range=[fecha_inicio, fecha_fin])
    
    reporte = {
        'periodo': {
            'inicio': str(fecha_inicio),
            'fin': str(fecha_fin)
        },
        'planes_tratamiento': {
            'total': planes.count(),
            'por_estado': {
                'propuesto': planes.filter(estado='propuesto').count(),
                'aprobado': planes.filter(estado='aprobado').count(),
                'en_proceso': planes.filter(estado='en_proceso').count(),
                'completado': planes.filter(estado='completado').count(),
            }
        },
        'procedimientos': {
            'total': procedimientos.count(),
            'completados': procedimientos.filter(estado='completado').count(),
            'pendientes': procedimientos.filter(estado='pendiente').count(),
        }
    }
    
    return Response(reporte)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def reporte_ingresos(request):
    """
    Generar reporte de ingresos por período.
    Query params: fecha_inicio, fecha_fin
    """
    from datetime import datetime, timedelta
    
    # Obtener rango de fechas
    fecha_fin = request.query_params.get('fecha_fin')
    fecha_inicio = request.query_params.get('fecha_inicio')
    
    if not fecha_fin:
        fecha_fin = timezone.now().date()
    else:
        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
    
    if not fecha_inicio:
        fecha_inicio = fecha_fin - timedelta(days=30)
    else:
        fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
    
    # Consultar pagos en el rango
    pagos = Pago.objects.filter(fechapago__range=[fecha_inicio, fecha_fin])
    
    total_ingresos = pagos.aggregate(Sum('montopagado'))['montopagado__sum'] or 0
    
    reporte = {
        'periodo': {
            'inicio': str(fecha_inicio),
            'fin': str(fecha_fin)
        },
        'total_ingresos': float(total_ingresos),
        'total_pagos': pagos.count(),
        'por_tipo_pago': list(pagos.values(
            'idtipopago__nombrepago'  # Corregido: campo correcto
        ).annotate(
            total=Sum('montopagado'),
            cantidad=Count('id')
        ).order_by('-total'))
    }
    
    return Response(reporte)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def reporte_pacientes(request):
    """
    CU25: Reporte de pacientes con estadísticas
    Query params: 
        - fecha_inicio, fecha_fin: Rango de fechas (formato YYYY-MM-DD)
        - actividad: 'activos' (con citas en período), 'inactivos' (sin citas), 'todos' (default)
        - min_citas: Mínimo de citas totales
        - max_citas: Máximo de citas totales
    """
    from datetime import datetime
    
    # Obtener parámetros de filtrado
    fecha_fin = request.query_params.get('fecha_fin')
    fecha_inicio = request.query_params.get('fecha_inicio')
    actividad = request.query_params.get('actividad', 'todos').lower()  # NUEVO: filtro de actividad
    min_citas = request.query_params.get('min_citas')  # NUEVO: mínimo de citas
    max_citas = request.query_params.get('max_citas')  # NUEVO: máximo de citas
    
    # Función auxiliar para parsear fechas en múltiples formatos
    def parse_fecha(fecha_str, fecha_default):
        """Intenta parsear fecha en formatos: YYYY-MM-DD, DD/MM/YYYY"""
        if not fecha_str:
            return fecha_default
        
        # Intentar formato ISO (YYYY-MM-DD) - PREFERIDO
        try:
            return datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            pass
        
        # Intentar formato DD/MM/YYYY (por compatibilidad)
        try:
            return datetime.strptime(fecha_str, '%d/%m/%Y').date()
        except ValueError:
            pass
        
        # Si todo falla, usar default
        return fecha_default
    
    # Parsear fechas con soporte para múltiples formatos
    fecha_fin = parse_fecha(fecha_fin, timezone.now().date())
    fecha_inicio = parse_fecha(fecha_inicio, fecha_fin - timedelta(days=365))
    
    # Obtener todos los pacientes con sus estadísticas
    pacientes = Paciente.objects.select_related('codusuario').all()
    
    lista_pacientes = []
    for paciente in pacientes:
        # Estadísticas de citas (usar paciente directamente, no paciente.codusuario)
        citas_totales = Consulta.objects.filter(
            codpaciente=paciente
        ).count()
        
        citas_periodo = Consulta.objects.filter(
            codpaciente=paciente,
            fecha__range=[fecha_inicio, fecha_fin]
        ).count()
        
        # ✅ NUEVO: Aplicar filtro de actividad
        if actividad == 'activos' and citas_periodo == 0:
            continue  # Saltar pacientes sin citas en el período
        elif actividad == 'inactivos' and citas_periodo > 0:
            continue  # Saltar pacientes CON citas en el período
        
        # ✅ NUEVO: Aplicar filtro de mínimo de citas
        if min_citas and citas_totales < int(min_citas):
            continue
        
        # ✅ NUEVO: Aplicar filtro de máximo de citas
        if max_citas and citas_totales > int(max_citas):
            continue
        
        # Estadísticas de tratamientos (usar PK del paciente)
        planes_totales = PlanTratamiento.objects.filter(
            paciente_id=paciente.codusuario.codigo
        ).count()
        
        planes_activos = PlanTratamiento.objects.filter(
            paciente_id=paciente.codusuario.codigo,
            estado='activo'
        ).count()
        
        # Última cita (usar paciente directamente)
        ultima_cita = Consulta.objects.filter(
            codpaciente=paciente
        ).order_by('-fecha').first()
        
        lista_pacientes.append({
            'id': paciente.codusuario.codigo,
            'nombre': paciente.codusuario.nombre,
            'apellido': paciente.codusuario.apellido,
            'email': paciente.codusuario.correoelectronico,
            'telefono': paciente.codusuario.telefono,
            'fecha_nacimiento': str(paciente.fechanacimiento) if paciente.fechanacimiento else None,
            'estadisticas': {
                'citas_totales': citas_totales,
                'citas_periodo': citas_periodo,
                'planes_totales': planes_totales,
                'planes_activos': planes_activos,
                'ultima_cita': str(ultima_cita.fecha) if ultima_cita else None
            }
        })
    
    reporte = {
        'periodo': {
            'inicio': str(fecha_inicio),
            'fin': str(fecha_fin)
        },
        'total_pacientes': len(lista_pacientes),
        'pacientes': lista_pacientes
    }
    
    return Response(reporte)
