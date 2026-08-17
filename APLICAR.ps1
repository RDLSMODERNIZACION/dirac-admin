$ErrorActionPreference="Stop"
if (!(Test-Path ".\front\src\components\Planning.tsx")) {
  throw "Ejecutá este script desde la raíz de dirac-admin."
}
python ".\tools\aplicar_todas_obras_gantt.py"
Write-Host ""
Write-Host "Cronograma actualizado para mostrar todas las obras." -ForegroundColor Green
Write-Host "Solo requiere deploy de Vercel." -ForegroundColor Cyan
