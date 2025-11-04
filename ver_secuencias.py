import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

cursor = connection.cursor()
cursor.execute("""
    SELECT sequence_name 
    FROM information_schema.sequences 
    WHERE sequence_name LIKE '%tipodeusuario%' 
       OR sequence_name LIKE '%consulta%' 
       OR sequence_name LIKE '%pago%'
       OR sequence_name LIKE '%factura%'
    ORDER BY sequence_name
""")

print("\nSecuencias encontradas:")
print("=" * 60)
for row in cursor.fetchall():
    print(row[0])
print("=" * 60)
