$ErrorActionPreference="Stop"
if (!(Test-Path ".\backend\app\routers\service_detail.py")) {
  throw "Ejecutá este script desde la raíz de dirac-admin."
}
python ".\tools\aplicar_eliminar_factura_servicio.py"
Write-Host "Listo. Revisá con git diff y git status." -ForegroundColor Green
