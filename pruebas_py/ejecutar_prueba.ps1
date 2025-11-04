# Script PowerShell para ejecutar las pruebas de manera fácil
# Uso: .\ejecutar_prueba.ps1 00
#      .\ejecutar_prueba.ps1 01
#      etc.

param(
    [Parameter(Mandatory=$true)]
    [string]$NumeroFlujo
)

$pythonExe = "C:\Users\asus\AppData\Local\Programs\Python\Python313\python.exe"
$scriptPath = ".\flujo_$NumeroFlujo`_*.py"

# Buscar el archivo que coincida
$archivo = Get-ChildItem -Path . -Filter "flujo_$NumeroFlujo`_*.py" | Select-Object -First 1

if ($archivo) {
    Write-Host "`n🚀 Ejecutando: $($archivo.Name)" -ForegroundColor Cyan
    Write-Host "─────────────────────────────────────────────────────────────`n" -ForegroundColor Cyan
    
    & $pythonExe $archivo.Name
    
    Write-Host "`n─────────────────────────────────────────────────────────────" -ForegroundColor Cyan
    Write-Host "✅ Prueba completada: $($archivo.Name)" -ForegroundColor Green
} else {
    Write-Host "`n❌ Error: No se encontró el flujo $NumeroFlujo" -ForegroundColor Red
    Write-Host "`nFlujos disponibles:" -ForegroundColor Yellow
    Get-ChildItem -Path . -Filter "flujo_*.py" | ForEach-Object {
        Write-Host "  - $($_.Name)" -ForegroundColor White
    }
}
