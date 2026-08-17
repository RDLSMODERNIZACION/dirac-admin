$ErrorActionPreference="Stop"
if (!(Test-Path ".\backend\app\routers\services_board.py")) {
  throw "Ejecutá este script desde la raíz de dirac-admin."
}
python ".\tools\aplicar_servicios_mes_vencido.py"
Write-Host "Listo. Revisá con git diff y git status." -ForegroundColor Green
