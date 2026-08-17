$ErrorActionPreference="Stop"
if (!(Test-Path ".\backend\app\routers\dashboard.py")) {
  throw "Ejecutá este script desde la raíz de dirac-admin."
}
python ".\tools\aplicar_fix_cobros_huerfanos.py"
Write-Host "Listo. Subí los cambios y esperá el deploy de Render." -ForegroundColor Green
