$ErrorActionPreference="Stop"

if (!(Test-Path ".\backend\app\routers\planning.py")) {
  throw "Ejecutá este script desde la raíz de dirac-admin."
}

python ".\tools\aplicar_fix_planning.py"

Write-Host ""
Write-Host "Fix aplicado." -ForegroundColor Green
Write-Host "Ahora subí los cambios para que Render redeploye el backend." -ForegroundColor Cyan
