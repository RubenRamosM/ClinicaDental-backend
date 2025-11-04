"""
Script para crear las tablas de multitenancy directamente en PostgreSQL
"""
import os
import django
import psycopg2
from psycopg2 import sql

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings

# Obtener credenciales de la base de datos
db_settings = settings.DATABASES['default']

# Conectar a PostgreSQL
conn = psycopg2.connect(
    dbname=db_settings['NAME'],
    user=db_settings['USER'],
    password=db_settings['PASSWORD'],
    host=db_settings['HOST'],
    port=db_settings['PORT']
)
conn.autocommit = True
cursor = conn.cursor()

print("🔧 Creando tablas de multitenancy...")
print("")

# Crear tabla comun_clinica
print("1. Creando tabla comun_clinica...")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS comun_clinica (
        id BIGSERIAL PRIMARY KEY,
        schema_name VARCHAR(63) NOT NULL UNIQUE,
        nombre VARCHAR(200) NOT NULL,
        ruc VARCHAR(20) NOT NULL UNIQUE,
        direccion TEXT,
        telefono VARCHAR(50),
        email VARCHAR(254),
        admin_nombre VARCHAR(200) NOT NULL,
        admin_email VARCHAR(254) NOT NULL,
        admin_telefono VARCHAR(50),
        activa BOOLEAN NOT NULL DEFAULT TRUE,
        fecha_creacion TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
        fecha_actualizacion TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
        plan VARCHAR(20) NOT NULL DEFAULT 'basico',
        max_usuarios INTEGER NOT NULL DEFAULT 10,
        max_pacientes INTEGER NOT NULL DEFAULT 100,
        logo_url VARCHAR(200)
    );
""")
print("   ✅ Tabla comun_clinica creada")

# Crear índices para comun_clinica
print("2. Creando índices para comun_clinica...")
cursor.execute("""
    CREATE INDEX IF NOT EXISTS comun_clinica_schema_name_idx 
    ON comun_clinica(schema_name);
""")
cursor.execute("""
    CREATE INDEX IF NOT EXISTS comun_clinica_activa_idx 
    ON comun_clinica(activa);
""")
print("   ✅ Índices creados")

# Crear tabla comun_dominio
print("3. Creando tabla comun_dominio...")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS comun_dominio (
        id BIGSERIAL PRIMARY KEY,
        domain VARCHAR(253) NOT NULL UNIQUE,
        is_primary BOOLEAN NOT NULL DEFAULT TRUE,
        tenant_id BIGINT NOT NULL REFERENCES comun_clinica(id) ON DELETE CASCADE
    );
""")
print("   ✅ Tabla comun_dominio creada")

# Crear índices para comun_dominio
print("4. Creando índices para comun_dominio...")
cursor.execute("""
    CREATE INDEX IF NOT EXISTS comun_dominio_domain_idx 
    ON comun_dominio(domain);
""")
cursor.execute("""
    CREATE INDEX IF NOT EXISTS comun_dominio_tenant_id_idx 
    ON comun_dominio(tenant_id);
""")
cursor.execute("""
    CREATE INDEX IF NOT EXISTS comun_dominio_is_primary_idx 
    ON comun_dominio(is_primary);
""")
print("   ✅ Índices creados")

cursor.close()
conn.close()

print("")
print("=" * 60)
print("✅ TABLAS DE MULTITENANCY CREADAS EXITOSAMENTE")
print("=" * 60)
print("")
print("📝 SIGUIENTE PASO:")
print("   Ejecutar: python crear_tenant_publico.py")
print("")
