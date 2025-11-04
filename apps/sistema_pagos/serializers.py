"""
Serializers para sistema de pagos.
NOTA: Adaptado a los modelos existentes en la base de datos
"""
from rest_framework import serializers
from .models import (
    Tipopago, Estadodefactura, Factura, Itemdefactura,
    Pago, PagoEnLinea
)


class TipopagoSerializer(serializers.ModelSerializer):
    """Serializer para tipos de pago."""
    
    class Meta:
        model = Tipopago
        fields = ['id', 'nombrepago']


class EstadodefacturaSerializer(serializers.ModelSerializer):
    """Serializer para estados de factura."""
    
    class Meta:
        model = Estadodefactura
        fields = ['id', 'estado']


class ItemdefacturaSerializer(serializers.ModelSerializer):
    """Serializer para items de factura."""
    
    class Meta:
        model = Itemdefactura
        fields = ['id', 'idfactura', 'descripcion', 'monto']


class FacturaSerializer(serializers.ModelSerializer):
    """Serializer para facturas (modelos existentes)."""
    estado_nombre = serializers.CharField(source='idestadofactura.estado', read_only=True)
    items = ItemdefacturaSerializer(many=True, read_only=True, source='itemdefactura_set')
    
    class Meta:
        model = Factura
        fields = [
            'id', 'fechaemision', 'montototal',
            'idestadofactura', 'estado_nombre', 'items'
        ]


class FacturaCrearSerializer(serializers.ModelSerializer):
    """Serializer simplificado para crear facturas."""
    
    class Meta:
        model = Factura
        fields = ['fechaemision', 'montototal', 'idestadofactura']


class PagoSerializer(serializers.ModelSerializer):
    """Serializer para pagos (modelos existentes)."""
    tipo_pago_nombre = serializers.CharField(source='idtipopago.nombrepago', read_only=True)
    factura_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Pago
        fields = [
            'id', 'idfactura', 'factura_info', 'idtipopago', 
            'tipo_pago_nombre', 'montopagado', 'fechapago'
        ]
    
    def get_factura_info(self, obj):
        return {
            'id': obj.idfactura.id,
            'fecha': obj.idfactura.fechaemision,
            'total': float(obj.idfactura.montototal)
        }


class PagoEnLineaSerializer(serializers.ModelSerializer):
    """Serializer para pagos en línea (Stripe)."""
    
    class Meta:
        model = PagoEnLinea
        fields = [
            'id', 'codigo_pago', 'origen_tipo', 'consulta', 'monto',
            'moneda', 'estado', 'metodo_pago', 'stripe_payment_intent_id',
            'descripcion', 'fecha_creacion'
        ]
        read_only_fields = ['fecha_creacion']


class PagoCrearSerializer(serializers.ModelSerializer):
    """Serializer para registrar un pago."""
    
    class Meta:
        model = Pago
        fields = ['idfactura', 'idtipopago', 'montopagado', 'fechapago']
    
    def validate_montopagado(self, value):
        """Validar que el monto sea positivo."""
        if value <= 0:
            raise serializers.ValidationError('El monto debe ser mayor a 0')
        return value
