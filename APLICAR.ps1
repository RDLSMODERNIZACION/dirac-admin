$ErrorActionPreference="Stop"
if (!(Test-Path ".\backend\app\routers\service_documents.py")) {
  throw "Ejecutá este script desde la raíz de dirac-admin."
}
python ".\tools\aplicar_fix_service_storage.py"
Write-Host ""
Write-Host "Storage de Servicios corregido." -ForegroundColor Green
Write-Host "Requiere deploy de Render." -ForegroundColor Cyan
