$ErrorActionPreference="Stop"
if (!(Test-Path ".\backend\app\routers\finance_payables.py")) {
  throw "Ejecutá desde la raíz de dirac-admin y asegurate de tener aplicado Por pagar completo."
}
Get-Process node -ErrorAction SilentlyContinue | Stop-Process -Force
python ".\tools\aplicar_sync_costos_obra.py"
Write-Host ""
Write-Host "Sincronización Finanzas -> Costos de Obra aplicada." -ForegroundColor Green
Write-Host "Requiere deploy de Render y Vercel." -ForegroundColor Cyan
