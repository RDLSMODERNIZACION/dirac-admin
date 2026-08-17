$ErrorActionPreference="Stop"
if (!(Test-Path ".\backend\app\routers\planning.py")) {
  throw "Ejecutá este script desde la raíz de dirac-admin."
}

Get-Process node -ErrorAction SilentlyContinue | Stop-Process -Force

python ".\tools\aplicar_planificacion_pro.py"

Write-Host ""
Write-Host "Planificación Pro aplicada." -ForegroundColor Green
Write-Host "Backend: nuevas dependencias, hitos y reprogramación." -ForegroundColor Cyan
Write-Host "Frontend: Gantt interactivo, Calendario, Tareas y panel lateral." -ForegroundColor Cyan
