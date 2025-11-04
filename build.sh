#!/usr/bin/env bash
# exit on error
set -o errexit

echo "🔧 Instalando dependencias de Python..."
pip install -r requirements.txt

echo "📦 Recolectando archivos estáticos..."
python manage.py collectstatic --no-input

echo "🗄️ Aplicando migraciones al schema público..."
python manage.py migrate_schemas --shared

echo "🏥 Creando schemas de tenants existentes..."
python manage.py migrate_schemas

echo "✅ Build completado exitosamente!"
