import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

cursor = connection.cursor()
cursor.execute("""
    SELECT tablename 
    FROM pg_tables 
    WHERE schemaname = 'public' 
    AND tablename LIKE '%tratamiento%' 
    ORDER BY tablename;
""")

print("Tablas relacionadas con tratamientos:")
print("=" * 60)
for row in cursor.fetchall():
    print(f"  - {row[0]}")

print("\n" + "=" * 60)
print("Verificando modelo PlanTratamiento...")
from apps.tratamientos.models import PlanTratamiento
print(f"Nombre de tabla del modelo: {PlanTratamiento._meta.db_table}")
