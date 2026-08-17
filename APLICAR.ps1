$ErrorActionPreference="Stop"

if (!(Test-Path ".\front\src\components\Modules.tsx")) {
  throw "Ejecutá este script desde la raíz de dirac-admin."
}

Get-Process node -ErrorAction SilentlyContinue | Stop-Process -Force

python ".\tools\aplicar_proveedores_ejecutivo.py"

Write-Host ""
Write-Host "Proveedores Ejecutivo aplicado." -ForegroundColor Green
Write-Host "Requiere deploy de Render y Vercel." -ForegroundColor Cyan
