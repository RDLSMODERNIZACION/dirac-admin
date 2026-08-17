$ErrorActionPreference="Stop"
if (!(Test-Path ".\front\src\components\Planning.tsx")) {
  throw "Ejecutá este script desde la raíz de dirac-admin."
}
python ".\tools\aplicar_fix_vercel_planning.py"
Write-Host ""
Write-Host "Fix TypeScript de Planning aplicado." -ForegroundColor Green
Write-Host "Solo requiere nuevo deploy de Vercel." -ForegroundColor Cyan
