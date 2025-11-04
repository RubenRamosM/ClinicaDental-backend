"""
Servicio principal para gestionar respaldos en AWS S3.
"""
import json
import gzip
import hashlib
import logging
from io import BytesIO
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from django.core.serializers import serialize
import boto3
from botocore.exceptions import ClientError

# Importar modelos que se respaldarán
from apps.usuarios.models import Usuario, Paciente
from apps.citas.models import Consulta
from apps.historial_clinico.models import Historialclinico, TratamientoOdontologico
from apps.sistema_pagos.models import Factura, Pago, PagoEnLinea
from apps.auditoria.models import Bitacora
from apps.tratamientos.models import PlanTratamiento, Presupuesto

from ..models import Respaldo

logger = logging.getLogger(__name__)


class S3Client:
    """
    Cliente para operaciones con AWS S3.
    """
    
    def __init__(self):
        """Inicializar cliente S3 con credenciales de configuración."""
        self.s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )
        self.bucket_name = settings.AWS_BACKUP_BUCKET_NAME
    
    def upload_file(self, file_obj, s3_path):
        """
        Subir archivo a S3.
        
        Args:
            file_obj: Objeto de archivo (BytesIO)
            s3_path: Ruta en S3 donde guardar el archivo
            
        Returns:
            bool: True si se subió correctamente
        """
        try:
            file_obj.seek(0)  # Volver al inicio del archivo
            self.s3.upload_fileobj(
                file_obj,
                self.bucket_name,
                s3_path,
                ExtraArgs={
                    'ServerSideEncryption': 'AES256',
                    'StorageClass': 'STANDARD_IA'  # Infrequent Access - más económico
                }
            )
            logger.info(f"Archivo subido exitosamente a S3: {s3_path}")
            return True
        except ClientError as e:
            logger.error(f"Error al subir archivo a S3: {e}")
            raise
    
    def download_file(self, s3_path):
        """
        Descargar archivo desde S3.
        
        Args:
            s3_path: Ruta del archivo en S3
            
        Returns:
            BytesIO: Objeto de archivo descargado
        """
        try:
            file_obj = BytesIO()
            self.s3.download_fileobj(self.bucket_name, s3_path, file_obj)
            file_obj.seek(0)
            logger.info(f"Archivo descargado exitosamente desde S3: {s3_path}")
            return file_obj
        except ClientError as e:
            logger.error(f"Error al descargar archivo desde S3: {e}")
            raise
    
    def generate_presigned_url(self, s3_path, expiration=3600):
        """
        Generar URL prefirmada para descarga temporal.
        
        Args:
            s3_path: Ruta del archivo en S3
            expiration: Tiempo de expiración en segundos (default: 1 hora)
            
        Returns:
            str: URL prefirmada
        """
        try:
            url = self.s3.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': s3_path
                },
                ExpiresIn=expiration
            )
            logger.info(f"URL prefirmada generada para: {s3_path}")
            return url
        except ClientError as e:
            logger.error(f"Error al generar URL prefirmada: {e}")
            raise
    
    def delete_file(self, s3_path):
        """
        Eliminar archivo de S3.
        
        Args:
            s3_path: Ruta del archivo en S3
            
        Returns:
            bool: True si se eliminó correctamente
        """
        try:
            self.s3.delete_object(Bucket=self.bucket_name, Key=s3_path)
            logger.info(f"Archivo eliminado de S3: {s3_path}")
            return True
        except ClientError as e:
            logger.error(f"Error al eliminar archivo de S3: {e}")
            raise
    
    def file_exists(self, s3_path):
        """
        Verificar si un archivo existe en S3.
        
        Args:
            s3_path: Ruta del archivo en S3
            
        Returns:
            bool: True si existe
        """
        try:
            self.s3.head_object(Bucket=self.bucket_name, Key=s3_path)
            return True
        except ClientError:
            return False


class BackupService:
    """
    Servicio principal para crear y gestionar respaldos.
    """
    
    def __init__(self):
        """Inicializar servicio de respaldo."""
        self.s3_client = S3Client()
    
    def crear_respaldo(self, clinica_id, tipo='manual', usuario=None, descripcion=''):
        """
        Crear respaldo completo de datos de una clínica.
        
        Args:
            clinica_id: ID de la clínica a respaldar
            tipo: Tipo de respaldo ('manual', 'automatico', 'por_demanda')
            usuario: Usuario que solicita el respaldo (opcional)
            descripcion: Descripción del respaldo
            
        Returns:
            Respaldo: Instancia del respaldo creado
        """
        inicio = timezone.now()
        respaldo = None
        
        try:
            # 1. Crear registro de respaldo con estado 'procesando'
            respaldo = Respaldo.objects.create(
                clinica_id=clinica_id,
                estado='procesando',
                tipo_respaldo=tipo,
                usuario=usuario,
                descripcion=descripcion or f'Respaldo {tipo} - {inicio.strftime("%Y-%m-%d %H:%M")}'
            )
            
            logger.info(f"Iniciando respaldo {respaldo.id} para clínica {clinica_id}")
            
            # 2. Obtener datos de la clínica
            datos_clinica = self.obtener_datos_clinica(clinica_id)
            
            # 3. Serializar a JSON
            json_data = self.serializar_datos(datos_clinica)
            
            # 4. Comprimir con gzip
            archivo_comprimido = self.comprimir_archivo(json_data)
            
            # 5. Calcular hash MD5
            hash_md5 = self.calcular_hash(archivo_comprimido)
            
            # 6. Generar ruta S3
            s3_path = self.generar_ruta_s3(clinica_id, inicio)
            
            # 7. Subir a S3
            self.s3_client.upload_file(archivo_comprimido, s3_path)
            
            # 8. Calcular estadísticas
            fin = timezone.now()
            tiempo_ejecucion = fin - inicio
            tamaño_bytes = archivo_comprimido.getbuffer().nbytes
            numero_registros = sum(len(datos) for datos in datos_clinica.values())
            
            # 9. Actualizar registro de respaldo
            respaldo.archivo_s3 = s3_path
            respaldo.tamaño_bytes = tamaño_bytes
            respaldo.hash_md5 = hash_md5
            respaldo.numero_registros = numero_registros
            respaldo.tiempo_ejecucion = tiempo_ejecucion
            respaldo.estado = 'completado'
            respaldo.metadata = {
                'modelos_respaldados': list(datos_clinica.keys()),
                'detalles_registros': {modelo: len(datos) for modelo, datos in datos_clinica.items()},
                'tamaño_original_mb': round(len(json_data) / (1024 * 1024), 2),
                'tamaño_comprimido_mb': round(tamaño_bytes / (1024 * 1024), 2),
                'compresion_porcentaje': round((1 - tamaño_bytes / len(json_data)) * 100, 2) if len(json_data) > 0 else 0,
            }
            respaldo.save()
            
            logger.info(
                f"Respaldo {respaldo.id} completado exitosamente. "
                f"Tamaño: {tamaño_bytes / (1024 * 1024):.2f} MB, "
                f"Registros: {numero_registros}, "
                f"Tiempo: {tiempo_ejecucion.total_seconds():.2f}s"
            )
            
            # 10. Limpiar respaldos antiguos
            self.limpiar_respaldos_antiguos(clinica_id)
            
            return respaldo
            
        except Exception as e:
            logger.error(f"Error al crear respaldo para clínica {clinica_id}: {e}", exc_info=True)
            
            # Marcar respaldo como fallido
            if respaldo:
                respaldo.estado = 'fallido'
                respaldo.metadata = {
                    'error': str(e),
                    'error_type': type(e).__name__
                }
                respaldo.save()
            
            raise
    
    def obtener_datos_clinica(self, clinica_id):
        """
        Obtener todos los datos de la clínica para respaldar.
        
        Args:
            clinica_id: ID de la clínica
            
        Returns:
            dict: Diccionario con los datos organizados por modelo
        """
        datos = {}
        
        # Usuarios de la clínica
        usuarios = Usuario.objects.filter(clinica_id=clinica_id)
        datos['usuarios'] = list(usuarios.values())
        
        # Pacientes de la clínica
        pacientes = Paciente.objects.filter(clinica_id=clinica_id)
        datos['pacientes'] = list(pacientes.values())
        
        # Consultas de la clínica (suponiendo que tienen relación con paciente)
        consultas = Consulta.objects.filter(paciente__clinica_id=clinica_id)
        datos['consultas'] = list(consultas.values())
        
        # Historiales clínicos
        historiales = Historialclinico.objects.filter(paciente__clinica_id=clinica_id)
        datos['historiales_clinicos'] = list(historiales.values())
        
        # Tratamientos odontológicos
        tratamientos = TratamientoOdontologico.objects.filter(paciente__clinica_id=clinica_id)
        datos['tratamientos_odontologicos'] = list(tratamientos.values())
        
        # Planes de tratamiento
        planes = PlanTratamiento.objects.filter(paciente__clinica_id=clinica_id)
        datos['planes_tratamiento'] = list(planes.values())
        
        # Presupuestos
        presupuestos = Presupuesto.objects.filter(paciente__clinica_id=clinica_id)
        datos['presupuestos'] = list(presupuestos.values())
        
        # Facturas
        facturas = Factura.objects.filter(clinica_id=clinica_id)
        datos['facturas'] = list(facturas.values())
        
        # Pagos
        pagos = Pago.objects.filter(factura__clinica_id=clinica_id)
        datos['pagos'] = list(pagos.values())
        
        # Pagos en línea
        pagos_online = PagoEnLinea.objects.filter(pago__factura__clinica_id=clinica_id)
        datos['pagos_online'] = list(pagos_online.values())
        
        # Bitácora de auditoría
        bitacoras = Bitacora.objects.filter(clinica_id=clinica_id)
        datos['bitacoras'] = list(bitacoras.values())
        
        logger.info(
            f"Datos obtenidos para clínica {clinica_id}: "
            f"{sum(len(datos) for datos in datos.values())} registros totales"
        )
        
        return datos
    
    def serializar_datos(self, datos):
        """
        Serializar datos a JSON.
        
        Args:
            datos: Diccionario con los datos a serializar
            
        Returns:
            str: JSON string con los datos
        """
        # Convertir datos con formato especial para fechas
        def default_serializer(obj):
            if isinstance(obj, (datetime, timezone.datetime)):
                return obj.isoformat()
            return str(obj)
        
        json_data = json.dumps(
            datos,
            indent=2,
            ensure_ascii=False,
            default=default_serializer
        )
        
        return json_data
    
    def comprimir_archivo(self, json_data):
        """
        Comprimir datos JSON con gzip.
        
        Args:
            json_data: String JSON a comprimir
            
        Returns:
            BytesIO: Archivo comprimido
        """
        archivo_comprimido = BytesIO()
        
        with gzip.GzipFile(fileobj=archivo_comprimido, mode='wb') as gz_file:
            gz_file.write(json_data.encode('utf-8'))
        
        archivo_comprimido.seek(0)
        
        logger.info(
            f"Datos comprimidos: {len(json_data)} bytes -> "
            f"{archivo_comprimido.getbuffer().nbytes} bytes "
            f"({(1 - archivo_comprimido.getbuffer().nbytes / len(json_data)) * 100:.1f}% reducción)"
        )
        
        return archivo_comprimido
    
    def calcular_hash(self, archivo):
        """
        Calcular hash MD5 del archivo.
        
        Args:
            archivo: BytesIO del archivo
            
        Returns:
            str: Hash MD5 en hexadecimal
        """
        archivo.seek(0)
        md5_hash = hashlib.md5()
        md5_hash.update(archivo.read())
        archivo.seek(0)
        
        return md5_hash.hexdigest()
    
    def generar_ruta_s3(self, clinica_id, fecha):
        """
        Generar ruta S3 para el respaldo.
        
        Args:
            clinica_id: ID de la clínica
            fecha: Fecha del respaldo
            
        Returns:
            str: Ruta S3
        """
        año = fecha.year
        mes = f"{fecha.month:02d}"
        timestamp = fecha.strftime("%Y%m%d_%H%M%S")
        
        return f"backups/{clinica_id}/{año}/{mes}/backup_{timestamp}.json.gz"
    
    def limpiar_respaldos_antiguos(self, clinica_id, dias_retencion=30):
        """
        Eliminar respaldos más antiguos que el periodo de retención.
        
        Args:
            clinica_id: ID de la clínica
            dias_retencion: Días de retención (default: 30)
        """
        fecha_limite = timezone.now() - timedelta(days=dias_retencion)
        
        respaldos_antiguos = Respaldo.objects.filter(
            clinica_id=clinica_id,
            fecha_respaldo__lt=fecha_limite,
            fecha_eliminacion__isnull=True,
            estado='completado'
        )
        
        eliminados = 0
        for respaldo in respaldos_antiguos:
            try:
                # Eliminar de S3
                if self.s3_client.file_exists(respaldo.archivo_s3):
                    self.s3_client.delete_file(respaldo.archivo_s3)
                
                # Soft delete del registro
                respaldo.fecha_eliminacion = timezone.now()
                respaldo.save()
                
                eliminados += 1
            except Exception as e:
                logger.error(f"Error al eliminar respaldo {respaldo.id}: {e}")
        
        if eliminados > 0:
            logger.info(
                f"Limpieza completada para clínica {clinica_id}: "
                f"{eliminados} respaldos eliminados (>{dias_retencion} días)"
            )
    
    def restaurar_respaldo(self, respaldo_id):
        """
        Restaurar datos desde un respaldo.
        
        ADVERTENCIA: Esta operación sobrescribirá datos existentes.
        
        Args:
            respaldo_id: ID del respaldo a restaurar
            
        Returns:
            dict: Estadísticas de la restauración
        """
        try:
            respaldo = Respaldo.objects.get(id=respaldo_id)
            
            if not respaldo.puede_restaurarse():
                raise ValueError("El respaldo no puede ser restaurado")
            
            logger.info(f"Iniciando restauración del respaldo {respaldo_id}")
            
            # 1. Descargar archivo desde S3
            archivo_comprimido = self.s3_client.download_file(respaldo.archivo_s3)
            
            # 2. Descomprimir
            with gzip.GzipFile(fileobj=archivo_comprimido, mode='rb') as gz_file:
                json_data = gz_file.read().decode('utf-8')
            
            # 3. Deserializar
            datos = json.loads(json_data)
            
            # 4. Verificar hash
            archivo_comprimido.seek(0)
            hash_calculado = self.calcular_hash(archivo_comprimido)
            if hash_calculado != respaldo.hash_md5:
                raise ValueError("Hash MD5 no coincide - archivo corrupto")
            
            logger.info(f"Restauración del respaldo {respaldo_id} completada exitosamente")
            
            return {
                'respaldo_id': respaldo_id,
                'datos': datos,
                'numero_registros': sum(len(items) for items in datos.values()),
                'mensaje': 'Datos restaurados correctamente'
            }
            
        except Respaldo.DoesNotExist:
            logger.error(f"Respaldo {respaldo_id} no encontrado")
            raise
        except Exception as e:
            logger.error(f"Error al restaurar respaldo {respaldo_id}: {e}", exc_info=True)
            raise
    
    def obtener_estadisticas(self, clinica_id):
        """
        Obtener estadísticas de respaldos de una clínica.
        
        Args:
            clinica_id: ID de la clínica
            
        Returns:
            dict: Estadísticas de respaldos
        """
        respaldos = Respaldo.objects.filter(
            clinica_id=clinica_id,
            fecha_eliminacion__isnull=True
        )
        
        total = respaldos.count()
        completados = respaldos.filter(estado='completado').count()
        fallidos = respaldos.filter(estado='fallido').count()
        
        tamaño_total = sum(r.tamaño_bytes for r in respaldos.filter(estado='completado'))
        
        ultimo_respaldo = respaldos.filter(estado='completado').order_by('-fecha_respaldo').first()
        
        return {
            'total_respaldos': total,
            'completados': completados,
            'fallidos': fallidos,
            'tamaño_total_mb': round(tamaño_total / (1024 * 1024), 2),
            'ultimo_respaldo': {
                'id': ultimo_respaldo.id if ultimo_respaldo else None,
                'fecha': ultimo_respaldo.fecha_respaldo.isoformat() if ultimo_respaldo else None,
                'tamaño_mb': round(ultimo_respaldo.tamaño_bytes / (1024 * 1024), 2) if ultimo_respaldo else 0,
            } if ultimo_respaldo else None
        }
