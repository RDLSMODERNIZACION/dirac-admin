$ErrorActionPreference="Stop"

if (!(Test-Path ".\backend\app\routers\works_board.py")) {
  throw "Ejecutá este script desde la raíz de dirac-admin."
}

python ".\tools\aplicar_fix_works_board.py"

Write-Host ""
Write-Host "works-board corregido." -ForegroundColor Green
Write-Host "Solo requiere deploy de Render." -ForegroundColor Cyan
