$ErrorActionPreference="Stop"
if (!(Test-Path ".\backend\app\routers\service_detail.py")) {
  throw "Ejecutá este script desde la raíz de dirac-admin."
}
python ".\tools\aplicar_servicios_iva_incluido.py"
Write-Host "Listo. Revisá con git diff y git status." -ForegroundColor Green
