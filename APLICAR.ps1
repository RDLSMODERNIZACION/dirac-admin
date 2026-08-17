$ErrorActionPreference="Stop"
if (!(Test-Path ".\front\src\components\WorkDetail.tsx")) {
  throw "Ejecutá este script desde la raíz de dirac-admin."
}
python ".\tools\aplicar_checklist_simplificado.py"
Write-Host "Listo. Revisá con git diff y git status." -ForegroundColor Green
