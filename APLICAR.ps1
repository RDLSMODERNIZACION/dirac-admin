$ErrorActionPreference="Stop"
if (!(Test-Path ".\front\src\components\ResourceManager.tsx")) {
  throw "Ejecutá este script desde la raíz de dirac-admin."
}
python ".\tools\aplicar_fix_resourcemanager_post.py"
Write-Host ""
Write-Host "Fix ResourceManager aplicado." -ForegroundColor Green
Write-Host "Solo requiere nuevo deploy de Vercel." -ForegroundColor Cyan
