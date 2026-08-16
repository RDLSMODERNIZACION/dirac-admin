$ErrorActionPreference = "Stop"
if (!(Test-Path ".\backend\app\routers\work_detail.py")) {
  throw "Ejecutá este script desde la raíz de dirac-admin."
}
python ".\tools\aplicar_checklist_obras.py"
Write-Host "Listo. Revisá con git diff y git status." -ForegroundColor Green
