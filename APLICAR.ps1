$ErrorActionPreference="Stop"
if (!(Test-Path ".\front\src\components\Planning.tsx")) {
  throw "Ejecutá este script desde la raíz de dirac-admin."
}
python ".\tools\aplicar_gantt_legible.py"
Write-Host ""
Write-Host "Cronograma legible actualizado." -ForegroundColor Green
Write-Host "Solo requiere deploy de Vercel." -ForegroundColor Cyan
