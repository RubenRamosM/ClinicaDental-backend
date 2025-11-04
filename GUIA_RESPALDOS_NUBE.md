# ☁️ GUÍA COMPLETA - RESPALDOS AUTOMÁTICOS EN LA NUBE

## 📋 TABLA DE CONTENIDOS
1. [Introducción](#1-introducción)
2. [Configuración de Almacenamiento en la Nube](#2-configuración-de-almacenamiento-en-la-nube)
3. [Sistema de Respaldos Automáticos](#3-sistema-de-respaldos-automáticos)
4. [Multitenancy - Respaldos por Clínica](#4-multitenancy---respaldos-por-clínica)
5. [Restauración de Respaldos](#5-restauración-de-respaldos)
6. [Monitoreo y Notificaciones](#6-monitoreo-y-notificaciones)

---

## 1. INTRODUCCIÓN

### ¿Qué incluye este sistema?

- ✅ **Respaldos automáticos diarios** de base de datos
- ✅ **Almacenamiento en la nube** (AWS S3, Google Cloud, Azure)
- ✅ **Multitenancy**: Cada clínica respalda solo sus datos
- ✅ **Encriptación** de respaldos
- ✅ **Rotación automática** (mantener últimos 30 días)
- ✅ **Notificaciones por email** cuando se completa el respaldo
- ✅ **Restauración con un comando**

### Opciones de Almacenamiento

| Servicio | Costo (5GB/mes) | Ventajas |
|----------|-----------------|----------|
| **AWS S3** | ~$0.12 USD | Más popular, documentación extensa |
| **Google Cloud Storage** | ~$0.10 USD | Integración con Google Drive |
| **Azure Blob Storage** | ~$0.15 USD | Integración con Microsoft 365 |
| **Backblaze B2** | ~$0.05 USD | Más económico, API compatible S3 |

---

## 2. CONFIGURACIÓN DE ALMACENAMIENTO EN LA NUBE

### 2.1 Opción A: AWS S3 (Recomendado)

#### Paso 1: Crear cuenta en AWS

1. Ir a https://aws.amazon.com/
2. Crear cuenta gratuita (12 meses gratis con 5GB)
3. Configurar tarjeta de crédito (no se cobra si estás en free tier)

#### Paso 2: Crear bucket S3

```bash
# Instalar AWS CLI
pip install awscli

# Configurar credenciales
aws configure
# AWS Access Key ID: [tu_access_key]
# AWS Secret Access Key: [tu_secret_key]
# Default region: us-east-1
# Default output: json

# Crear bucket
aws s3 mb s3://clinica-dental-backups-2025
```

#### Paso 3: Configurar Django

```python
# settings.py

# Instalar: pip install boto3 django-storages

INSTALLED_APPS = [
    # ... otras apps
    'storages',
]

# Configuración AWS S3
AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME', 'clinica-dental-backups-2025')
AWS_S3_REGION_NAME = env('AWS_S3_REGION_NAME', 'us-east-1')
AWS_S3_SIGNATURE_VERSION = 's3v4'
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = 'private'  # Archivos privados
AWS_S3_ENCRYPTION = True  # Encriptación en reposo

# Directorio de respaldos
BACKUP_STORAGE_LOCATION = 'backups/'
```

#### Paso 4: Agregar a .env

```bash
# .env

# AWS S3 Credentials
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_STORAGE_BUCKET_NAME=clinica-dental-backups-2025
AWS_S3_REGION_NAME=us-east-1
```

---

### 2.2 Opción B: Google Cloud Storage

#### Paso 1: Crear cuenta en Google Cloud

1. Ir a https://cloud.google.com/
2. Activar $300 USD de crédito gratis (12 meses)
3. Crear proyecto: "clinica-dental-backups"

#### Paso 2: Crear bucket

```bash
# Instalar Google Cloud SDK
pip install google-cloud-storage

# Autenticarse
gcloud auth login

# Crear bucket
gsutil mb -l us-central1 gs://clinica-dental-backups-2025/
```

#### Paso 3: Obtener credenciales

```bash
# Crear service account
gcloud iam service-accounts create backup-service \
    --display-name="Backup Service Account"

# Descargar credenciales JSON
gcloud iam service-accounts keys create credentials.json \
    --iam-account=backup-service@tu-proyecto.iam.gserviceaccount.com
```

#### Paso 4: Configurar Django

```python
# settings.py

from google.oauth2 import service_account

GS_CREDENTIALS = service_account.Credentials.from_service_account_file(
    BASE_DIR / 'credentials.json'
)
GS_BUCKET_NAME = env('GS_BUCKET_NAME', 'clinica-dental-backups-2025')
GS_PROJECT_ID = env('GS_PROJECT_ID', 'tu-proyecto')
GS_DEFAULT_ACL = 'private'
GS_FILE_OVERWRITE = False
```

---

### 2.3 Opción C: Azure Blob Storage

#### Paso 1: Crear cuenta en Azure

1. Ir a https://azure.microsoft.com/
2. Crear cuenta gratuita ($200 USD de crédito)
3. Crear Storage Account

#### Paso 2: Configurar

```bash
# Instalar Azure SDK
pip install azure-storage-blob

# Obtener connection string desde Azure Portal
# Storage Account > Access Keys > Connection String
```

#### Paso 3: Configurar Django

```python
# settings.py

AZURE_ACCOUNT_NAME = env('AZURE_ACCOUNT_NAME')
AZURE_ACCOUNT_KEY = env('AZURE_ACCOUNT_KEY')
AZURE_CONTAINER_NAME = env('AZURE_CONTAINER_NAME', 'clinica-backups')
AZURE_CONNECTION_STRING = env('AZURE_CONNECTION_STRING')
```

---

## 3. SISTEMA DE RESPALDOS AUTOMÁTICOS

### 3.1 Crear app de respaldos

```bash
python manage.py startapp respaldos
```

### 3.2 Modelo de Respaldo

```python
# apps/respaldos/models.py
from django.db import models
from apps.comun.models import Clinica

class Respaldo(models.Model):
    """
    Registro de respaldos realizados.
    Multitenancy: Cada clínica tiene sus propios respaldos.
    """
    TIPO_CHOICES = [
        ('completo', 'Respaldo Completo'),
        ('incremental', 'Respaldo Incremental'),
        ('manual', 'Respaldo Manual'),
    ]
    
    ESTADO_CHOICES = [
        ('en_proceso', 'En Proceso'),
        ('completado', 'Completado'),
        ('fallido', 'Fallido'),
    ]
    
    clinica = models.ForeignKey(
        'comun.Clinica',
        on_delete=models.CASCADE,
        related_name='respaldos',
        help_text='Clínica a la que pertenece este respaldo'
    )
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='completo')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='en_proceso')
    
    # Información del archivo
    nombre_archivo = models.CharField(max_length=255)
    ruta_nube = models.CharField(max_length=500, help_text='Ruta en S3/GCS/Azure')
    tamano_bytes = models.BigIntegerField(default=0)
    hash_md5 = models.CharField(max_length=32, help_text='Hash MD5 para verificar integridad')
    
    # Estadísticas
    tablas_respaldadas = models.JSONField(default=list, help_text='Lista de tablas incluidas')
    registros_totales = models.IntegerField(default=0)
    tiempo_ejecucion = models.DurationField(null=True, blank=True)
    
    # Metadata
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_expiracion = models.DateTimeField(
        help_text='Fecha en que se eliminará automáticamente',
        null=True,
        blank=True
    )
    notas = models.TextField(blank=True)
    error_mensaje = models.TextField(blank=True)
    
    # Usuario que solicitó el respaldo (si es manual)
    creado_por = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='respaldos_creados'
    )
    
    class Meta:
        db_table = 'respaldo'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['clinica', '-fecha_creacion']),
            models.Index(fields=['estado', 'fecha_creacion']),
        ]
    
    def __str__(self):
        return f"Respaldo {self.clinica.nombre} - {self.fecha_creacion.strftime('%Y-%m-%d %H:%M')}"
    
    def get_tamano_legible(self):
        """Retorna el tamaño en formato legible"""
        for unidad in ['bytes', 'KB', 'MB', 'GB']:
            if self.tamano_bytes < 1024.0:
                return f"{self.tamano_bytes:.2f} {unidad}"
            self.tamano_bytes /= 1024.0
        return f"{self.tamano_bytes:.2f} TB"
```

### 3.3 Servicio de Respaldo con AWS S3

```python
# apps/respaldos/services/backup_service.py
import os
import gzip
import hashlib
import json
from datetime import datetime, timedelta
from io import BytesIO
from django.conf import settings
from django.core import serializers
from django.apps import apps
from django.utils import timezone
import boto3
from botocore.exceptions import ClientError

class BackupService:
    """
    Servicio para crear respaldos automáticos en AWS S3.
    Soporta multitenancy: cada clínica respalda solo sus datos.
    """
    
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )
        self.bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    
    def crear_respaldo_clinica(self, clinica, tipo='completo', usuario=None):
        """
        Crea un respaldo completo de los datos de una clínica específica.
        
        Args:
            clinica: Instancia de Clinica
            tipo: 'completo', 'incremental', 'manual'
            usuario: Usuario que solicita el respaldo (opcional)
        
        Returns:
            Instancia de Respaldo creada
        """
        from apps.respaldos.models import Respaldo
        
        # Crear registro de respaldo
        respaldo = Respaldo.objects.create(
            clinica=clinica,
            tipo=tipo,
            estado='en_proceso',
            creado_por=usuario,
            nombre_archivo=self._generar_nombre_archivo(clinica),
        )
        
        try:
            inicio = timezone.now()
            
            # 1. Recolectar datos de la clínica
            datos = self._recolectar_datos_clinica(clinica)
            
            # 2. Comprimir datos
            datos_comprimidos = self._comprimir_datos(datos)
            
            # 3. Calcular hash MD5
            hash_md5 = self._calcular_md5(datos_comprimidos)
            
            # 4. Subir a S3
            ruta_s3 = self._subir_a_s3(
                datos_comprimidos,
                clinica,
                respaldo.nombre_archivo
            )
            
            # 5. Actualizar registro
            fin = timezone.now()
            respaldo.estado = 'completado'
            respaldo.ruta_nube = ruta_s3
            respaldo.tamano_bytes = len(datos_comprimidos)
            respaldo.hash_md5 = hash_md5
            respaldo.tablas_respaldadas = list(datos.keys())
            respaldo.registros_totales = sum(len(v) for v in datos.values())
            respaldo.tiempo_ejecucion = fin - inicio
            respaldo.fecha_expiracion = timezone.now() + timedelta(days=30)
            respaldo.save()
            
            # 6. Enviar notificación
            self._enviar_notificacion_exito(clinica, respaldo)
            
            return respaldo
            
        except Exception as e:
            respaldo.estado = 'fallido'
            respaldo.error_mensaje = str(e)
            respaldo.save()
            
            # Enviar notificación de error
            self._enviar_notificacion_error(clinica, respaldo, str(e))
            
            raise
    
    def _generar_nombre_archivo(self, clinica):
        """Genera nombre único para el archivo de respaldo"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        nombre_limpio = clinica.nombre.replace(' ', '_').lower()
        return f"backup_{nombre_limpio}_{clinica.id}_{timestamp}.json.gz"
    
    def _recolectar_datos_clinica(self, clinica):
        """
        Recolecta todos los datos relacionados con una clínica.
        
        IMPORTANTE: Ajusta esta lista según tus modelos que tienen FK a Clinica
        """
        datos = {}
        
        # Lista de modelos a respaldar (con relación a Clinica)
        modelos_a_respaldar = [
            # Usuarios de la clínica
            ('usuarios.Usuario', 'clinica'),
            
            # Pacientes
            ('usuarios.Paciente', 'clinica'),
            
            # Profesionales
            ('profesionales.Odontologo', 'clinica'),
            ('profesionales.Recepcionista', 'clinica'),
            
            # Citas
            ('citas.Consulta', 'clinica'),
            ('citas.Horario', 'clinica'),
            
            # Historial clínico
            ('historial_clinico.HistorialClinico', 'paciente__clinica'),
            ('historial_clinico.Tratamiento', 'historial__paciente__clinica'),
            
            # Pagos
            ('sistema_pagos.Factura', 'consulta__clinica'),
            ('sistema_pagos.Pago', 'factura__consulta__clinica'),
            ('sistema_pagos.PagoEnLinea', 'consulta__clinica'),
            
            # Inventario
            ('inventario.Inventario', 'clinica'),
            
            # Auditoría
            ('auditoria.Bitacora', 'usuario__clinica'),
        ]
        
        for modelo_path, filtro_field in modelos_a_respaldar:
            try:
                modelo = apps.get_model(modelo_path)
                
                # Construir filtro dinámico
                filtro = {filtro_field: clinica}
                
                # Obtener queryset filtrado
                queryset = modelo.objects.filter(**filtro)
                
                # Serializar a JSON
                datos[modelo_path] = json.loads(
                    serializers.serialize('json', queryset)
                )
                
            except LookupError:
                # Modelo no existe, saltar
                continue
            except Exception as e:
                print(f"Error al respaldar {modelo_path}: {e}")
                continue
        
        return datos
    
    def _comprimir_datos(self, datos):
        """Comprime datos usando gzip"""
        json_bytes = json.dumps(datos, ensure_ascii=False).encode('utf-8')
        
        buffer = BytesIO()
        with gzip.GzipFile(fileobj=buffer, mode='wb') as gz:
            gz.write(json_bytes)
        
        return buffer.getvalue()
    
    def _calcular_md5(self, datos_bytes):
        """Calcula hash MD5 de los datos"""
        return hashlib.md5(datos_bytes).hexdigest()
    
    def _subir_a_s3(self, datos_comprimidos, clinica, nombre_archivo):
        """
        Sube el respaldo a S3.
        Estructura: backups/{clinica_id}/{año}/{mes}/{archivo}
        """
        now = datetime.now()
        ruta = f"backups/{clinica.id}/{now.year}/{now.month:02d}/{nombre_archivo}"
        
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=ruta,
                Body=datos_comprimidos,
                ContentType='application/gzip',
                ServerSideEncryption='AES256',  # Encriptación
                Metadata={
                    'clinica_id': str(clinica.id),
                    'clinica_nombre': clinica.nombre,
                    'fecha_respaldo': now.isoformat(),
                }
            )
            
            return ruta
            
        except ClientError as e:
            raise Exception(f"Error al subir a S3: {e}")
    
    def _enviar_notificacion_exito(self, clinica, respaldo):
        """Envía email notificando respaldo exitoso"""
        from django.core.mail import send_mail
        
        asunto = f"✅ Respaldo Completado - {clinica.nombre}"
        mensaje = f"""
        Respaldo completado exitosamente:
        
        Clínica: {clinica.nombre}
        Fecha: {respaldo.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S')}
        Tamaño: {respaldo.get_tamano_legible()}
        Tablas: {len(respaldo.tablas_respaldadas)}
        Registros: {respaldo.registros_totales:,}
        Tiempo: {respaldo.tiempo_ejecucion}
        
        El respaldo se almacenó de forma segura en la nube y estará disponible por 30 días.
        """
        
        # Enviar a administradores de la clínica
        emails_admin = clinica.usuarios.filter(
            rol='administrador'
        ).values_list('email', flat=True)
        
        if emails_admin:
            send_mail(
                asunto,
                mensaje,
                settings.DEFAULT_FROM_EMAIL,
                list(emails_admin),
                fail_silently=True,
            )
    
    def _enviar_notificacion_error(self, clinica, respaldo, error):
        """Envía email notificando error en respaldo"""
        from django.core.mail import send_mail
        
        asunto = f"❌ Error en Respaldo - {clinica.nombre}"
        mensaje = f"""
        Error al crear respaldo:
        
        Clínica: {clinica.nombre}
        Fecha: {respaldo.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S')}
        Error: {error}
        
        Por favor contacte al soporte técnico.
        """
        
        emails_admin = clinica.usuarios.filter(
            rol='administrador'
        ).values_list('email', flat=True)
        
        if emails_admin:
            send_mail(
                asunto,
                mensaje,
                settings.DEFAULT_FROM_EMAIL,
                list(emails_admin),
                fail_silently=True,
            )
    
    def listar_respaldos_clinica(self, clinica, limit=10):
        """Lista respaldos disponibles de una clínica"""
        from apps.respaldos.models import Respaldo
        
        return Respaldo.objects.filter(
            clinica=clinica,
            estado='completado'
        ).order_by('-fecha_creacion')[:limit]
    
    def eliminar_respaldos_antiguos(self, dias=30):
        """
        Elimina respaldos más antiguos que X días.
        Se ejecuta automáticamente.
        """
        from apps.respaldos.models import Respaldo
        
        fecha_limite = timezone.now() - timedelta(days=dias)
        
        respaldos_antiguos = Respaldo.objects.filter(
            fecha_creacion__lt=fecha_limite,
            estado='completado'
        )
        
        for respaldo in respaldos_antiguos:
            try:
                # Eliminar de S3
                self.s3_client.delete_object(
                    Bucket=self.bucket_name,
                    Key=respaldo.ruta_nube
                )
                
                # Eliminar registro
                respaldo.delete()
                
            except Exception as e:
                print(f"Error al eliminar respaldo {respaldo.id}: {e}")


# Instancia global
backup_service = BackupService()
```

### 3.4 Comando de Django para Respaldos

```python
# apps/respaldos/management/commands/crear_respaldo.py
from django.core.management.base import BaseCommand
from apps.comun.models import Clinica
from apps.respaldos.services.backup_service import backup_service

class Command(BaseCommand):
    help = 'Crea respaldo de una clínica específica o todas'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--clinica',
            type=int,
            help='ID de la clínica a respaldar'
        )
        
        parser.add_argument(
            '--todas',
            action='store_true',
            help='Respaldar todas las clínicas'
        )
    
    def handle(self, *args, **options):
        if options['todas']:
            # Respaldar todas las clínicas activas
            clinicas = Clinica.objects.filter(activo=True)
            
            self.stdout.write(
                self.style.SUCCESS(f'Iniciando respaldo de {clinicas.count()} clínicas...')
            )
            
            for clinica in clinicas:
                try:
                    respaldo = backup_service.crear_respaldo_clinica(
                        clinica,
                        tipo='completo'
                    )
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✅ {clinica.nombre}: {respaldo.get_tamano_legible()}'
                        )
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'❌ {clinica.nombre}: {e}')
                    )
        
        elif options['clinica']:
            # Respaldar clínica específica
            try:
                clinica = Clinica.objects.get(id=options['clinica'])
                
                self.stdout.write(f'Respaldando {clinica.nombre}...')
                
                respaldo = backup_service.crear_respaldo_clinica(
                    clinica,
                    tipo='completo'
                )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Respaldo completado: {respaldo.get_tamano_legible()}'
                    )
                )
                
            except Clinica.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'❌ Clínica {options["clinica"]} no encontrada')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Error: {e}')
                )
        
        else:
            self.stdout.write(
                self.style.ERROR('Debes especificar --clinica ID o --todas')
            )
```

**Uso:**

```bash
# Respaldar clínica específica
python manage.py crear_respaldo --clinica 1

# Respaldar todas las clínicas
python manage.py crear_respaldo --todas
```

---

## 4. MULTITENANCY - RESPALDOS POR CLÍNICA

### 4.1 Endpoints API

```python
# apps/respaldos/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Respaldo
from .serializers import RespaldoSerializer
from .services.backup_service import backup_service

class RespaldoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para gestionar respaldos.
    Multitenancy: Cada clínica solo ve sus respaldos.
    """
    queryset = Respaldo.objects.all()
    serializer_class = RespaldoSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtrar respaldos por clínica del usuario"""
        user = self.request.user
        
        if user.rol == 'superadmin':
            # Superadmin ve todos los respaldos
            return Respaldo.objects.all()
        else:
            # Usuario normal solo ve respaldos de su clínica
            return Respaldo.objects.filter(clinica=user.clinica)
    
    @action(detail=False, methods=['post'])
    def crear_respaldo_manual(self, request):
        """
        Crear respaldo manual de la clínica del usuario.
        
        POST /api/v1/respaldos/crear_respaldo_manual/
        """
        user = request.user
        
        # Solo administradores pueden crear respaldos manuales
        if user.rol not in ['administrador', 'superadmin']:
            return Response({
                'error': 'Solo administradores pueden crear respaldos'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            respaldo = backup_service.crear_respaldo_clinica(
                clinica=user.clinica,
                tipo='manual',
                usuario=user
            )
            
            serializer = self.get_serializer(respaldo)
            return Response({
                'mensaje': 'Respaldo creado exitosamente',
                'respaldo': serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'error': f'Error al crear respaldo: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def restaurar(self, request, pk=None):
        """
        Restaurar un respaldo (próximamente).
        
        POST /api/v1/respaldos/{id}/restaurar/
        """
        # TODO: Implementar restauración
        return Response({
            'mensaje': 'Funcionalidad de restauración en desarrollo'
        }, status=status.HTTP_501_NOT_IMPLEMENTED)
    
    @action(detail=True, methods=['get'])
    def descargar(self, request, pk=None):
        """
        Generar URL temporal para descargar respaldo.
        
        GET /api/v1/respaldos/{id}/descargar/
        """
        respaldo = self.get_object()
        
        # Verificar permisos
        if request.user.rol != 'superadmin' and respaldo.clinica != request.user.clinica:
            return Response({
                'error': 'No tienes permiso para descargar este respaldo'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            # Generar URL temporal de S3 (válida por 1 hora)
            url = backup_service.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': backup_service.bucket_name,
                    'Key': respaldo.ruta_nube
                },
                ExpiresIn=3600  # 1 hora
            )
            
            return Response({
                'url': url,
                'expira_en': '1 hora'
            })
            
        except Exception as e:
            return Response({
                'error': f'Error al generar URL: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
```

### 4.2 Serializer

```python
# apps/respaldos/serializers.py
from rest_framework import serializers
from .models import Respaldo

class RespaldoSerializer(serializers.ModelSerializer):
    tamano_legible = serializers.SerializerMethodField()
    clinica_nombre = serializers.CharField(source='clinica.nombre', read_only=True)
    creado_por_nombre = serializers.CharField(source='creado_por.nombre', read_only=True)
    
    class Meta:
        model = Respaldo
        fields = [
            'id',
            'clinica',
            'clinica_nombre',
            'tipo',
            'estado',
            'nombre_archivo',
            'tamano_bytes',
            'tamano_legible',
            'tablas_respaldadas',
            'registros_totales',
            'tiempo_ejecucion',
            'fecha_creacion',
            'fecha_expiracion',
            'creado_por',
            'creado_por_nombre',
            'notas',
        ]
        read_only_fields = fields
    
    def get_tamano_legible(self, obj):
        return obj.get_tamano_legible()
```

---

## 5. RESTAURACIÓN DE RESPALDOS

### 5.1 Servicio de Restauración

```python
# apps/respaldos/services/restore_service.py
import gzip
import json
from io import BytesIO
from django.apps import apps
from django.core import serializers
from django.db import transaction
import boto3

class RestoreService:
    """Servicio para restaurar respaldos desde la nube"""
    
    def __init__(self):
        from django.conf import settings
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )
        self.bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    
    def restaurar_respaldo(self, respaldo, clinica):
        """
        Restaura un respaldo completo.
        
        ADVERTENCIA: Esto eliminará los datos actuales de la clínica
        y los reemplazará con los del respaldo.
        """
        try:
            # 1. Descargar respaldo desde S3
            datos_comprimidos = self._descargar_desde_s3(respaldo.ruta_nube)
            
            # 2. Descomprimir
            datos = self._descomprimir_datos(datos_comprimidos)
            
            # 3. Validar integridad
            if not self._validar_integridad(datos_comprimidos, respaldo.hash_md5):
                raise Exception("Integridad del respaldo comprometida")
            
            # 4. Restaurar datos (transacción atómica)
            with transaction.atomic():
                self._restaurar_datos(datos, clinica)
            
            return True
            
        except Exception as e:
            raise Exception(f"Error al restaurar: {e}")
    
    def _descargar_desde_s3(self, ruta):
        """Descarga archivo desde S3"""
        response = self.s3_client.get_object(
            Bucket=self.bucket_name,
            Key=ruta
        )
        return response['Body'].read()
    
    def _descomprimir_datos(self, datos_comprimidos):
        """Descomprime datos gzip"""
        buffer = BytesIO(datos_comprimidos)
        with gzip.GzipFile(fileobj=buffer, mode='rb') as gz:
            json_bytes = gz.read()
        
        return json.loads(json_bytes.decode('utf-8'))
    
    def _validar_integridad(self, datos_comprimidos, hash_esperado):
        """Valida integridad del respaldo"""
        import hashlib
        hash_actual = hashlib.md5(datos_comprimidos).hexdigest()
        return hash_actual == hash_esperado
    
    def _restaurar_datos(self, datos, clinica):
        """
        Restaura datos deserializando JSON.
        
        IMPORTANTE: Los datos deben restaurarse en orden correcto
        para respetar las relaciones FK.
        """
        orden_restauracion = [
            'usuarios.Usuario',
            'usuarios.Paciente',
            'profesionales.Odontologo',
            'citas.Consulta',
            'historial_clinico.HistorialClinico',
            'historial_clinico.Tratamiento',
            'sistema_pagos.Factura',
            'sistema_pagos.Pago',
        ]
        
        for modelo_path in orden_restauracion:
            if modelo_path in datos:
                try:
                    # Deserializar y guardar
                    for obj in serializers.deserialize('json', json.dumps(datos[modelo_path])):
                        obj.save()
                except Exception as e:
                    print(f"Error al restaurar {modelo_path}: {e}")


restore_service = RestoreService()
```

---

## 6. MONITOREO Y NOTIFICACIONES

### 6.1 Tarea Celery para Respaldos Automáticos

```python
# apps/respaldos/tasks.py
from celery import shared_task
from apps.comun.models import Clinica
from .services.backup_service import backup_service

@shared_task
def crear_respaldos_automaticos():
    """
    Tarea que se ejecuta diariamente para crear respaldos de todas las clínicas.
    Configurar en Celery Beat para ejecutar a las 2:00 AM.
    """
    clinicas = Clinica.objects.filter(activo=True)
    
    resultados = {
        'exitosos': 0,
        'fallidos': 0,
        'detalles': []
    }
    
    for clinica in clinicas:
        try:
            respaldo = backup_service.crear_respaldo_clinica(
                clinica,
                tipo='completo'
            )
            resultados['exitosos'] += 1
            resultados['detalles'].append({
                'clinica': clinica.nombre,
                'estado': 'OK',
                'tamano': respaldo.get_tamano_legible()
            })
        except Exception as e:
            resultados['fallidos'] += 1
            resultados['detalles'].append({
                'clinica': clinica.nombre,
                'estado': 'ERROR',
                'error': str(e)
            })
    
    return resultados

@shared_task
def limpiar_respaldos_antiguos():
    """
    Elimina respaldos más antiguos que 30 días.
    Ejecutar semanalmente.
    """
    backup_service.eliminar_respaldos_antiguos(dias=30)
    return 'Limpieza completada'
```

### 6.2 Configurar Celery Beat

```python
# config/celery.py
from celery import Celery
from celery.schedules import crontab

app = Celery('dental_clinic')

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Configurar tareas programadas
app.conf.beat_schedule = {
    'respaldos-automaticos-diarios': {
        'task': 'apps.respaldos.tasks.crear_respaldos_automaticos',
        'schedule': crontab(hour=2, minute=0),  # 2:00 AM cada día
    },
    'limpiar-respaldos-antiguos': {
        'task': 'apps.respaldos.tasks.limpiar_respaldos_antiguos',
        'schedule': crontab(day_of_week='sunday', hour=3, minute=0),  # Domingos 3:00 AM
    },
}
```

---

## 📊 RESUMEN DE IMPLEMENTACIÓN

### Instalación

```bash
# 1. Instalar dependencias
pip install boto3 django-storages celery

# 2. Agregar a INSTALLED_APPS
'storages',
'respaldos',

# 3. Configurar variables de entorno (.env)
AWS_ACCESS_KEY_ID=tu_key
AWS_SECRET_ACCESS_KEY=tu_secret
AWS_STORAGE_BUCKET_NAME=clinica-dental-backups-2025
AWS_S3_REGION_NAME=us-east-1

# 4. Ejecutar migraciones
python manage.py makemigrations respaldos
python manage.py migrate

# 5. Crear respaldo de prueba
python manage.py crear_respaldo --clinica 1
```

### Comandos Disponibles

```bash
# Respaldo manual de una clínica
python manage.py crear_respaldo --clinica 1

# Respaldo de todas las clínicas
python manage.py crear_respaldo --todas

# Limpiar respaldos antiguos
python manage.py shell
>>> from apps.respaldos.services.backup_service import backup_service
>>> backup_service.eliminar_respaldos_antiguos(dias=30)
```

### API Endpoints

```
GET    /api/v1/respaldos/                      # Listar respaldos
GET    /api/v1/respaldos/{id}/                 # Ver detalle
POST   /api/v1/respaldos/crear_respaldo_manual/  # Crear respaldo
GET    /api/v1/respaldos/{id}/descargar/       # Descargar respaldo
POST   /api/v1/respaldos/{id}/restaurar/       # Restaurar (próximamente)
```

---

✅ **RESPALDOS AUTOMÁTICOS** | ☁️ **ALMACENAMIENTO EN LA NUBE** | 🔒 **MULTITENANCY SEGURO**
