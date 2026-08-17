$ErrorActionPreference="Stop"

if (!(Test-Path ".\front\src\components\WorksBoard.tsx")) {
  throw "Ejecutá este script desde la raíz de dirac-admin."
}

python ".\tools\aplicar_orden_fecha_fin.py"

Write-Host ""
Write-Host "Orden predeterminado por Fecha fin aplicado." -ForegroundColor Green
Write-Host "Solo requiere deploy de Vercel." -ForegroundColor Cyan
