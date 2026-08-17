$ErrorActionPreference="Stop"
if (!(Test-Path ".\backend\app\routers\work_detail.py")) {
  throw "Ejecutá este script desde la raíz de dirac-admin."
}
python ".\tools\aplicar_factura_obra_monto_libre.py"
Write-Host ""
Write-Host "Facturacion de obra independiente de items aplicada." -ForegroundColor Green
Write-Host "Requiere deploy de Render y Vercel." -ForegroundColor Cyan
