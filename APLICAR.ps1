$ErrorActionPreference="Stop"

if (!(Test-Path ".\front\src\components\ClientAnalytics.tsx")) {
  throw "Ejecutá este script desde la raíz de dirac-admin."
}

python ".\tools\aplicar_clientes_limpio.py"

Write-Host ""
Write-Host "Clientes simplificado correctamente." -ForegroundColor Green
Write-Host "Solo requiere deploy de Vercel." -ForegroundColor Cyan
