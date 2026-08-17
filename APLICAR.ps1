$ErrorActionPreference="Stop"

if (!(Test-Path ".\front\app\globals.css")) {
  throw "Ejecutá este script desde la raíz de dirac-admin."
}

# Frenamos Next para evitar que tenga el archivo abierto mientras lo reemplazamos.
Get-Process node -ErrorAction SilentlyContinue | Stop-Process -Force

python ".\tools\aplicar_gantt_pro_fix.py"

Write-Host ""
Write-Host "Gantt Pro aplicado correctamente." -ForegroundColor Green
Write-Host "Ahora podés ejecutar: cd front ; npm run dev" -ForegroundColor Cyan
