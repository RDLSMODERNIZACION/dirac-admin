$ErrorActionPreference="Stop"
if (!(Test-Path ".\front\src\components\WorksBoard.tsx")) {
  throw "Ejecutá este script desde la raíz de dirac-admin."
}
python ".\tools\aplicar_obras_ancho_completo.py"
Write-Host "Listo. Revisá con git diff." -ForegroundColor Green
