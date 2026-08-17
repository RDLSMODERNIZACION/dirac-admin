$ErrorActionPreference="Stop"
if (!(Test-Path ".\backend\app\routers\debts.py")) { throw "Ejecutá esto desde la raíz de dirac-admin." }
python ".\tools\aplicar_editar_deudas.py"
Write-Host "Listo. Revisá con git diff y git status." -ForegroundColor Green
