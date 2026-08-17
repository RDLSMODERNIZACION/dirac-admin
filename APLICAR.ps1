$ErrorActionPreference="Stop"
if (!(Test-Path ".\front\src\components\ServicesBoard.tsx")) {
  throw "Ejecutá este script desde la raíz de dirac-admin."
}
python ".\tools\aplicar_servicios_sin_riesgo_acciones.py"
Write-Host "Listo. Revisá con git diff." -ForegroundColor Green
