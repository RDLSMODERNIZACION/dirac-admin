$ErrorActionPreference="Stop"
if (!(Test-Path ".\front\src\components\Planning.tsx")) {
  throw "Ejecutá este script desde la raíz de dirac-admin."
}
python ".\tools\aplicar_gantt_obra_fila_unica.py"
Write-Host ""
Write-Host "Gantt actualizado: obra en una fila, tareas compactas y Hoy continuo." -ForegroundColor Green
Write-Host "Solo requiere deploy de Vercel." -ForegroundColor Cyan
