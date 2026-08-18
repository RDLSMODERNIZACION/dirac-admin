$ErrorActionPreference="Stop"
if (!(Test-Path ".\front\app\globals.css")) {
  throw "Ejecutá este script desde la raíz de dirac-admin."
}
python ".\tools\aplicar_gantt_sticky.py"
if ($LASTEXITCODE -ne 0) { throw "No se pudo aplicar el cambio." }
Write-Host ""
Write-Host "Columna Obra / tarea fijada en el Gantt." -ForegroundColor Green
Write-Host "Solo requiere deploy de Vercel." -ForegroundColor Cyan
