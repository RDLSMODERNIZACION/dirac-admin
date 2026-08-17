$ErrorActionPreference="Stop"
if (!(Test-Path ".\backend\app\routers\documents.py")) {
  throw "Ejecutá este script desde la raíz de dirac-admin."
}
python ".\tools\aplicar_storage_auto_bucket_v2.py"
Write-Host ""
Write-Host "Storage auto-bucket aplicado correctamente." -ForegroundColor Green
Write-Host "Requiere deploy de Render." -ForegroundColor Cyan
