$ErrorActionPreference = "Stop"
if (!(Test-Path ".\front\src\components\Dashboard.tsx")) {
  throw "Ejecutá este script desde la raíz de dirac-admin."
}
python ".\tools\aplicar_dashboard_etiquetas.py"
Write-Host "Listo. Revisá con git diff." -ForegroundColor Green
