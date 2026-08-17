$ErrorActionPreference="Stop"

if (!(Test-Path ".\front\src\components\Modules.tsx")) {
  throw "Ejecutá este script desde la raíz de dirac-admin."
}

python ".\tools\aplicar_finanzas_por_pagar_simple.py"

Write-Host ""
Write-Host "Por pagar simplificado correctamente." -ForegroundColor Green
Write-Host "Solo requiere deploy de Vercel." -ForegroundColor Cyan
