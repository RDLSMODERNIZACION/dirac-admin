$ErrorActionPreference="Stop"
if (!(Test-Path ".\front\src\components\WorkDetail.tsx")) {
  throw "Ejecutá este script desde la raíz de dirac-admin."
}
python ".\tools\aplicar_facturas_menu_editar_completo.py"
Write-Host ""
Write-Host "Facturas: menu, editar y eliminar aplicado." -ForegroundColor Green
Write-Host "Requiere Render + Vercel." -ForegroundColor Cyan
