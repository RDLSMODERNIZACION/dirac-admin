$ErrorActionPreference="Stop"
if (!(Test-Path ".\front\src\components\WorkDetail.tsx")) {
  throw "Ejecutá este script desde la raíz de dirac-admin."
}
python ".\tools\aplicar_facturas_editar_menu.py"
Write-Host ""
Write-Host "Facturas editables + menu de tres puntos aplicado." -ForegroundColor Green
Write-Host "Requiere deploy de Render y Vercel." -ForegroundColor Cyan
