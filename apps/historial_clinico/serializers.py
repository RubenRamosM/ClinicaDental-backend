"""
Serializers para historial clínico.
"""
from rest_framework import serializers
from . import models
from .models import Historialclinico, DocumentoClinico


class HistorialclinicoSerializer(serializers.ModelSerializer):
    """Serializer completo para Historia Clínica Electrónica (HCE)."""
    paciente_nombre = serializers.SerializerMethodField()
    
    class Meta:
        model = Historialclinico
        fields = [
            'id', 
            'pacientecodigo',
            'paciente_nombre',
            'episodio',
            'fecha',
            'updated_at',
            'motivoconsulta',
            'diagnostico',
            'tratamiento',
            'alergias',
            'enfermedades',
            'antecedentesfamiliares',
            'antecedentespersonales',
            'examengeneral',
            'examenregional',
            'examenbucal',
            'receta',
            'descripcion'  # Campo legacy
        ]
        read_only_fields = ['fecha', 'updated_at', 'episodio']
    
    def get_paciente_nombre(self, obj):
        if obj.pacientecodigo and obj.pacientecodigo.codusuario:
            return f"{obj.pacientecodigo.codusuario.nombre} {obj.pacientecodigo.codusuario.apellido}"
        return None


class HistorialclinicoCrearSerializer(serializers.ModelSerializer):
    """Serializer para crear Historia Clínica con validaciones."""
    
    class Meta:
        model = Historialclinico
        fields = [
            'pacientecodigo',
            'motivoconsulta',
            'diagnostico',
            'tratamiento',
            'alergias',
            'enfermedades',
            'antecedentesfamiliares',
            'antecedentespersonales',
            'examengeneral',
            'examenregional',
            'examenbucal',
            'receta',
            'descripcion'  # Campo legacy (opcional)
        ]
    
    def validate(self, data):
        """Validar que al menos haya motivo o diagnóstico."""
        motivoconsulta = data.get('motivoconsulta', '').strip()
        diagnostico = data.get('diagnostico', '').strip()
        
        if not motivoconsulta and not diagnostico:
            raise serializers.ValidationError({
                'motivoconsulta': 'Debe proporcionar al menos un motivo de consulta o diagnóstico.',
                'diagnostico': 'Debe proporcionar al menos un motivo de consulta o diagnóstico.'
            })
        
        # Validar longitud mínima si están presentes
        if motivoconsulta and len(motivoconsulta) < 10:
            raise serializers.ValidationError({
                'motivoconsulta': 'El motivo de consulta debe tener al menos 10 caracteres.'
            })
        
        if diagnostico and len(diagnostico) < 10:
            raise serializers.ValidationError({
                'diagnostico': 'El diagnóstico debe tener al menos 10 caracteres.'
            })
        
        return data


class DocumentoClinicoSerializer(serializers.ModelSerializer):
    """Serializer para documentos clínicos."""
    paciente_nombre = serializers.SerializerMethodField()
    historial_fecha = serializers.DateTimeField(
        source='historial.fecha',
        read_only=True
    )
    
    class Meta:
        model = DocumentoClinico
        fields = [
            'id', 
            'historial',
            'paciente_nombre',
            'historial_fecha',
            'titulo',
            'tipo_documento',
            'archivo_url',
            'descripcion',
            'fecha_subida'
        ]
        read_only_fields = ['fecha_subida']
    
    def get_paciente_nombre(self, obj):
        if obj.historial and obj.historial.pacientecodigo and obj.historial.pacientecodigo.codusuario:
            usuario = obj.historial.pacientecodigo.codusuario
            return f"{usuario.nombre} {usuario.apellido}"
        return None


class DocumentoClinicoCrearSerializer(serializers.ModelSerializer):
    """Serializer para subir documentos clínicos."""
    archivo = serializers.FileField(write_only=True, required=True)
    
    class Meta:
        model = DocumentoClinico
        fields = [
            'historial',
            'titulo',
            'tipo_documento',
            'descripcion',
            'archivo'
        ]
    
    def validate_archivo(self, value):
        """Validar tipo y tamaño del archivo."""
        # Validar tamaño máximo (10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if value.size > max_size:
            raise serializers.ValidationError(
                "El archivo no debe superar los 10MB."
            )
        
        # Validar extensión
        extensiones_validas = [
            '.pdf', '.jpg', '.jpeg', '.png', '.gif',
            '.doc', '.docx', '.xls', '.xlsx'
        ]
        extension = value.name.lower()
        if not any(extension.endswith(ext) for ext in extensiones_validas):
            raise serializers.ValidationError(
                f"Extensión no válida. Permitidas: {', '.join(extensiones_validas)}"
            )
        
        return value
    
    def create(self, validated_data):
        """Crear documento y subir archivo a S3."""
        archivo = validated_data.pop('archivo')
        
        # TODO: Implementar subida a S3
        # from apps.api.supabase_client import supabase_client
        # archivo_url = supabase_client.upload_file(archivo)
        
        # Por ahora, solo guardar la URL simulada
        validated_data['archivo_url'] = f"https://s3.amazonaws.com/dental-clinic-files/{archivo.name}"
        
        documento = DocumentoClinico.objects.create(**validated_data)
        return documento


# =============== ODONTOGRAMA DIGITAL ===============

class OdontogramaSerializer(serializers.ModelSerializer):
    """Serializer para odontograma."""
    paciente_nombre = serializers.SerializerMethodField()
    odontologo_nombre = serializers.SerializerMethodField()
    estadisticas = serializers.SerializerMethodField()
    
    class Meta:
        model = models.Odontograma
        fields = [
            'id', 'paciente', 'paciente_nombre', 'odontologo', 'odontologo_nombre',
            'dientes', 'observaciones_generales', 'estadisticas',
            'fecha_creacion', 'fecha_actualizacion'
        ]
        read_only_fields = ['fecha_creacion', 'fecha_actualizacion']
    
    def get_paciente_nombre(self, obj):
        if obj.paciente and obj.paciente.codusuario:
            return f"{obj.paciente.codusuario.nombre} {obj.paciente.codusuario.apellido}"
        return None
    
    def get_odontologo_nombre(self, obj):
        if obj.odontologo and obj.odontologo.codusuario:
            return f"Dr. {obj.odontologo.codusuario.nombre} {obj.odontologo.codusuario.apellido}"
        return None
    
    def get_estadisticas(self, obj):
        return obj.obtener_estadisticas()


class OdontogramaCrearSerializer(serializers.ModelSerializer):
    """Serializer para crear odontograma."""
    
    class Meta:
        model = models.Odontograma
        fields = ['id', 'paciente', 'odontologo', 'observaciones_generales']
        read_only_fields = ['id']
    
    def create(self, validated_data):
        """Crear odontograma e inicializar dientes."""
        odontograma = models.Odontograma.objects.create(**validated_data)
        odontograma.inicializar_dientes()
        odontograma.save()
        return odontograma


class ActualizarDienteSerializer(serializers.Serializer):
    """Serializer para actualizar estado de un diente."""
    numero_diente = serializers.IntegerField(min_value=1, max_value=32)
    estado = serializers.ChoiceField(choices=models.Odontograma.ESTADO_DIENTE_CHOICES)
    caras_afectadas = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True
    )
    observaciones = serializers.CharField(required=False, allow_blank=True)


class TratamientoOdontologicoSerializer(serializers.ModelSerializer):
    """Serializer para tratamientos odontológicos."""
    odontograma_paciente = serializers.CharField(
        source='odontograma.paciente',
        read_only=True
    )
    
    class Meta:
        model = models.TratamientoOdontologico
        fields = [
            'id', 'odontograma', 'odontograma_paciente', 'numero_diente',
            'tipo_tratamiento', 'descripcion', 'fecha_tratamiento', 'costo'
        ]


class ConsentimientoInformadoSerializer(serializers.ModelSerializer):
    """Serializer completo para consentimiento informado."""
    paciente_nombre = serializers.SerializerMethodField()
    odontologo_nombre = serializers.SerializerMethodField()
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    vigente = serializers.SerializerMethodField()
    
    class Meta:
        model = models.ConsentimientoInformado
        fields = [
            'id', 'paciente', 'paciente_nombre', 'consulta', 'odontologo', 'odontologo_nombre',
            'tipo_tratamiento', 'contenido_documento', 'riesgos', 'beneficios', 'alternativas',
            'firma_paciente_url', 'firma_tutor_url', 'nombre_tutor', 'documento_tutor',
            'estado', 'estado_display', 'fecha_creacion', 'fecha_firma',
            'fecha_vencimiento', 'ip_firma', 'notas', 'vigente'
        ]
        read_only_fields = ['fecha_creacion', 'fecha_firma', 'ip_firma']
    
    def get_paciente_nombre(self, obj):
        if obj.paciente and obj.paciente.codusuario:
            return f"{obj.paciente.codusuario.nombre} {obj.paciente.codusuario.apellido}"
        return None
    
    def get_odontologo_nombre(self, obj):
        if obj.odontologo and obj.odontologo.codusuario:
            return f"{obj.odontologo.codusuario.nombre} {obj.odontologo.codusuario.apellido}"
        return None
    
    def get_vigente(self, obj):
        return obj.esta_vigente()


class ConsentimientoCrearSerializer(serializers.ModelSerializer):
    """Serializer para crear consentimientos informados."""
    class Meta:
        model = models.ConsentimientoInformado
        fields = [
            'id', 'paciente', 'consulta', 'odontologo', 'tipo_tratamiento',
            'contenido_documento', 'riesgos', 'beneficios', 'alternativas',
            'fecha_vencimiento', 'notas'
        ]
        read_only_fields = ['id']


class FirmarConsentimientoSerializer(serializers.Serializer):
    """Serializer para firmar un consentimiento informado."""
    # ✅ CORREGIDO: Usar TextField para base64 largo (sin límite de longitud)
    firma_paciente_url = serializers.CharField(
        required=True,
        allow_blank=False,
        trim_whitespace=False,  # No recortar espacios en base64
        help_text="URL de la imagen de la firma del paciente (base64 data URI permitido)"
    )
    # ✅ CORREGIDO: Usar TextField para base64 largo para firma tutor
    firma_tutor_url = serializers.CharField(
        required=False,
        allow_blank=True,
        trim_whitespace=False,  # No recortar espacios en base64
        help_text="URL de la firma del tutor (solo si aplica)"
    )
    nombre_tutor = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=200
    )
    documento_tutor = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=50
    )
    ip_firma = serializers.IPAddressField(required=False)
    
    def validate_firma_paciente_url(self, value):
        """Validar formato de firma (permitir data URI base64 o URL)."""
        if not value:
            raise serializers.ValidationError("La firma del paciente es obligatoria")
        
        # Validar que sea base64 data URI o URL válida
        if not (value.startswith('data:image/') or value.startswith('http://') or value.startswith('https://')):
            raise serializers.ValidationError(
                "La firma debe ser un data URI base64 (data:image/...) o una URL válida"
            )
        
        return value
    
    def validate_firma_tutor_url(self, value):
        """Validar formato de firma del tutor (opcional)."""
        if not value:
            return value
        
        # Validar que sea base64 data URI o URL válida
        if not (value.startswith('data:image/') or value.startswith('http://') or value.startswith('https://')):
            raise serializers.ValidationError(
                "La firma debe ser un data URI base64 (data:image/...) o una URL válida"
            )
        
        return value

