$ErrorActionPreference="Stop"
if (!(Test-Path ".\front\src\components\Planning.tsx")) {
  throw "Ejecutá este script desde la raíz de dirac-admin."
}
python ".\tools\aplicar_sugerencia_hito.py"
Write-Host ""
Write-Host "Sugerencia automatica de hito aplicada." -ForegroundColor Green
Write-Host "Solo requiere deploy de Vercel." -ForegroundColor Cyan
