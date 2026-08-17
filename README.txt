DIRAC ADMIN -> /admin

Aplicar desde:
C:\Users\victo\OneDrive\Escritorio\dirac-admin

.\APLICAR.ps1

Esto crea:
front/next.config.mjs

con:
basePath: "/admin"

Después:
git add .
git commit -m "Preparar admin para subruta admin"
git push

Vercel del admin volverá a desplegar.
Su URL directa pasará a ser:
https://TU-ADMIN.vercel.app/admin
