$ErrorActionPreference="Stop"
if (!(Test-Path ".\front\src\components\ServicesBoard.tsx")) {
  throw "Ejecutá este script desde la raíz de dirac-admin."
}
python ".\tools\aplicar_menu_servicios.py"
Write-Host "Listo. Revisá con git diff y git status." -ForegroundColor Green
