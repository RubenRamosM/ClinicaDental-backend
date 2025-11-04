"""
Views para sistema de pagos.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q, Sum

from .models import (
    Tipopago, Estadodefactura, Factura, Pago, PagoEnLinea
)
from .serializers import (
    TipopagoSerializer, EstadodefacturaSerializer,
    FacturaSerializer, FacturaCrearSerializer,
    PagoSerializer, PagoCrearSerializer, PagoEnLineaSerializer
)
from apps.comun.permisos import EsStaff, EsAdministrador


class TipopagoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para tipos de pago.
    
    GET /api/v1/pagos/tipos-pago/
    """
    queryset = Tipopago.objects.all()
    serializer_class = TipopagoSerializer
    permission_classes = [IsAuthenticated]


class EstadodefacturaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para estados de factura.
    
    GET /api/v1/pagos/estados-factura/
    """
    queryset = Estadodefactura.objects.all()
    serializer_class = EstadodefacturaSerializer
    permission_classes = [IsAuthenticated]


class FacturaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de facturas.
    """
    queryset = Factura.objects.all()
    serializer_class = FacturaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['idestadofactura']
    search_fields = ['id']
    ordering_fields = ['fechaemision', 'montototal']
    ordering = ['-fechaemision']
    
    def get_serializer_class(self):
        """Seleccionar serializer según acción."""
        if self.action == 'create':
            return FacturaCrearSerializer
        return FacturaSerializer
    
    @action(detail=False, methods=['get'])
    def pendientes(self, request):
        """Listar facturas pendientes de pago."""
        # Buscar estado "pendiente" 
        estado_pendiente = Estadodefactura.objects.filter(
            estado__icontains='pendiente'
        ).first()
        
        if estado_pendiente:
            facturas = self.queryset.filter(idestadofactura=estado_pendiente)
        else:
            facturas = self.queryset.none()
        
        serializer = self.get_serializer(facturas, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def historial_pagos(self, request, pk=None):
        """Ver historial de pagos de una factura."""
        factura = self.get_object()
        pagos = Pago.objects.filter(idfactura=factura)
        
        serializer = PagoSerializer(pagos, many=True)
        total_pagado = pagos.aggregate(Sum('montopagado'))['montopagado__sum'] or 0
        
        return Response({
            'factura': FacturaSerializer(factura).data,
            'pagos': serializer.data,
            'total_pagado': float(total_pagado),
            'saldo_pendiente': float(factura.montototal - total_pagado)
        })


class PagoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de pagos.
    """
    queryset = Pago.objects.all()
    serializer_class = PagoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['idfactura', 'idtipopago']
    search_fields = ['id']
    ordering_fields = ['fechapago', 'montopagado']
    ordering = ['-fechapago']
    
    def get_serializer_class(self):
        """Seleccionar serializer según acción."""
        if self.action == 'create':
            return PagoCrearSerializer
        return PagoSerializer
    
    def perform_create(self, serializer):
        """Registrar pago y actualizar estado de factura."""
        pago = serializer.save()
        
        # Calcular total pagado de la factura
        factura = pago.idfactura
        total_pagado = Pago.objects.filter(idfactura=factura).aggregate(
            Sum('montopagado')
        )['montopagado__sum'] or 0
        
        # Actualizar estado si está completamente pagada
        if total_pagado >= factura.montototal:
            estado_pagada = Estadodefactura.objects.filter(
                estado__icontains='pagada'
            ).first()
            if estado_pagada:
                factura.idestadofactura = estado_pagada
                factura.save()
    
    @action(detail=False, methods=['get'])
    def resumen(self, request):
        """Resumen de pagos del día/mes."""
        from django.utils import timezone
        
        hoy = timezone.now().date()
        inicio_mes = hoy.replace(day=1)
        
        # Pagos de hoy
        pagos_hoy = self.queryset.filter(fechapago=hoy)
        total_hoy = pagos_hoy.aggregate(Sum('montopagado'))['montopagado__sum'] or 0
        
        # Pagos del mes
        pagos_mes = self.queryset.filter(
            fechapago__gte=inicio_mes,
            fechapago__lte=hoy
        )
        total_mes = pagos_mes.aggregate(Sum('montopagado'))['montopagado__sum'] or 0
        
        return Response({
            'hoy': {
                'cantidad': pagos_hoy.count(),
                'total': float(total_hoy)
            },
            'mes_actual': {
                'cantidad': pagos_mes.count(),
                'total': float(total_mes)
            }
        })
    
    @action(detail=False, methods=['get'])
    def pendientes(self, request):
        """Pagos pendientes (facturas con saldo pendiente)."""
        # Obtener facturas con estado pendiente
        estado_pendiente = Estadodefactura.objects.filter(estado__icontains='pendiente').first()
        if estado_pendiente:
            facturas_pendientes = Factura.objects.filter(idestadofactura=estado_pendiente)
            pagos = self.queryset.filter(idfactura__in=facturas_pendientes)
        else:
            pagos = self.queryset.none()
        
        serializer = self.get_serializer(pagos, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def hoy(self, request):
        """Pagos realizados hoy."""
        from django.utils import timezone
        hoy = timezone.now().date()
        pagos = self.queryset.filter(fechapago=hoy)
        serializer = self.get_serializer(pagos, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='resumen-ingresos')
    def resumen_ingresos(self, request):
        """Resumen de ingresos por período."""
        from django.utils import timezone
        from datetime import timedelta
        
        hoy = timezone.now().date()
        inicio_mes = hoy.replace(day=1)
        inicio_semana = hoy - timedelta(days=hoy.weekday())
        
        # Ingresos de hoy
        total_hoy = self.queryset.filter(fechapago=hoy).aggregate(
            Sum('montopagado'))['montopagado__sum'] or 0
        
        # Ingresos de la semana
        total_semana = self.queryset.filter(
            fechapago__gte=inicio_semana).aggregate(
            Sum('montopagado'))['montopagado__sum'] or 0
        
        # Ingresos del mes
        total_mes = self.queryset.filter(
            fechapago__gte=inicio_mes).aggregate(
            Sum('montopagado'))['montopagado__sum'] or 0
        
        return Response({
            'hoy': float(total_hoy),
            'semana': float(total_semana),
            'mes': float(total_mes)
        })


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


# ============================================================================
# STRIPE INTEGRATION - Payment Intents for Consultas
# ============================================================================

from rest_framework.decorators import api_view, permission_classes
from django.conf import settings
import stripe
import uuid
from decimal import Decimal

# Configurar API key de Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def crear_intencion_pago_consulta(request):
    """
    Crear Payment Intent en Stripe para pagar una consulta/cita.
    
    POST /api/v1/pagos/stripe/crear-intencion-consulta/
    
    Body:
    {
        "tipo_consulta_id": 198,
        "monto": 150.00  // Opcional, si no se envía se toma del tipo de consulta
    }
    
    Response:
    {
        "client_secret": "pi_xxx_secret_xxx",
        "pago_id": 123,
        "monto": 150.00,
        "moneda": "BOB"
    }
    """
    try:
        tipo_consulta_id = request.data.get('tipo_consulta_id')
        monto = request.data.get('monto')
        
        if not tipo_consulta_id:
            return Response({
                'error': 'El campo tipo_consulta_id es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Obtener tipo de consulta
        from apps.citas.models import Tipodeconsulta
        try:
            tipo_consulta = Tipodeconsulta.objects.get(id=tipo_consulta_id)
        except Tipodeconsulta.DoesNotExist:
            return Response({
                'error': 'Tipo de consulta no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Usar monto del tipo de consulta si no se proporciona
        if not monto:
            # Verificar si el modelo tiene campo costo o precio
            if hasattr(tipo_consulta, 'costo'):
                monto = tipo_consulta.costo
            elif hasattr(tipo_consulta, 'precio'):
                monto = tipo_consulta.precio
            else:
                # Monto por defecto si no hay campo en el modelo
                monto = Decimal('100.00')
        
        monto = Decimal(str(monto))
        
        # Generar código único de pago
        codigo_pago = f"CITA-{uuid.uuid4().hex[:8].upper()}"
        
        # Crear Payment Intent en Stripe
        # Nota: Stripe maneja montos en centavos
        intent = stripe.PaymentIntent.create(
            amount=int(monto * 100),  # Convertir a centavos
            currency='bob',  # Bolivianos
            metadata={
                'tipo_consulta_id': tipo_consulta_id,
                'tipo_consulta_nombre': tipo_consulta.nombreconsulta,
                'usuario_id': request.user.id,
                'usuario_email': request.user.email,
                'codigo_pago': codigo_pago,
            },
            description=f"Pago consulta: {tipo_consulta.nombreconsulta}",
        )
        
        # Crear registro en base de datos
        pago = PagoEnLinea.objects.create(
            codigo_pago=codigo_pago,
            origen_tipo='consulta',
            monto=monto,
            moneda='BOB',
            monto_original=monto,
            saldo_anterior=Decimal('0.00'),
            saldo_nuevo=Decimal('0.00'),
            estado='pendiente',
            metodo_pago='tarjeta',
            stripe_payment_intent_id=intent.id,
            stripe_metadata={
                'tipo_consulta_id': tipo_consulta_id,
                'tipo_consulta_nombre': tipo_consulta.nombreconsulta,
            },
            descripcion=f"Pago por consulta: {tipo_consulta.nombreconsulta}",
        )
        
        return Response({
            'client_secret': intent.client_secret,
            'pago_id': pago.id,
            'codigo_pago': codigo_pago,
            'monto': float(monto),
            'moneda': 'BOB',
            'tipo_consulta': tipo_consulta.nombreconsulta,
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': f'Error al crear intención de pago: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirmar_pago_consulta(request):
    """
    Confirmar que un pago fue exitoso y actualizar el estado.
    
    POST /api/v1/pagos/stripe/confirmar-pago/
    
    Body:
    {
        "pago_id": 123,
        "payment_intent_id": "pi_xxx"  // Opcional
    }
    
    Response:
    {
        "success": true,
        "pago": {...},
        "mensaje": "Pago confirmado exitosamente"
    }
    """
    try:
        pago_id = request.data.get('pago_id')
        payment_intent_id = request.data.get('payment_intent_id')
        
        if not pago_id:
            return Response({
                'error': 'El campo pago_id es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Obtener pago
        try:
            pago = PagoEnLinea.objects.get(id=pago_id)
        except PagoEnLinea.DoesNotExist:
            return Response({
                'error': 'Pago no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Verificar estado en Stripe
        if payment_intent_id or pago.stripe_payment_intent_id:
            intent_id = payment_intent_id or pago.stripe_payment_intent_id
            
            try:
                intent = stripe.PaymentIntent.retrieve(intent_id)
                
                if intent.status == 'succeeded':
                    pago.estado = 'aprobado'
                    # Verificar si hay charges disponibles
                    if hasattr(intent, 'charges') and intent.charges and hasattr(intent.charges, 'data') and len(intent.charges.data) > 0:
                        pago.stripe_charge_id = intent.charges.data[0].id
                    pago.numero_intentos += 1
                    pago.save()
                    
                    return Response({
                        'success': True,
                        'pago': PagoEnLineaSerializer(pago).data,
                        'mensaje': 'Pago confirmado exitosamente'
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'success': False,
                        'estado_stripe': intent.status,
                        'mensaje': f'El pago está en estado: {intent.status}'
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
            except stripe.error.StripeError as e:
                return Response({
                    'error': f'Error de Stripe: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        else:
            return Response({
                'error': 'No se encontró payment_intent_id'
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        return Response({
            'error': f'Error al confirmar pago: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_clave_publica_stripe(request):
    """
    Obtener clave pública de Stripe para el frontend.
    
    GET /api/v1/pagos/stripe/clave-publica/
    
    Response:
    {
        "publishable_key": "pk_test_xxx"
    }
    """
    return Response({
        'publishable_key': settings.STRIPE_PUBLIC_KEY
    })


# ============================================================================
# STRIPE INTEGRATION - Payment Intents for Presupuestos/Tratamientos
# ============================================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def crear_intencion_pago_presupuesto(request):
    """
    Crear Payment Intent en Stripe para pagar un presupuesto/tratamiento.
    
    POST /api/v1/pagos/stripe/crear-intencion-presupuesto/
    
    Body:
    {
        "presupuesto_id": 123,
        "monto": 1500.00  // Opcional, si no se envía se toma el total del presupuesto
    }
    
    Response:
    {
        "client_secret": "pi_xxx_secret_xxx",
        "pago_id": 456,
        "codigo_pago": "PRES-XXXXXXXX",
        "monto": 1500.00,
        "moneda": "BOB",
        "presupuesto": {...}
    }
    """
    try:
        presupuesto_id = request.data.get('presupuesto_id')
        monto = request.data.get('monto')
        
        if not presupuesto_id:
            return Response({
                'error': 'El campo presupuesto_id es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Obtener presupuesto
        from apps.tratamientos.models import Presupuesto
        try:
            presupuesto = Presupuesto.objects.get(id=presupuesto_id)
        except Presupuesto.DoesNotExist:
            return Response({
                'error': 'Presupuesto no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Verificar que el presupuesto esté pendiente o aprobado
        if presupuesto.estado not in ['pendiente', 'aprobado']:
            return Response({
                'error': f'No se puede pagar un presupuesto en estado: {presupuesto.estado}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Usar monto total del presupuesto si no se proporciona
        if not monto:
            monto = presupuesto.total
        
        monto = Decimal(str(monto))
        
        # Validar que el monto no sea mayor al total del presupuesto
        if monto > presupuesto.total:
            return Response({
                'error': f'El monto a pagar ({monto}) no puede ser mayor al total del presupuesto ({presupuesto.total})'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Generar código único de pago
        codigo_pago = f"PRES-{uuid.uuid4().hex[:8].upper()}"
        
        # Crear Payment Intent en Stripe
        intent = stripe.PaymentIntent.create(
            amount=int(monto * 100),  # Convertir a centavos
            currency='bob',  # Bolivianos
            metadata={
                'presupuesto_id': presupuesto_id,
                'presupuesto_codigo': presupuesto.codigo,
                'usuario_id': request.user.id,
                'usuario_email': request.user.email,
                'codigo_pago': codigo_pago,
                'tipo': 'presupuesto',
            },
            description=f"Pago presupuesto: {presupuesto.codigo}",
        )
        
        # Crear registro en base de datos
        pago = PagoEnLinea.objects.create(
            codigo_pago=codigo_pago,
            origen_tipo='plan_completo',  # O 'items_individuales' según el caso
            monto=monto,
            moneda='BOB',
            monto_original=monto,
            saldo_anterior=Decimal('0.00'),
            saldo_nuevo=Decimal('0.00'),
            estado='pendiente',
            metodo_pago='tarjeta',
            stripe_payment_intent_id=intent.id,
            stripe_metadata={
                'presupuesto_id': presupuesto_id,
                'presupuesto_codigo': presupuesto.codigo,
                'total_presupuesto': str(presupuesto.total),
            },
            descripcion=f"Pago presupuesto: {presupuesto.codigo} - Total: Bs. {presupuesto.total}",
        )
        
        return Response({
            'client_secret': intent.client_secret,
            'pago_id': pago.id,
            'codigo_pago': codigo_pago,
            'monto': float(monto),
            'moneda': 'BOB',
            'presupuesto': {
                'id': presupuesto.id,
                'codigo': presupuesto.codigo,
                'total': float(presupuesto.total),
                'estado': presupuesto.estado,
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': f'Error al crear intención de pago: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirmar_pago_presupuesto(request):
    """
    Confirmar que un pago de presupuesto fue exitoso y actualizar el estado.
    
    POST /api/v1/pagos/stripe/confirmar-pago-presupuesto/
    
    Body:
    {
        "pago_id": 456,
        "presupuesto_id": 123,
        "payment_intent_id": "pi_xxx"  // Opcional
    }
    
    Response:
    {
        "success": true,
        "pago": {...},
        "presupuesto": {...},
        "mensaje": "Pago confirmado y presupuesto aprobado"
    }
    """
    try:
        pago_id = request.data.get('pago_id')
        presupuesto_id = request.data.get('presupuesto_id')
        payment_intent_id = request.data.get('payment_intent_id')
        
        if not pago_id:
            return Response({
                'error': 'El campo pago_id es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not presupuesto_id:
            return Response({
                'error': 'El campo presupuesto_id es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Obtener pago
        try:
            pago = PagoEnLinea.objects.get(id=pago_id)
        except PagoEnLinea.DoesNotExist:
            return Response({
                'error': 'Pago no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Obtener presupuesto
        from apps.tratamientos.models import Presupuesto
        try:
            presupuesto = Presupuesto.objects.get(id=presupuesto_id)
        except Presupuesto.DoesNotExist:
            return Response({
                'error': 'Presupuesto no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Verificar estado en Stripe
        if payment_intent_id or pago.stripe_payment_intent_id:
            intent_id = payment_intent_id or pago.stripe_payment_intent_id
            
            try:
                intent = stripe.PaymentIntent.retrieve(intent_id)
                
                if intent.status == 'succeeded':
                    # Actualizar pago
                    pago.estado = 'aprobado'
                    pago.stripe_charge_id = intent.charges.data[0].id if intent.charges.data else None
                    pago.numero_intentos += 1
                    pago.save()
                    
                    # Aprobar presupuesto automáticamente
                    if presupuesto.estado == 'pendiente':
                        presupuesto.estado = 'aprobado'
                        presupuesto.save()
                    
                    # Crear registro de pago en el modelo Pago (si existe)
                    # TODO: Vincular con el sistema de pagos interno si es necesario
                    
                    return Response({
                        'success': True,
                        'pago': PagoEnLineaSerializer(pago).data,
                        'presupuesto': {
                            'id': presupuesto.id,
                            'codigo': presupuesto.codigo,
                            'estado': presupuesto.estado,
                            'total': float(presupuesto.total),
                        },
                        'mensaje': 'Pago confirmado exitosamente. El presupuesto ha sido aprobado.'
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'success': False,
                        'estado_stripe': intent.status,
                        'mensaje': f'El pago está en estado: {intent.status}'
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
            except stripe.error.StripeError as e:
                return Response({
                    'error': f'Error de Stripe: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        else:
            return Response({
                'error': 'No se encontró payment_intent_id'
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        return Response({
            'error': f'Error al confirmar pago: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

