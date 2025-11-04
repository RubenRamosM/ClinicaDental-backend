# Script para configurar archivo hosts en Windows
# DEBE EJECUTARSE COMO ADMINISTRADOR

# Ruta del archivo hosts
$hostsPath = "C:\Windows\System32\drivers\etc\hosts"

# Crear backup
$backupPath = "$hostsPath.backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
Copy-Item -Path $hostsPath -Destination $backupPath
Write-Host "✅ Backup creado: $backupPath" -ForegroundColor Green

# Leer contenido actual
$hostsContent = Get-Content $hostsPath

# Entradas a agregar
$entries = @"

# Django Multitenancy - Clínica Dental Backend
# Agregado el: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
127.0.0.1 localhost
127.0.0.1 clinica1.localhost
127.0.0.1 clinica2.localhost
127.0.0.1 clinica3.localhost
127.0.0.1 clinica4.localhost
127.0.0.1 clinica5.localhost
"@

# Verificar si ya existen las entradas
if ($hostsContent -match "Django Multitenancy") {
    Write-Host "⚠️  Las entradas ya existen en el archivo hosts" -ForegroundColor Yellow
    Write-Host "Si necesitas actualizarlas, edita manualmente:" -ForegroundColor Yellow
    Write-Host $hostsPath -ForegroundColor Cyan
} else {
    # Agregar al final del archivo
    Add-Content -Path $hostsPath -Value $entries
    Write-Host "✅ Entradas agregadas al archivo hosts" -ForegroundColor Green
}

# Limpiar caché DNS
Write-Host "`n🔄 Limpiando caché DNS..." -ForegroundColor Cyan
ipconfig /flushdns | Out-Null
Write-Host "✅ Caché DNS limpiada" -ForegroundColor Green

# Verificar
Write-Host "`n📋 Verificando configuración..." -ForegroundColor Cyan
Write-Host "`nProbando ping a subdominios:" -ForegroundColor Yellow

$subdominios = @('localhost', 'clinica1.localhost', 'clinica2.localhost')
foreach ($subdominio in $subdominios) {
    $result = Test-Connection -ComputerName $subdominio -Count 1 -Quiet
    if ($result) {
        Write-Host "  ✅ $subdominio" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $subdominio" -ForegroundColor Red
    }
}

Write-Host "`n🎉 Configuración completada!" -ForegroundColor Green
Write-Host "`nAhora puedes acceder a:" -ForegroundColor Cyan
Write-Host "  http://localhost:8001/api/" -ForegroundColor White
Write-Host "  http://clinica1.localhost:8001/api/" -ForegroundColor White
Write-Host "  http://clinica2.localhost:8001/api/" -ForegroundColor White
