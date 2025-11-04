"""
Generación de reportes clínicos y estadísticas.
CU25: Reportes Clínicos
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, Avg, Sum, Q, F
from django.utils import timezone
from datetime import timedelta, datetime
from decimal import Decimal

from apps.citas.models import Consulta
from apps.usuarios.models import Paciente
from apps.historial_clinico.models import Historialclinico
from apps.sistema_pagos.models import Factura


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def estadisticas_generales(request):
    """
    Retorna estadísticas generales de la clínica.
    
    GET /api/v1/reportes/estadisticas/
    
    Query params opcionales:
    - fecha_inicio: YYYY-MM-DD
    - fecha_fin: YYYY-MM-DD
    - periodo: 'mes', 'trimestre', 'anio' (por defecto: mes actual)
    """
    # Determinar rango de fechas
    fecha_fin = timezone.now().date()
    periodo = request.query_params.get('periodo', 'mes')
    
    if request.query_params.get('fecha_inicio') and request.query_params.get('fecha_fin'):
        fecha_inicio = datetime.strptime(request.query_params['fecha_inicio'], '%Y-%m-%d').date()
        fecha_fin = datetime.strptime(request.query_params['fecha_fin'], '%Y-%m-%d').date()
    elif periodo == 'mes':
        fecha_inicio = fecha_fin.replace(day=1)
    elif periodo == 'trimestre':
        mes_inicio = ((fecha_fin.month - 1) // 3) * 3 + 1
        fecha_inicio = fecha_fin.replace(month=mes_inicio, day=1)
    elif periodo == 'anio':
        fecha_inicio = fecha_fin.replace(month=1, day=1)
    else:
        fecha_inicio = fecha_fin - timedelta(days=30)
    
    # Estadísticas de Consultas
    consultas_periodo = Consulta.objects.filter(fecha__range=[fecha_inicio, fecha_fin])
    
    estadisticas_consultas = {
        'total_consultas': consultas_periodo.count(),
        'consultas_completadas': consultas_periodo.filter(estado='completada').count(),
        'consultas_canceladas': consultas_periodo.filter(estado='cancelada').count(),
        'consultas_no_asistio': consultas_periodo.filter(estado='no_asistio').count(),
        'consultas_pendientes': consultas_periodo.filter(estado='pendiente').count(),
        'consultas_por_tipo': list(
            consultas_periodo.values('tipo_consulta')
            .annotate(cantidad=Count('id'))
            .order_by('-cantidad')
        ),
        'tasa_asistencia': _calcular_tasa_asistencia(consultas_periodo),
    }
    
    # Estadísticas de Pacientes
    estadisticas_pacientes = {
        'total_pacientes': Paciente.objects.count(),
        'pacientes_nuevos_periodo': Paciente.objects.filter(
            fechainscripcion__range=[fecha_inicio, fecha_fin]
        ).count(),
        'pacientes_activos': Paciente.objects.filter(
            codusuario__consulta__fecha__range=[fecha_inicio, fecha_fin]
        ).distinct().count(),
    }
    
    # Estadísticas Financieras
    facturas_periodo = Factura.objects.filter(
        fechafacturacion__range=[fecha_inicio, fecha_fin]
    )
    
    estadisticas_financieras = {
        'ingresos_totales': float(facturas_periodo.aggregate(
            total=Sum('montototal')
        )['total'] or 0),
        'facturas_emitidas': facturas_periodo.count(),
        'facturas_pagadas': facturas_periodo.filter(estadopago='pagado').count(),
        'facturas_pendientes': facturas_periodo.filter(estadopago='pendiente').count(),
        'ticket_promedio': float(facturas_periodo.aggregate(
            promedio=Avg('montototal')
        )['promedio'] or 0),
    }
    
    return Response({
        'periodo': {
            'fecha_inicio': fecha_inicio.isoformat(),
            'fecha_fin': fecha_fin.isoformat(),
            'tipo_periodo': periodo
        },
        'consultas': estadisticas_consultas,
        'pacientes': estadisticas_pacientes,
        'financiero': estadisticas_financieras,
        'fecha_generacion': timezone.now().isoformat(),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def reporte_productividad_odontologos(request):
    """
    Reporte de productividad de odontólogos.
    
    GET /api/v1/reportes/odontologos/productividad/
    """
    fecha_inicio = request.query_params.get('fecha_inicio')
    fecha_fin = request.query_params.get('fecha_fin')
    
    if not fecha_inicio or not fecha_fin:
        fecha_fin = timezone.now().date()
        fecha_inicio = fecha_fin - timedelta(days=30)
    else:
        fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
    
    # Productividad por odontólogo
    from apps.profesionales.models import Odontologo
    
    odontologos = Odontologo.objects.all()
    reporte = []
    
    for odontologo in odontologos:
        consultas = Consulta.objects.filter(
            cododontologo=odontologo,
            fecha__range=[fecha_inicio, fecha_fin]
        )
        
        reporte.append({
            'odontologo_id': odontologo.codigo,
            'nombre': f"{odontologo.codusuario.nombre} {odontologo.codusuario.apellido}",
            'especialidad': odontologo.especialidad,
            'consultas_realizadas': consultas.filter(estado='completada').count(),
            'consultas_canceladas': consultas.filter(estado='cancelada').count(),
            'horas_trabajadas': _calcular_horas_trabajadas(consultas),
            'pacientes_atendidos': consultas.values('codpaciente').distinct().count(),
            'ingresos_generados': float(_calcular_ingresos_odontologo(odontologo, fecha_inicio, fecha_fin)),
            'tasa_completitud': _calcular_tasa_completitud(consultas),
        })
    
    return Response({
        'periodo': {
            'fecha_inicio': fecha_inicio.isoformat(),
            'fecha_fin': fecha_fin.isoformat()
        },
        'odontologos': sorted(reporte, key=lambda x: x['consultas_realizadas'], reverse=True),
        'fecha_generacion': timezone.now().isoformat(),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def reporte_ingresos_mensuales(request):
    """
    Reporte de ingresos mensuales desglosados.
    
    GET /api/v1/reportes/ingresos/mensuales/
    """
    anio = int(request.query_params.get('anio', timezone.now().year))
    
    ingresos_por_mes = []
    
    for mes in range(1, 13):
        fecha_inicio = datetime(anio, mes, 1).date()
        if mes == 12:
            fecha_fin = datetime(anio, 12, 31).date()
        else:
            fecha_fin = datetime(anio, mes + 1, 1).date() - timedelta(days=1)
        
        facturas_mes = Factura.objects.filter(
            fechafacturacion__range=[fecha_inicio, fecha_fin]
        )
        
        ingresos_por_mes.append({
            'mes': mes,
            'nombre_mes': fecha_inicio.strftime('%B'),
            'ingresos_totales': float(facturas_mes.aggregate(
                total=Sum('montototal')
            )['total'] or 0),
            'facturas': facturas_mes.count(),
            'promedio_diario': float(facturas_mes.aggregate(
                promedio=Avg('montototal')
            )['promedio'] or 0),
        })
    
    return Response({
        'anio': anio,
        'ingresos_mensuales': ingresos_por_mes,
        'total_anual': sum(m['ingresos_totales'] for m in ingresos_por_mes),
        'promedio_mensual': sum(m['ingresos_totales'] for m in ingresos_por_mes) / 12,
        'fecha_generacion': timezone.now().isoformat(),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def reporte_pacientes_frecuentes(request):
    """
    Reporte de pacientes con más consultas.
    
    GET /api/v1/reportes/pacientes/frecuentes/
    """
    limite = int(request.query_params.get('limite', 20))
    fecha_inicio = request.query_params.get('fecha_inicio')
    fecha_fin = request.query_params.get('fecha_fin')
    
    consultas_query = Consulta.objects.all()
    
    if fecha_inicio and fecha_fin:
        fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
        consultas_query = consultas_query.filter(fecha__range=[fecha_inicio, fecha_fin])
    
    # Pacientes más frecuentes
    pacientes_frecuentes = (
        consultas_query
        .values('codpaciente', 'codpaciente__codusuario__nombre', 'codpaciente__codusuario__apellido')
        .annotate(
            total_consultas=Count('id'),
            consultas_completadas=Count('id', filter=Q(estado='completada')),
            ultima_consulta=F('fecha')
        )
        .order_by('-total_consultas')[:limite]
    )
    
    reporte = []
    for p in pacientes_frecuentes:
        reporte.append({
            'paciente_id': p['codpaciente'],
            'nombre': f"{p['codpaciente__codusuario__nombre']} {p['codpaciente__codusuario__apellido']}",
            'total_consultas': p['total_consultas'],
            'consultas_completadas': p['consultas_completadas'],
            'ultima_consulta': p['ultima_consulta'].isoformat() if p['ultima_consulta'] else None,
        })
    
    return Response({
        'pacientes_frecuentes': reporte,
        'total_registros': len(reporte),
        'fecha_generacion': timezone.now().isoformat(),
    })


# === Funciones auxiliares ===

def _calcular_tasa_asistencia(consultas):
    """Calcula el porcentaje de asistencia a consultas."""
    total = consultas.count()
    if total == 0:
        return 0.0
    
    asistencias = consultas.filter(
        estado__in=['completada', 'en_consulta', 'diagnosticada']
    ).count()
    
    return round((asistencias / total) * 100, 2)


def _calcular_horas_trabajadas(consultas):
    """Calcula las horas trabajadas basado en duración de consultas."""
    total_minutos = consultas.aggregate(
        total=Sum('duracion_estimada')
    )['total'] or 0
    
    return round(total_minutos / 60, 2)


def _calcular_ingresos_odontologo(odontologo, fecha_inicio, fecha_fin):
    """Calcula ingresos generados por un odontólogo en un periodo."""
    facturas = Factura.objects.filter(
        codpaciente__consulta__cododontologo=odontologo,
        fechafacturacion__range=[fecha_inicio, fecha_fin]
    )
    
    return facturas.aggregate(total=Sum('montototal'))['total'] or Decimal('0.00')


def _calcular_tasa_completitud(consultas):
    """Calcula el porcentaje de consultas completadas."""
    total = consultas.count()
    if total == 0:
        return 0.0
    
    completadas = consultas.filter(estado='completada').count()
    return round((completadas / total) * 100, 2)
