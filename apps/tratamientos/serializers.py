from rest_framework import serializers
from decimal import Decimal
from .models import PlanTratamiento, Presupuesto, ItemPresupuesto, Procedimiento, HistorialPago, SesionTratamiento
from apps.usuarios.models import Paciente
from apps.profesionales.models import Odontologo
from apps.administracion_clinica.models import Servicio


class ProcedimientoSerializer(serializers.ModelSerializer):
    """Serializer para procedimientos"""
    servicio_nombre = serializers.CharField(source='servicio.nombre', read_only=True)
    odontologo_nombre = serializers.SerializerMethodField()
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    # ✅ AGREGADO: Alias para compatibilidad con frontend
    costofinal = serializers.DecimalField(source='costo_estimado', max_digits=10, decimal_places=2, read_only=True)
    estado_item = serializers.CharField(source='get_estado_display', read_only=True)  # Alias de estado_display

    class Meta:
        model = Procedimiento
        fields = [
            'id', 'plan_tratamiento', 'servicio', 'servicio_nombre',
            'odontologo', 'odontologo_nombre', 'numero_diente',
            'descripcion', 'estado', 'estado_display', 'estado_item',
            'fecha_planificada', 'fecha_realizado', 'duracion_minutos',
            'costo_estimado', 'costofinal', 'costo_real', 'notas', 'complicaciones'
        ]
        read_only_fields = ['fecha_realizado']

    def get_odontologo_nombre(self, obj):
        if obj.odontologo and obj.odontologo.codusuario:
            return f"{obj.odontologo.codusuario.nombre} {obj.odontologo.codusuario.apellido}"
        return None


class ProcedimientoCrearSerializer(serializers.ModelSerializer):
    """Serializer para crear procedimientos"""
    class Meta:
        model = Procedimiento
        fields = [
            'plan_tratamiento', 'servicio', 'odontologo', 'numero_diente',
            'descripcion', 'fecha_planificada', 'duracion_minutos', 'costo_estimado', 'notas'
        ]

    def validate(self, data):
        # Validar número de diente si se proporciona
        if data.get('numero_diente') and (data['numero_diente'] < 1 or data['numero_diente'] > 32):
            raise serializers.ValidationError({
                'numero_diente': 'Debe ser un número entre 1 y 32'
            })
        return data


class ItemPresupuestoSerializer(serializers.ModelSerializer):
    """Serializer para items de presupuesto"""
    servicio_nombre = serializers.CharField(source='servicio.nombre', read_only=True)
    total_calculado = serializers.SerializerMethodField()

    class Meta:
        model = ItemPresupuesto
        fields = [
            'id', 'presupuesto', 'servicio', 'servicio_nombre',
            'descripcion', 'cantidad', 'precio_unitario',
            'descuento_item', 'total', 'total_calculado', 'numero_diente'
        ]
        read_only_fields = ['total']

    def get_total_calculado(self, obj):
        return obj.total


class ItemPresupuestoCrearSerializer(serializers.ModelSerializer):
    """Serializer para crear items de presupuesto"""
    class Meta:
        model = ItemPresupuesto
        fields = [
            'servicio', 'descripcion', 'cantidad',
            'precio_unitario', 'descuento_item', 'numero_diente'
        ]

    def validate(self, data):
        # Validar número de diente si se proporciona
        if data.get('numero_diente') and (data['numero_diente'] < 1 or data['numero_diente'] > 32):
            raise serializers.ValidationError({
                'numero_diente': 'Debe ser un número entre 1 y 32'
            })
        # Validar que precio_unitario sea positivo
        if data.get('precio_unitario') and data['precio_unitario'] < 0:
            raise serializers.ValidationError({
                'precio_unitario': 'Debe ser mayor o igual a 0'
            })
        return data


class PresupuestoSerializer(serializers.ModelSerializer):
    """Serializer para presupuestos con items"""
    items = ItemPresupuestoSerializer(many=True, read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    paciente_nombre = serializers.SerializerMethodField()
    odontologo_nombre = serializers.SerializerMethodField()
    plan_codigo = serializers.CharField(source='plan_tratamiento.codigo', read_only=True)

    class Meta:
        model = Presupuesto
        fields = [
            'id', 'plan_tratamiento', 'plan_codigo', 'codigo',
            'subtotal', 'descuento', 'impuesto', 'total',
            'estado', 'estado_display', 'notas',
            'fecha_creacion', 'fecha_vencimiento', 'fecha_aprobacion',
            'aprobado_por', 'motivo_rechazo', 'items', 
            'paciente_nombre', 'odontologo_nombre'
        ]
        read_only_fields = ['codigo', 'total', 'fecha_creacion', 'fecha_aprobacion']

    def get_paciente_nombre(self, obj):
        paciente = obj.plan_tratamiento.paciente
        if paciente and paciente.codusuario:
            return f"{paciente.codusuario.nombre} {paciente.codusuario.apellido}"
        return None
    
    def get_odontologo_nombre(self, obj):
        odontologo = obj.plan_tratamiento.odontologo
        if odontologo and odontologo.codusuario:
            return f"{odontologo.codusuario.nombre} {odontologo.codusuario.apellido}"
        return None


class PresupuestoCrearSerializer(serializers.ModelSerializer):
    """Serializer para crear presupuesto con items"""
    items = ItemPresupuestoCrearSerializer(many=True, write_only=True)

    class Meta:
        model = Presupuesto
        fields = [
            'id', 'plan_tratamiento', 'descuento', 'impuesto',
            'notas', 'fecha_vencimiento', 'items'
        ]
        read_only_fields = ['id']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        
        # Calcular subtotal desde los items
        subtotal = Decimal('0')
        for item_data in items_data:
            cantidad = item_data.get('cantidad', 1)
            precio = item_data.get('precio_unitario', Decimal('0'))
            descuento = item_data.get('descuento_item', Decimal('0'))
            subtotal += (precio * cantidad) - descuento
        
        # Crear presupuesto
        validated_data['subtotal'] = subtotal
        presupuesto = Presupuesto.objects.create(**validated_data)
        
        # Crear items
        for item_data in items_data:
            ItemPresupuesto.objects.create(presupuesto=presupuesto, **item_data)
        
        return presupuesto
    
    def to_representation(self, instance):
        """Incluir el id en la respuesta de creación."""
        representation = super().to_representation(instance)
        representation['id'] = instance.id
        return representation


class PlanTratamientoSerializer(serializers.ModelSerializer):
    """Serializer completo para planes de tratamiento"""
    # Arrays relacionados
    procedimientos = ProcedimientoSerializer(many=True, read_only=True)
    presupuestos = PresupuestoSerializer(many=True, read_only=True)
    
    # Campos computados básicos
    paciente_nombre = serializers.SerializerMethodField()
    odontologo_nombre = serializers.SerializerMethodField()
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    estado_plan = serializers.CharField(source='estado', read_only=True)  # Alias para el frontend
    costo_total = serializers.SerializerMethodField()
    progreso = serializers.SerializerMethodField()
    
    # Campos para la tabla del frontend
    cantidad_items = serializers.SerializerMethodField()
    items_activos = serializers.SerializerMethodField()
    
    # ✅ NUEVOS: Objetos completos para el frontend
    paciente_detalle = serializers.SerializerMethodField()
    odontologo_detalle = serializers.SerializerMethodField()
    
    # ✅ NUEVO: Alias de procedimientos para compatibilidad con frontend
    items = serializers.SerializerMethodField()
    
    # ✅ NUEVO: Estadísticas completas
    estadisticas = serializers.SerializerMethodField()
    
    # ✅ NUEVOS: Campos calculados para el frontend
    es_borrador = serializers.SerializerMethodField()
    puede_editarse = serializers.SerializerMethodField()
    es_aprobado = serializers.SerializerMethodField()
    items_completados = serializers.SerializerMethodField()
    subtotal_calculado = serializers.SerializerMethodField()
    descuento = serializers.DecimalField(max_digits=10, decimal_places=2, default=0, read_only=True)
    notas_plan = serializers.CharField(source='observaciones', read_only=True, allow_blank=True, allow_null=True)

    class Meta:
        model = PlanTratamiento
        fields = [
            'id', 'paciente', 'paciente_nombre', 'paciente_detalle',
            'odontologo', 'odontologo_nombre', 'odontologo_detalle',
            'codigo', 'descripcion', 'diagnostico', 'observaciones', 'notas_plan',
            'estado', 'estado_plan', 'estado_display',
            'fecha_creacion', 'fecha_aprobacion', 'fecha_inicio', 'fecha_finalizacion',
            'duracion_estimada_dias',
            'costo_total', 'subtotal_calculado', 'descuento',
            'progreso', 'cantidad_items', 'items_activos', 'items_completados',
            'procedimientos', 'items', 'presupuestos', 'estadisticas',
            'es_borrador', 'puede_editarse', 'es_aprobado'
        ]
        read_only_fields = ['codigo', 'fecha_creacion', 'fecha_aprobacion']

    def get_paciente_nombre(self, obj):
        if obj.paciente and obj.paciente.codusuario:
            return f"{obj.paciente.codusuario.nombre} {obj.paciente.codusuario.apellido}"
        return None

    def get_odontologo_nombre(self, obj):
        if obj.odontologo and obj.odontologo.codusuario:
            return f"{obj.odontologo.codusuario.nombre} {obj.odontologo.codusuario.apellido}"
        return None

    def get_costo_total(self, obj):
        return obj.calcular_costo_total()

    def get_progreso(self, obj):
        return obj.obtener_progreso()

    def get_cantidad_items(self, obj):
        """Total de procedimientos en el plan"""
        return obj.procedimientos.count()

    def get_items_activos(self, obj):
        """Procedimientos activos (no cancelados)"""
        return obj.procedimientos.exclude(estado='cancelado').count()
    
    # ✅ NUEVOS MÉTODOS AGREGADOS
    
    def get_paciente_detalle(self, obj):
        """Devuelve objeto completo del paciente para el frontend"""
        if obj.paciente and obj.paciente.codusuario:
            usuario = obj.paciente.codusuario
            return {
                'id': usuario.codigo,  # Usar codigo del Usuario, no del Paciente
                'nombre': usuario.nombre,
                'apellido': usuario.apellido,
                'email': usuario.correoelectronico  # Campo correcto: correoelectronico
            }
        return None
    
    def get_odontologo_detalle(self, obj):
        """Devuelve objeto completo del odontólogo para el frontend"""
        if obj.odontologo and obj.odontologo.codusuario:
            usuario = obj.odontologo.codusuario
            return {
                'id': usuario.codigo,  # Usar codigo del Usuario, no del Odontologo
                'nombre': f"{usuario.nombre} {usuario.apellido}",
                'especialidad': obj.odontologo.especialidad if obj.odontologo.especialidad else "Odontología General"
            }
        return None
    
    def get_items(self, obj):
        """
        Alias de procedimientos para compatibilidad con frontend.
        Devuelve los mismos datos que procedimientos pero con el nombre 'items'.
        """
        return ProcedimientoSerializer(obj.procedimientos.all(), many=True).data
    
    def get_estadisticas(self, obj):
        """Devuelve estadísticas calculadas del plan"""
        total_items = obj.procedimientos.count()
        items_activos = obj.procedimientos.filter(estado='en_proceso').count()
        items_completados = obj.procedimientos.filter(estado='completado').count()
        items_cancelados = obj.procedimientos.filter(estado='cancelado').count()
        items_pendientes = obj.procedimientos.filter(estado='pendiente').count()
        
        return {
            'total_items': total_items,
            'items_pendientes': items_pendientes,
            'items_activos': items_activos,
            'items_cancelados': items_cancelados,
            'items_completados': items_completados,
            'progreso_porcentaje': obj.obtener_progreso()
        }
    
    def get_es_borrador(self, obj):
        """Plan está en estado borrador"""
        return obj.estado == 'borrador'
    
    def get_puede_editarse(self, obj):
        """Plan puede editarse (solo si está en borrador)"""
        return obj.estado == 'borrador'
    
    def get_es_aprobado(self, obj):
        """Plan ha sido aprobado"""
        return obj.estado == 'aprobado'
    
    def get_items_completados(self, obj):
        """Total de procedimientos completados"""
        return obj.procedimientos.filter(estado='completado').count()
    
    def get_subtotal_calculado(self, obj):
        """Subtotal (mismo que costo_total por ahora)"""
        return obj.calcular_costo_total()


class PlanTratamientoCrearSerializer(serializers.ModelSerializer):
    """Serializer para crear planes de tratamiento"""
    class Meta:
        model = PlanTratamiento
        fields = [
            'id', 'codigo',  # ✅ Agregados para retornar después de crear
            'paciente', 'odontologo', 'descripcion', 'diagnostico',
            'observaciones', 'fecha_inicio', 'duracion_estimada_dias'
        ]
        read_only_fields = ['id', 'codigo']  # No se pueden modificar, solo leer

    def validate_paciente(self, value):
        if not value:
            raise serializers.ValidationError("El paciente es obligatorio")
        return value


class AprobarPresupuestoSerializer(serializers.Serializer):
    """Serializer para aprobar presupuesto"""
    aprobado_por = serializers.CharField(max_length=200, required=True)
    notas = serializers.CharField(required=False, allow_blank=True)


class RechazarPresupuestoSerializer(serializers.Serializer):
    """Serializer para rechazar presupuesto"""
    motivo_rechazo = serializers.CharField(required=True)


class HistorialPagoSerializer(serializers.ModelSerializer):
    """Serializer completo para historial de pagos"""
    # Relaciones
    plan_tratamiento_codigo = serializers.CharField(source='plan_tratamiento.codigo', read_only=True)
    plan_tratamiento_descripcion = serializers.CharField(source='plan_tratamiento.descripcion', read_only=True)
    presupuesto_codigo = serializers.CharField(source='presupuesto.codigo', read_only=True)
    
    # Display fields
    metodo_pago_display = serializers.CharField(source='get_metodo_pago_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    
    # Información del paciente
    paciente_nombre = serializers.SerializerMethodField()
    paciente_codigo = serializers.SerializerMethodField()
    
    class Meta:
        model = HistorialPago
        fields = [
            'id', 'plan_tratamiento', 'plan_tratamiento_codigo', 'plan_tratamiento_descripcion',
            'presupuesto', 'presupuesto_codigo',
            'codigo', 'monto', 'metodo_pago', 'metodo_pago_display',
            'estado', 'estado_display', 'fecha_pago',
            'numero_comprobante', 'numero_transaccion', 'notas', 'registrado_por',
            'paciente_nombre', 'paciente_codigo'
        ]
        read_only_fields = ['codigo', 'fecha_pago']
    
    def get_paciente_nombre(self, obj):
        """Obtiene el nombre del paciente desde el plan de tratamiento"""
        if obj.plan_tratamiento and obj.plan_tratamiento.paciente and obj.plan_tratamiento.paciente.codusuario:
            usuario = obj.plan_tratamiento.paciente.codusuario
            return f"{usuario.nombre} {usuario.apellido}"
        return None
    
    def get_paciente_codigo(self, obj):
        """Obtiene el código del paciente"""
        if obj.plan_tratamiento and obj.plan_tratamiento.paciente:
            return obj.plan_tratamiento.paciente.codigo
        return None


class HistorialPagoCrearSerializer(serializers.ModelSerializer):
    """Serializer para crear un nuevo pago"""
    class Meta:
        model = HistorialPago
        fields = [
            'plan_tratamiento', 'presupuesto', 'monto', 'metodo_pago',
            'numero_comprobante', 'numero_transaccion', 'notas'
        ]
    
    def validate(self, data):
        """Validaciones al crear un pago"""
        # Validar que el monto sea positivo
        if data.get('monto') and data['monto'] <= 0:
            raise serializers.ValidationError({
                'monto': 'El monto debe ser mayor a 0'
            })
        
        # Validar que el plan de tratamiento esté aprobado
        plan = data.get('plan_tratamiento')
        if plan and plan.estado not in ['aprobado', 'en_progreso', 'completado']:
            raise serializers.ValidationError({
                'plan_tratamiento': f'El plan de tratamiento debe estar aprobado. Estado actual: {plan.get_estado_display()}'
            })
        
        # Si se proporciona presupuesto, validar que esté aprobado
        presupuesto = data.get('presupuesto')
        if presupuesto and presupuesto.estado != 'aprobado':
            raise serializers.ValidationError({
                'presupuesto': f'El presupuesto debe estar aprobado. Estado actual: {presupuesto.get_estado_display()}'
            })
        
        # Validar que el presupuesto pertenezca al plan
        if presupuesto and plan and presupuesto.plan_tratamiento != plan:
            raise serializers.ValidationError({
                'presupuesto': 'El presupuesto no pertenece al plan de tratamiento seleccionado'
            })
        
        # Validar número de comprobante según método de pago
        metodo = data.get('metodo_pago')
        if metodo in ['tarjeta', 'transferencia', 'cheque'] and not data.get('numero_comprobante'):
            raise serializers.ValidationError({
                'numero_comprobante': f'El número de comprobante es requerido para el método {metodo}'
            })
        
        return data
    
    def create(self, validated_data):
        """Crear pago y generar código automático"""
        pago = HistorialPago(**validated_data)
        # El código se genera automáticamente en el método save()
        pago.save()
        return pago


# ================================
# SERIALIZERS PARA SESIONES
# ================================

class SesionTratamientoSerializer(serializers.ModelSerializer):
    """Serializer completo para sesiones de tratamiento"""
    odontologo_nombre = serializers.SerializerMethodField()
    plan_codigo = serializers.CharField(source='plan_tratamiento.codigo', read_only=True)
    plan_descripcion = serializers.CharField(source='plan_tratamiento.descripcion', read_only=True)
    paciente_nombre = serializers.SerializerMethodField()
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    duracion_formateada = serializers.SerializerMethodField()
    
    class Meta:
        model = SesionTratamiento
        fields = [
            'id', 'codigo', 'plan_tratamiento', 'plan_codigo', 'plan_descripcion',
            'odontologo', 'odontologo_nombre', 'paciente_nombre',
            'numero_sesion', 'titulo', 'descripcion', 'estado', 'estado_display',
            'fecha_programada', 'fecha_inicio', 'fecha_fin', 'duracion_minutos', 'duracion_formateada',
            'observaciones', 'recomendaciones', 'proxima_sesion_programada'
        ]
        read_only_fields = ['codigo', 'numero_sesion']
    
    def get_odontologo_nombre(self, obj):
        if obj.odontologo and obj.odontologo.codusuario:
            return f"{obj.odontologo.codusuario.nombre} {obj.odontologo.codusuario.apellido}"
        return None
    
    def get_paciente_nombre(self, obj):
        if obj.plan_tratamiento and obj.plan_tratamiento.paciente:
            paciente = obj.plan_tratamiento.paciente
            if paciente.codusuario:
                return f"{paciente.codusuario.nombre} {paciente.codusuario.apellido}"
        return None
    
    def get_duracion_formateada(self, obj):
        if obj.duracion_minutos:
            horas = obj.duracion_minutos // 60
            minutos = obj.duracion_minutos % 60
            if horas > 0:
                return f"{horas}h {minutos}min"
            return f"{minutos}min"
        return None


class SesionTratamientoCrearSerializer(serializers.ModelSerializer):
    """Serializer para crear sesiones de tratamiento"""
    class Meta:
        model = SesionTratamiento
        fields = [
            'plan_tratamiento', 'odontologo', 'titulo', 'descripcion',
            'fecha_programada', 'observaciones', 'recomendaciones',
            'proxima_sesion_programada'
        ]
    
    def validate_plan_tratamiento(self, value):
        """Validar que el plan existe y está activo"""
        if value.estado == 'cancelado':
            raise serializers.ValidationError('No se pueden crear sesiones para un plan cancelado')
        return value
    
    def validate_fecha_programada(self, value):
        """Validar que la fecha sea futura"""
        from django.utils import timezone
        if value < timezone.now():
            raise serializers.ValidationError('La fecha programada debe ser futura')
        return value
