$ErrorActionPreference = "Stop"
python ".\tools\aplicar_fix_deudas_proyeccion.py"
Write-Host "Listo. Revisá con git diff." -ForegroundColor Green
