$ErrorActionPreference="Stop"
python ".\tools\aplicar_admin_basepath.py"
Write-Host ""
Write-Host "Admin preparado para /admin." -ForegroundColor Green
Write-Host "Luego hace falta configurar el rewrite en la web principal." -ForegroundColor Cyan
