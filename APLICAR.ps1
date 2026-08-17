$ErrorActionPreference="Stop"
if (!(Test-Path ".\front\src\components\Jobs.tsx")) {
  throw "Ejecutá este script desde la raíz de dirac-admin."
}
python ".\tools\aplicar_administracion_obras.py"
Write-Host ""
Write-Host "Administracion de obras aplicada." -ForegroundColor Green
Write-Host "Requiere deploy de Render y Vercel." -ForegroundColor Cyan
