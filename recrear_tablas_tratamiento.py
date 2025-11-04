"""
Script para recrear las tablas de tratamiento que fueron eliminadas por error
en la migración historial_clinico.0008
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

def recrear_tablas():
    """Recrea las tablas de tratamiento si no existen"""
    
    with connection.cursor() as cursor:
        print("🔍 Verificando tablas existentes...")
        
        # Verificar qué tablas existen
        cursor.execute("""
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public' 
            AND tablename IN ('plan_tratamiento', 'presupuesto', 'item_presupuesto', 'procedimiento')
            ORDER BY tablename;
        """)
        
        tablas_existentes = [row[0] for row in cursor.fetchall()]
        print(f"Tablas existentes: {tablas_existentes}")
        
        # Crear plan_tratamiento si no existe
        if 'plan_tratamiento' not in tablas_existentes:
            print("\n📦 Creando tabla plan_tratamiento...")
            cursor.execute("""
                CREATE TABLE plan_tratamiento (
                    id bigserial PRIMARY KEY,
                    codigo varchar(50) UNIQUE NOT NULL,
                    descripcion text NOT NULL,
                    diagnostico text,
                    observaciones text,
                    estado varchar(20) NOT NULL DEFAULT 'borrador',
                    fecha_creacion timestamp with time zone NOT NULL DEFAULT NOW(),
                    fecha_aprobacion timestamp with time zone,
                    fecha_inicio date,
                    fecha_finalizacion date,
                    duracion_estimada_dias integer,
                    pacientecodigo bigint NOT NULL REFERENCES paciente(codusuario) ON DELETE CASCADE,
                    odontologocodigo bigint REFERENCES odontologo(codusuario) ON DELETE SET NULL
                );
                
                CREATE INDEX plan_tratamiento_codigo_idx ON plan_tratamiento(codigo);
                CREATE INDEX plan_tratamiento_estado_idx ON plan_tratamiento(estado);
                CREATE INDEX plan_tratamiento_paciente_idx ON plan_tratamiento(pacientecodigo);
                CREATE INDEX plan_tratamiento_odontologo_idx ON plan_tratamiento(odontologocodigo);
            """)
            print("✅ Tabla plan_tratamiento creada")
        else:
            print("✅ Tabla plan_tratamiento ya existe")
        
        # Crear presupuesto si no existe
        if 'presupuesto' not in tablas_existentes:
            print("\n📦 Creando tabla presupuesto...")
            cursor.execute("""
                CREATE TABLE presupuesto (
                    id bigserial PRIMARY KEY,
                    codigo varchar(50) UNIQUE NOT NULL,
                    subtotal numeric(10,2) NOT NULL CHECK (subtotal >= 0),
                    descuento numeric(10,2) NOT NULL DEFAULT 0 CHECK (descuento >= 0),
                    impuesto numeric(10,2) NOT NULL DEFAULT 0 CHECK (impuesto >= 0),
                    total numeric(10,2) NOT NULL CHECK (total >= 0),
                    estado varchar(20) NOT NULL DEFAULT 'pendiente',
                    notas text,
                    fecha_creacion timestamp with time zone NOT NULL DEFAULT NOW(),
                    fecha_vencimiento date,
                    fecha_aprobacion timestamp with time zone,
                    aprobado_por varchar(200),
                    motivo_rechazo text,
                    idplantratamiento bigint NOT NULL REFERENCES plan_tratamiento(id) ON DELETE CASCADE
                );
                
                CREATE INDEX presupuesto_codigo_idx ON presupuesto(codigo);
                CREATE INDEX presupuesto_estado_idx ON presupuesto(estado);
                CREATE INDEX presupuesto_plan_idx ON presupuesto(idplantratamiento);
            """)
            print("✅ Tabla presupuesto creada")
        else:
            print("✅ Tabla presupuesto ya existe")
        
        # Crear item_presupuesto si no existe
        if 'item_presupuesto' not in tablas_existentes:
            print("\n📦 Creando tabla item_presupuesto...")
            cursor.execute("""
                CREATE TABLE item_presupuesto (
                    id bigserial PRIMARY KEY,
                    descripcion text,
                    cantidad integer NOT NULL DEFAULT 1 CHECK (cantidad >= 1),
                    precio_unitario numeric(10,2) NOT NULL CHECK (precio_unitario >= 0),
                    descuento_item numeric(10,2) NOT NULL DEFAULT 0 CHECK (descuento_item >= 0),
                    total numeric(10,2) NOT NULL CHECK (total >= 0),
                    numero_diente integer CHECK (numero_diente >= 1),
                    idpresupuesto bigint NOT NULL REFERENCES presupuesto(id) ON DELETE CASCADE,
                    idservicio bigint NOT NULL REFERENCES servicio(id) ON DELETE CASCADE
                );
                
                CREATE INDEX item_presupuesto_presupuesto_idx ON item_presupuesto(idpresupuesto);
                CREATE INDEX item_presupuesto_servicio_idx ON item_presupuesto(idservicio);
            """)
            print("✅ Tabla item_presupuesto creada")
        else:
            print("✅ Tabla item_presupuesto ya existe")
        
        # Crear procedimiento si no existe
        if 'procedimiento' not in tablas_existentes:
            print("\n📦 Creando tabla procedimiento...")
            cursor.execute("""
                CREATE TABLE procedimiento (
                    id bigserial PRIMARY KEY,
                    numero_diente integer CHECK (numero_diente >= 1),
                    descripcion text NOT NULL,
                    estado varchar(20) NOT NULL DEFAULT 'pendiente',
                    fecha_planificada date,
                    fecha_realizado timestamp with time zone,
                    duracion_minutos integer,
                    costo_estimado numeric(10,2) CHECK (costo_estimado >= 0),
                    costo_real numeric(10,2) CHECK (costo_real >= 0),
                    notas text,
                    complicaciones text,
                    idplantratamiento bigint NOT NULL REFERENCES plan_tratamiento(id) ON DELETE CASCADE,
                    odontologocodigo bigint REFERENCES odontologo(codusuario) ON DELETE SET NULL,
                    idservicio bigint NOT NULL REFERENCES servicio(id) ON DELETE CASCADE
                );
                
                CREATE INDEX procedimiento_estado_idx ON procedimiento(estado);
                CREATE INDEX procedimiento_plan_idx ON procedimiento(idplantratamiento);
                CREATE INDEX procedimiento_odontologo_idx ON procedimiento(odontologocodigo);
            """)
            print("✅ Tabla procedimiento creada")
        else:
            print("✅ Tabla procedimiento ya existe")
        
        print("\n" + "="*60)
        print("✅ TODAS LAS TABLAS RESTAURADAS EXITOSAMENTE")
        print("="*60)


if __name__ == '__main__':
    try:
        recrear_tablas()
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
