$ErrorActionPreference="Stop"

if (!(Test-Path ".\front\src\components\Sidebar.tsx")) {
  throw "Ejecutá este script desde la raíz de dirac-admin."
}

python ".\tools\aplicar_sacar_compras.py"

Write-Host ""
Write-Host "Compras eliminado del menú." -ForegroundColor Green
Write-Host "No se borraron datos ni tablas." -ForegroundColor Cyan
