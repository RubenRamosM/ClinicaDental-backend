"""
Serializers para gestión de inventario.
"""
from rest_framework import serializers
from apps.historial_clinico.models_inventario import CategoriaInsumo, Proveedor, Insumo, MovimientoInventario, AlertaInventario
from django.utils import timezone
from datetime import timedelta


class CategoriaInsumoSerializer(serializers.ModelSerializer):
    total_insumos = serializers.SerializerMethodField()
    
    class Meta:
        model = CategoriaInsumo
        fields = [
            'id', 'nombre', 'descripcion', 'activo',
            'fecha_creacion', 'total_insumos'
        ]
        read_only_fields = ['fecha_creacion']
    
    def get_total_insumos(self, obj):
        return obj.insumos.filter(activo=True).count()


class ProveedorSerializer(serializers.ModelSerializer):
    total_insumos = serializers.SerializerMethodField()
    
    class Meta:
        model = Proveedor
        fields = [
            'id', 'nombre', 'ruc', 'direccion', 'telefono', 'email',
            'contacto_nombre', 'contacto_telefono', 'activo', 'notas',
            'fecha_registro', 'total_insumos'
        ]
        read_only_fields = ['fecha_registro']
    
    def get_total_insumos(self, obj):
        return obj.insumos.filter(activo=True).count()


class InsumoListSerializer(serializers.ModelSerializer):
    """Serializer ligero para listados."""
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)
    proveedor_nombre = serializers.CharField(source='proveedor_principal.nombre', read_only=True)
    requiere_reposicion = serializers.BooleanField(read_only=True)
    estado_stock = serializers.CharField(read_only=True)
    
    class Meta:
        model = Insumo
        fields = [
            'id', 'codigo', 'nombre', 'categoria', 'categoria_nombre',
            'proveedor_principal', 'proveedor_nombre', 'stock_actual',
            'stock_minimo', 'unidad_medida', 'precio_compra',
            'requiere_reposicion', 'estado_stock', 'activo'
        ]


class InsumoDetailSerializer(serializers.ModelSerializer):
    """Serializer completo con todas las relaciones."""
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)
    proveedor_nombre = serializers.CharField(source='proveedor_principal.nombre', read_only=True)
    requiere_reposicion = serializers.BooleanField(read_only=True)
    estado_stock = serializers.CharField(read_only=True)
    valor_inventario = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    ultimos_movimientos = serializers.SerializerMethodField()
    
    class Meta:
        model = Insumo
        fields = [
            'id', 'codigo', 'nombre', 'descripcion',
            'categoria', 'categoria_nombre',
            'proveedor_principal', 'proveedor_nombre',
            'stock_actual', 'stock_minimo', 'stock_maximo', 'unidad_medida',
            'precio_compra', 'precio_venta',
            'requiere_vencimiento', 'fecha_vencimiento', 'lote', 'ubicacion',
            'requiere_reposicion', 'estado_stock', 'valor_inventario',
            'activo', 'fecha_creacion', 'fecha_actualizacion',
            'ultimos_movimientos'
        ]
        read_only_fields = ['fecha_creacion', 'fecha_actualizacion', 'stock_actual']
    
    def get_ultimos_movimientos(self, obj):
        movimientos = obj.movimientos.all()[:5]
        return MovimientoInventarioListSerializer(movimientos, many=True).data


class InsumoCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para crear/actualizar insumos."""
    
    class Meta:
        model = Insumo
        fields = [
            'codigo', 'nombre', 'descripcion',
            'categoria', 'proveedor_principal',
            'stock_minimo', 'stock_maximo', 'unidad_medida',
            'precio_compra', 'precio_venta',
            'requiere_vencimiento', 'fecha_vencimiento', 'lote', 'ubicacion',
            'activo'
        ]
    
    def validate_codigo(self, value):
        """Validar que el código sea único."""
        if self.instance and self.instance.codigo == value:
            return value
        
        if Insumo.objects.filter(codigo=value).exists():
            raise serializers.ValidationError("Ya existe un insumo con este código.")
        
        return value
    
    def validate(self, data):
        """Validaciones cruzadas."""
        if data.get('stock_minimo', 0) > data.get('stock_maximo', 100):
            raise serializers.ValidationError({
                'stock_minimo': 'El stock mínimo no puede ser mayor al stock máximo.'
            })
        
        if data.get('requiere_vencimiento') and not data.get('fecha_vencimiento'):
            raise serializers.ValidationError({
                'fecha_vencimiento': 'Debe especificar una fecha de vencimiento.'
            })
        
        return data


class MovimientoInventarioListSerializer(serializers.ModelSerializer):
    """Serializer ligero para listados de movimientos."""
    insumo_nombre = serializers.CharField(source='insumo.nombre', read_only=True)
    insumo_codigo = serializers.CharField(source='insumo.codigo', read_only=True)
    proveedor_nombre = serializers.CharField(source='proveedor.nombre', read_only=True)
    realizado_por_nombre = serializers.SerializerMethodField()
    
    class Meta:
        model = MovimientoInventario
        fields = [
            'id', 'insumo', 'insumo_nombre', 'insumo_codigo',
            'tipo_movimiento', 'cantidad', 'stock_anterior', 'stock_nuevo',
            'motivo', 'proveedor', 'proveedor_nombre',
            'costo_unitario', 'costo_total',
            'fecha_movimiento', 'realizado_por', 'realizado_por_nombre'
        ]
        read_only_fields = ['fecha_movimiento', 'stock_anterior', 'stock_nuevo']
    
    def get_realizado_por_nombre(self, obj):
        if obj.realizado_por:
            return f"{obj.realizado_por.nombre} {obj.realizado_por.apellido}"
        return None


class MovimientoInventarioCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear movimientos de inventario."""
    
    class Meta:
        model = MovimientoInventario
        fields = [
            'insumo', 'tipo_movimiento', 'cantidad', 'motivo',
            'proveedor', 'numero_factura', 'costo_unitario', 'notas'
        ]
    
    def validate(self, data):
        """Validaciones según tipo de movimiento."""
        insumo = data.get('insumo')
        tipo = data.get('tipo_movimiento')
        cantidad = data.get('cantidad')
        
        # Para salidas, verificar que haya stock suficiente
        if tipo in ['salida', 'merma']:
            if insumo.stock_actual < cantidad:
                raise serializers.ValidationError({
                    'cantidad': f'Stock insuficiente. Stock actual: {insumo.stock_actual}'
                })
        
        # Para entradas desde proveedor, requerir datos de compra
        if tipo == 'entrada' and data.get('proveedor'):
            if not data.get('costo_unitario'):
                raise serializers.ValidationError({
                    'costo_unitario': 'Debe especificar el costo unitario para compras.'
                })
        
        return data
    
    def create(self, validated_data):
        """Agregar usuario que realiza el movimiento."""
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            # Obtener Usuario desde auth user
            from apps.usuarios.models import Usuario
            try:
                usuario = Usuario.objects.get(correoelectronico=request.user.email)
                validated_data['realizado_por'] = usuario
            except Usuario.DoesNotExist:
                pass
        
        return super().create(validated_data)


class AlertaInventarioSerializer(serializers.ModelSerializer):
    insumo_nombre = serializers.CharField(source='insumo.nombre', read_only=True)
    insumo_codigo = serializers.CharField(source='insumo.codigo', read_only=True)
    stock_actual = serializers.DecimalField(
        source='insumo.stock_actual',
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    
    class Meta:
        model = AlertaInventario
        fields = [
            'id', 'insumo', 'insumo_nombre', 'insumo_codigo',
            'tipo_alerta', 'mensaje', 'prioridad', 'stock_actual',
            'resuelta', 'fecha_creacion', 'fecha_resolucion'
        ]
        read_only_fields = ['fecha_creacion']


class ReporteInventarioSerializer(serializers.Serializer):
    """Serializer para reportes de inventario."""
    total_insumos = serializers.IntegerField()
    insumos_activos = serializers.IntegerField()
    insumos_stock_bajo = serializers.IntegerField()
    insumos_agotados = serializers.IntegerField()
    valor_total_inventario = serializers.DecimalField(max_digits=12, decimal_places=2)
    categorias = serializers.ListField()
    alertas_pendientes = serializers.IntegerField()
