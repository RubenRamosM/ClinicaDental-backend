"""
Serializers para administración clínica (servicios y combos).
"""
from rest_framework import serializers
from .models import Servicio, ComboServicio, ComboServicioDetalle


class ServicioSerializer(serializers.ModelSerializer):
    """Serializer para servicios."""
    
    class Meta:
        model = Servicio
        fields = [
            'id', 'nombre', 'descripcion', 'costobase', 'duracion',
            'activo', 'fecha_creacion', 'fecha_modificacion'
        ]
        read_only_fields = ['fecha_creacion', 'fecha_modificacion']


class ServicioListaSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listas de servicios."""
    
    class Meta:
        model = Servicio
        fields = ['id', 'nombre', 'costobase', 'duracion', 'activo']  # Corregido: campos reales del modelo


class ComboServicioDetalleSerializer(serializers.ModelSerializer):
    """Serializer para detalles de combo."""
    servicio = ServicioListaSerializer(read_only=True)
    servicio_id = serializers.PrimaryKeyRelatedField(
        queryset=Servicio.objects.filter(activo=True),
        source='servicio',
        write_only=True
    )
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True, source='calcular_subtotal')
    
    class Meta:
        model = ComboServicioDetalle
        fields = [
            'id', 'servicio', 'servicio_id', 'cantidad', 'orden', 'subtotal'
        ]


class ComboServicioSerializer(serializers.ModelSerializer):
    """Serializer para combos de servicios."""
    detalles = ComboServicioDetalleSerializer(many=True, read_only=True)
    precio_total_servicios = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True, source='calcular_precio_total_servicios'
    )
    precio_final = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True, source='calcular_precio_final'
    )
    duracion_total = serializers.IntegerField(read_only=True, source='calcular_duracion_total')
    servicios_incluidos = serializers.SerializerMethodField()
    
    class Meta:
        model = ComboServicio
        fields = [
            'id', 'nombre', 'descripcion', 'tipo_precio', 'valor_precio',
            'activo', 'detalles', 'precio_total_servicios', 'precio_final',
            'duracion_total', 'servicios_incluidos',
            'fecha_creacion', 'fecha_modificacion'
        ]
        read_only_fields = ['fecha_creacion', 'fecha_modificacion']
    
    def get_servicios_incluidos(self, obj):
        """Retorna cantidad de servicios en el combo."""
        return obj.detalles.count()


class ComboServicioCrearSerializer(serializers.ModelSerializer):
    """Serializer para crear combos con sus detalles."""
    detalles = ComboServicioDetalleSerializer(many=True)
    
    class Meta:
        model = ComboServicio
        fields = [
            'nombre', 'descripcion', 'tipo_precio', 'valor_precio',
            'activo', 'detalles'
        ]
    
    def validate_detalles(self, value):
        """Validar que el combo tenga al menos 2 servicios."""
        if len(value) < 2:
            raise serializers.ValidationError(
                "Un combo debe tener al menos 2 servicios."
            )
        return value
    
    def validate_valor_precio(self, value):
        """Validar que el valor sea positivo."""
        if value < 0:
            raise serializers.ValidationError(
                "El valor del precio no puede ser negativo."
            )
        return value
    
    def create(self, validated_data):
        """Crear combo con sus detalles."""
        detalles_data = validated_data.pop('detalles')
        combo = ComboServicio.objects.create(**validated_data)
        
        for detalle_data in detalles_data:
            ComboServicioDetalle.objects.create(
                combo=combo,
                **detalle_data
            )
        
        return combo


class ComboServicioActualizarSerializer(serializers.ModelSerializer):
    """Serializer para actualizar combos."""
    detalles = ComboServicioDetalleSerializer(many=True, required=False)
    
    class Meta:
        model = ComboServicio
        fields = [
            'nombre', 'descripcion', 'tipo_precio', 'valor_precio',
            'activo', 'detalles'
        ]
    
    def update(self, instance, validated_data):
        """Actualizar combo y sus detalles."""
        detalles_data = validated_data.pop('detalles', None)
        
        # Actualizar campos del combo
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Si se proporcionan detalles, reemplazar todos
        if detalles_data is not None:
            instance.detalles.all().delete()
            for detalle_data in detalles_data:
                ComboServicioDetalle.objects.create(
                    combo=instance,
                    **detalle_data
                )
        
        return instance
