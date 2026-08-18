$ErrorActionPreference="Stop"
if (!(Test-Path ".\backend\app\main.py") -or !(Test-Path ".\front\app\page.tsx")) {
  throw "Ejecutá este script desde la raíz de dirac-admin."
}
python ".\tools\aplicar_login.py"
if ($LASTEXITCODE -ne 0) { throw "No se pudo aplicar el login." }
Write-Host ""
Write-Host "Login agregado." -ForegroundColor Green
Write-Host "Usuarios: victor / luciano" -ForegroundColor Cyan
Write-Host "Contraseña: admin" -ForegroundColor Cyan
Write-Host "Requiere deploy de Render y Vercel." -ForegroundColor Yellow
