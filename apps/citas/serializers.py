"""
Serializers para la app de citas.
"""
from rest_framework import serializers
from .models import Horario, Estadodeconsulta, Tipodeconsulta, Consulta


class HorarioSerializer(serializers.ModelSerializer):
    """Serializer para horarios."""
    hora_formateada = serializers.SerializerMethodField()
    hora_texto = serializers.SerializerMethodField()  # ✅ Alias para compatibilidad
    
    class Meta:
        model = Horario
        fields = ['id', 'hora', 'hora_formateada', 'hora_texto']
        read_only_fields = ['id']
    
    def get_hora_formateada(self, obj):
        """Formato 12 horas con AM/PM."""
        if obj.hora:
            return obj.hora.strftime('%I:%M %p')
        return None
    
    def get_hora_texto(self, obj):
        """Formato 24 horas HH:MM."""
        if obj.hora:
            return obj.hora.strftime('%H:%M')
        return None


class EstadodeconsultaSerializer(serializers.ModelSerializer):
    """Serializer para estados de consulta."""
    
    class Meta:
        model = Estadodeconsulta
        fields = ['id', 'estado']
        read_only_fields = ['id']


class TipodeconsultaSerializer(serializers.ModelSerializer):
    """Serializer para tipos de consulta."""
    nombre = serializers.CharField(source='nombreconsulta', read_only=True)
    
    class Meta:
        model = Tipodeconsulta
        fields = [
            'id', 'nombreconsulta', 'nombre', 'permite_agendamiento_web',
            'requiere_aprobacion', 'es_urgencia', 'duracion_estimada'
        ]
        read_only_fields = ['id', 'nombre']


class ConsultaSerializer(serializers.ModelSerializer):
    """Serializer básico para consultas."""
    paciente_nombre = serializers.CharField(
        source='codpaciente.codusuario.nombre', read_only=True
    )
    paciente_apellido = serializers.CharField(
        source='codpaciente.codusuario.apellido', read_only=True
    )
    odontologo_nombre = serializers.SerializerMethodField()
    tipo_consulta_nombre = serializers.CharField(
        source='idtipoconsulta.nombreconsulta', read_only=True
    )
    estado_consulta_nombre = serializers.CharField(
        source='idestadoconsulta.estado', read_only=True
    )
    # ✅ NUEVO: Campo hora para que el frontend pueda parsear fechas correctamente
    hora = serializers.SerializerMethodField()
    
    class Meta:
        model = Consulta
        fields = [
            'id', 'fecha', 'hora',  # ✅ 'hora' agregado después de 'fecha'
            'codpaciente', 'paciente_nombre', 'paciente_apellido',
            'cododontologo', 'odontologo_nombre', 'codrecepcionista',
            'idhorario', 'idtipoconsulta', 'tipo_consulta_nombre',
            'idestadoconsulta', 'estado_consulta_nombre', 'estado',
            'fecha_preferida', 'horario_preferido', 'motivo_consulta',
            'diagnostico', 'tratamiento', 'costo_consulta', 'requiere_pago'
        ]
        read_only_fields = ['id']
    
    def get_odontologo_nombre(self, obj):
        if obj.cododontologo:
            return f"Dr(a). {obj.cododontologo.codusuario.nombre} {obj.cododontologo.codusuario.apellido}"
        return None
    
    def get_hora(self, obj):
        """Obtener hora desde el horario relacionado."""
        if obj.idhorario and obj.idhorario.hora:
            return obj.idhorario.hora.strftime('%H:%M')
        return None


class ConsultaDetalleSerializer(ConsultaSerializer):
    """Serializer detallado para consultas."""
    paciente = serializers.SerializerMethodField()
    odontologo = serializers.SerializerMethodField()
    recepcionista = serializers.SerializerMethodField()
    horario = HorarioSerializer(source='idhorario', read_only=True)
    tipo_consulta = TipodeconsultaSerializer(source='idtipoconsulta', read_only=True)
    estado_consulta = EstadodeconsultaSerializer(source='idestadoconsulta', read_only=True)
    
    class Meta(ConsultaSerializer.Meta):
        fields = ConsultaSerializer.Meta.fields + [
            'paciente', 'odontologo', 'recepcionista', 'horario',
            'tipo_consulta', 'estado_consulta', 'hora_llegada',
            'hora_inicio_consulta', 'hora_fin_consulta', 'tipo_consulta',
            'notas_recepcion', 'motivo_cancelacion', 'observaciones'
        ]
    
    def get_paciente(self, obj):
        return {
            'codigo': obj.codpaciente.codusuario.codigo,
            'nombre': obj.codpaciente.codusuario.nombre,
            'apellido': obj.codpaciente.codusuario.apellido,
            'correo': obj.codpaciente.codusuario.correoelectronico,
            'telefono': obj.codpaciente.codusuario.telefono,
            'carnet': obj.codpaciente.carnetidentidad
        }
    
    def get_odontologo(self, obj):
        if obj.cododontologo:
            return {
                'codigo': obj.cododontologo.codusuario.codigo,
                'nombre': obj.cododontologo.codusuario.nombre,
                'apellido': obj.cododontologo.codusuario.apellido,
                'especialidad': obj.cododontologo.especialidad,
                'matricula': obj.cododontologo.nromatricula
            }
        return None
    
    def get_recepcionista(self, obj):
        if obj.codrecepcionista:
            return {
                'codigo': obj.codrecepcionista.codusuario.codigo,
                'nombre': obj.codrecepcionista.codusuario.nombre,
                'apellido': obj.codrecepcionista.codusuario.apellido
            }
        return None


class ConsultaCrearSerializer(serializers.ModelSerializer):
    """Serializer para crear consultas - acepta formato admin y paciente."""
    
    # Campos opcionales para agendamiento web (pacientes)
    fecha_preferida = serializers.DateField(required=False, allow_null=True)
    horario_preferido = serializers.ChoiceField(
        choices=[
            ('manana', 'Mañana (8am-12pm)'),
            ('tarde', 'Tarde (2pm-6pm)'),
            ('noche', 'Noche (6pm-8pm)'),
            ('cualquiera', 'Cualquier horario')
        ],
        required=False
    )
    
    class Meta:
        model = Consulta
        fields = [
            'id', 'codpaciente', 'cododontologo', 'fecha', 'idhorario',
            'idtipoconsulta', 'idestadoconsulta', 'motivo_consulta',
            'fecha_preferida', 'horario_preferido'
        ]
        read_only_fields = ['id']
        extra_kwargs = {
            'cododontologo': {'required': False},
            'fecha': {'required': False},
            'idhorario': {'required': False},
            'idestadoconsulta': {'required': False, 'allow_null': True},  # ✅ Permitir null
        }
    
    def validate_idestadoconsulta(self, value):
        """
        ✅ Validación personalizada: Ignorar cualquier valor enviado desde el frontend.
        El backend siempre establecerá el estado correcto en create().
        """
        # Simplemente retornar None, será ignorado en create()
        return None
    
    def validate(self, attrs):
        """Validar que se proporcionen campos suficientes."""
        # Si es agendamiento admin (tiene fecha directa)
        if 'fecha' in attrs:
            if not attrs.get('idhorario'):
                raise serializers.ValidationError({
                    'idhorario': 'Este campo es requerido cuando se especifica fecha.'
                })
        # Si es agendamiento paciente (tiene fecha_preferida)
        elif 'fecha_preferida' in attrs:
            pass  # fecha_preferida es suficiente para pacientes
        else:
            raise serializers.ValidationError({
                'fecha': 'Debe especificar fecha o fecha_preferida.'
            })
        
        return attrs
    
    def create(self, validated_data):
        # Remover campos de preferencia si existen
        fecha_preferida = validated_data.pop('fecha_preferida', None)
        horario_preferido = validated_data.pop('horario_preferido', None)
        
        # Remover idestadoconsulta si viene del frontend (no confiar)
        validated_data.pop('idestadoconsulta', None)
        
        # Establecer valores por defecto
        if 'estado' not in validated_data:
            validated_data['estado'] = 'pendiente'
        
        # SIEMPRE establecer estado de consulta correcto (ID fijo 1 = Pendiente)
        try:
            estado_pendiente = Estadodeconsulta.objects.get(id=1)  # ID fijo del seed
        except Estadodeconsulta.DoesNotExist:
            # Fallback: buscar por nombre
            estado_pendiente = Estadodeconsulta.objects.get(estado='Pendiente')
        validated_data['idestadoconsulta'] = estado_pendiente
        
        # Si es agendamiento paciente (sin fecha directa)
        if 'fecha' not in validated_data and fecha_preferida:
            validated_data['fecha'] = fecha_preferida
            validated_data['horario_preferido'] = horario_preferido or 'cualquiera'
            
            # Asignar primer horario disponible temporalmente
            if 'idhorario' not in validated_data:
                horario = Horario.objects.first()
                validated_data['idhorario'] = horario
        
        return super().create(validated_data)


class ConsultaActualizarEstadoSerializer(serializers.ModelSerializer):
    """Serializer para actualizar estado de consulta."""
    
    class Meta:
        model = Consulta
        fields = ['estado', 'idestadoconsulta', 'motivo_cancelacion']
    
    def validate(self, data):
        if data.get('estado') == 'cancelada' and not data.get('motivo_cancelacion'):
            raise serializers.ValidationError({
                'motivo_cancelacion': 'Debe proporcionar un motivo para cancelar.'
            })
        return data


class ConsultaDiagnosticoSerializer(serializers.ModelSerializer):
    """Serializer para agregar diagnóstico y tratamiento."""
    
    class Meta:
        model = Consulta
        fields = [
            'diagnostico', 'tratamiento', 'costo_consulta',
            'requiere_pago', 'observaciones'
        ]
