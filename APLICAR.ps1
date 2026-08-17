$ErrorActionPreference="Stop"
if (!(Test-Path ".\front\src\components\WorkDetail.tsx")) {
  throw "Ejecutá este script desde la raíz de dirac-admin."
}
python ".\tools\aplicar_decimales_factura_obra.py"
Write-Host ""
Write-Host "Decimales de factura de obra corregidos." -ForegroundColor Green
Write-Host "Solo requiere deploy de Vercel." -ForegroundColor Cyan
