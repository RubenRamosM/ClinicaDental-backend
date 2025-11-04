"""
Script para configurar AWS S3 para el proyecto de Clínica Dental
usando credenciales existentes de AWS.

Crea un bucket NUEVO sin afectar otros proyectos.
"""

import boto3
import os
from botocore.exceptions import ClientError

def configurar_bucket_clinica():
    """
    Configura un bucket S3 exclusivo para el proyecto de clínica dental.
    No afecta otros buckets o proyectos existentes.
    """
    
    # Nombre del bucket (debe ser único globalmente)
    # Formato: clinica-dental-backups-{tu-identificador}
    BUCKET_NAME = 'clinica-dental-backups-2025-bolivia'
    REGION = 'us-east-1'  # Cambiar si prefieres otra región
    
    print("=" * 60)
    print("🏥 CONFIGURACIÓN AWS S3 - CLÍNICA DENTAL")
    print("=" * 60)
    print()
    
    # 1. Verificar credenciales
    print("📋 Paso 1: Verificando credenciales AWS...")
    try:
        session = boto3.Session()
        credentials = session.get_credentials()
        
        if credentials is None:
            print("❌ No se encontraron credenciales de AWS")
            print()
            print("Para configurar:")
            print("  aws configure")
            return False
        
        print(f"✅ Credenciales encontradas")
        print(f"   Access Key: {credentials.access_key[:8]}...")
        print(f"   Region: {session.region_name or REGION}")
        print()
        
    except Exception as e:
        print(f"❌ Error al verificar credenciales: {e}")
        return False
    
    # 2. Crear cliente S3
    print("📋 Paso 2: Conectando a AWS S3...")
    try:
        s3_client = boto3.client('s3', region_name=REGION)
        print("✅ Conectado a AWS S3")
        print()
    except Exception as e:
        print(f"❌ Error al conectar: {e}")
        return False
    
    # 3. Verificar si el bucket ya existe
    print("📋 Paso 3: Verificando bucket...")
    try:
        s3_client.head_bucket(Bucket=BUCKET_NAME)
        print(f"⚠️  El bucket '{BUCKET_NAME}' ya existe")
        print("   Puedes usar este bucket o cambiar el nombre en el script")
        print()
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        
        if error_code == '404':
            # El bucket no existe, crearlo
            print(f"📦 Creando bucket '{BUCKET_NAME}'...")
            try:
                if REGION == 'us-east-1':
                    # us-east-1 no necesita LocationConstraint
                    s3_client.create_bucket(Bucket=BUCKET_NAME)
                else:
                    s3_client.create_bucket(
                        Bucket=BUCKET_NAME,
                        CreateBucketConfiguration={'LocationConstraint': REGION}
                    )
                
                print(f"✅ Bucket '{BUCKET_NAME}' creado exitosamente")
                print()
                
            except ClientError as create_error:
                print(f"❌ Error al crear bucket: {create_error}")
                print()
                print("Posibles soluciones:")
                print("1. El nombre del bucket ya está en uso (deben ser únicos globalmente)")
                print("2. Cambia el BUCKET_NAME en este script a algo único")
                print("3. Ejemplo: 'clinica-dental-tu-ciudad-2025'")
                return False
        else:
            print(f"❌ Error al verificar bucket: {e}")
            return False
    
    # 4. Configurar políticas de seguridad
    print("📋 Paso 4: Configurando seguridad del bucket...")
    try:
        # Bloquear acceso público (seguridad)
        s3_client.put_public_access_block(
            Bucket=BUCKET_NAME,
            PublicAccessBlockConfiguration={
                'BlockPublicAcls': True,
                'IgnorePublicAcls': True,
                'BlockPublicPolicy': True,
                'RestrictPublicBuckets': True
            }
        )
        print("✅ Acceso público bloqueado (privado)")
        
        # Habilitar encriptación
        s3_client.put_bucket_encryption(
            Bucket=BUCKET_NAME,
            ServerSideEncryptionConfiguration={
                'Rules': [
                    {
                        'ApplyServerSideEncryptionByDefault': {
                            'SSEAlgorithm': 'AES256'
                        }
                    }
                ]
            }
        )
        print("✅ Encriptación AES256 habilitada")
        print()
        
    except ClientError as e:
        print(f"⚠️  Advertencia al configurar seguridad: {e}")
        print("   El bucket está creado pero sin configuración de seguridad adicional")
        print()
    
    # 5. Crear estructura de carpetas de prueba
    print("📋 Paso 5: Creando estructura de carpetas...")
    try:
        # Crear una carpeta de ejemplo (backups/test/)
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key='backups/README.txt',
            Body=b'Este es el directorio de respaldos de la Clinica Dental\n'
        )
        print("✅ Estructura de carpetas creada")
        print()
        
    except ClientError as e:
        print(f"⚠️  No se pudo crear estructura: {e}")
        print()
    
    # 6. Listar buckets existentes
    print("📋 Paso 6: Buckets en tu cuenta AWS:")
    try:
        response = s3_client.list_buckets()
        for bucket in response['Buckets']:
            if bucket['Name'] == BUCKET_NAME:
                print(f"   ✅ {bucket['Name']} (CLÍNICA DENTAL - NUEVO)")
            else:
                print(f"   📦 {bucket['Name']} (otros proyectos)")
        print()
        
    except Exception as e:
        print(f"⚠️  No se pudo listar buckets: {e}")
        print()
    
    # 7. Generar configuración para .env
    print("=" * 60)
    print("✅ CONFIGURACIÓN COMPLETADA")
    print("=" * 60)
    print()
    print("📝 Agrega estas líneas a tu archivo .env:")
    print()
    print(f"AWS_ACCESS_KEY_ID={credentials.access_key}")
    print(f"AWS_SECRET_ACCESS_KEY={credentials.secret_key}")
    print(f"AWS_STORAGE_BUCKET_NAME={BUCKET_NAME}")
    print(f"AWS_S3_REGION_NAME={REGION}")
    print()
    print("=" * 60)
    print()
    print("🎯 Próximos pasos:")
    print("1. Copia las variables de arriba a tu .env")
    print("2. Instala: pip install boto3 django-storages")
    print("3. Ejecuta: python manage.py crear_respaldo --clinica 1")
    print()
    print("💡 Nota: Este bucket es INDEPENDIENTE de tus otros proyectos")
    print("   No hay riesgo de conflictos o sobreescritura de datos")
    print()
    
    return True


if __name__ == '__main__':
    try:
        configurar_bucket_clinica()
    except KeyboardInterrupt:
        print("\n\n❌ Configuración cancelada por el usuario")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
