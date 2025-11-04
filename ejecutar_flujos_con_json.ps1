# Script para ejecutar el seeder y todos los flujos generando JSON
# Ejecutar desde el directorio raiz del proyecto

Write-Host "=== EJECUTANDO SEEDER ===" -ForegroundColor Cyan
py -3.13 seed_database.py --force

Write-Host "`n=== EJECUTANDO FLUJO 01 ===" -ForegroundColor Cyan
cd pruebas_py
py -3.13 flujo_01_autenticacion.py

Write-Host "`n=== ARCHIVOS JSON GENERADOS ===" -ForegroundColor Green
Get-ChildItem *.json | Format-Table Name, Length, LastWriteTime
