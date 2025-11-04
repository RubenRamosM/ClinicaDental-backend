#!/usr/bin/env bash
# exit on error
set -o errexit

echo "🔧 Instalando dependencias de Python..."
pip install -r requirements.txt

echo "📦 Recolectando archivos estáticos..."
python manage.py collectstatic --no-input

echo "🔍 DEBUG: Verificando variable DATABASE_URL..."
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL no está definida!"
    exit 1
else
    echo "✅ DATABASE_URL está definida (primeros 50 caracteres):"
    echo "${DATABASE_URL:0:50}..."
fi

echo "️ Aplicando migraciones al schema público (shared)..."
python manage.py migrate_schemas --shared

echo "✅ Schema público creado. No hay tenants que migrar en el primer deploy."
echo "✅ Build completado exitosamente!"
