$ErrorActionPreference="Stop"
if (!(Test-Path ".\backend\app\main.py")) {
  throw "Ejecutá este script desde la raíz de dirac-admin."
}
python ".\tools\aplicar_cuadro_servicios.py"
Write-Host "Listo. Revisá con git diff y git status." -ForegroundColor Green
