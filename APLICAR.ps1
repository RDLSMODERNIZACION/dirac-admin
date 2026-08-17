$ErrorActionPreference="Stop"
if (!(Test-Path ".\front\src\components\Jobs.tsx")) {
  throw "Ejecutá este script desde la raíz de dirac-admin."
}
python ".\tools\aplicar_fix_admin_refresh.py"
Write-Host ""
Write-Host "Administracion ahora refresca al entrar." -ForegroundColor Green
Write-Host "Solo requiere deploy de Vercel." -ForegroundColor Cyan
