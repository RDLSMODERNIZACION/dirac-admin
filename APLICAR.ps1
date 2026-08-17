$ErrorActionPreference="Stop"
if (!(Test-Path ".\front\src\components\FinancePayables.tsx")) {
  throw "Primero aplicá el módulo Por pagar simple, o ejecutá esto desde un repo que ya tenga FinancePayables.tsx."
}
Get-Process node -ErrorAction SilentlyContinue | Stop-Process -Force
python ".\tools\aplicar_por_pagar_completo.py"
Write-Host ""
Write-Host "Por pagar completo aplicado." -ForegroundColor Green
Write-Host "Requiere deploy de Render y Vercel." -ForegroundColor Cyan
