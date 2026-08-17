$ErrorActionPreference="Stop"
if (!(Test-Path ".\front\src\components\WorksBoard.tsx")) { throw "Ejecutá esto desde la raíz de dirac-admin." }
python ".\tools\aplicar_botones_nuevo_trabajo.py"
Write-Host "Listo. Revisá con git diff y git status." -ForegroundColor Green
