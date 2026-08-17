$ErrorActionPreference="Stop"
if (!(Test-Path ".\front\src\components\Planning.tsx")) { throw "Ejecutá desde la raíz de dirac-admin." }
python ".\tools\aplicar_plazo_obras_gantt.py"
Write-Host ""
Write-Host "Plazos de obra agregados al cronograma." -ForegroundColor Green
Write-Host "Solo requiere Vercel." -ForegroundColor Cyan
