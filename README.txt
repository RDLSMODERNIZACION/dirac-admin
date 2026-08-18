LOGIN DIRAC ADMIN

Usuarios:
- victor
- luciano

Contraseña:
admin

La validación se hace en el backend, no solo en el frontend.
Todas las rutas /api/* requieren una sesión válida excepto /api/auth/*.

La sesión se guarda en el navegador.
Si Render reinicia el backend, hay que iniciar sesión de nuevo.

Aplicar desde:
C:\Users\victo\OneDrive\Escritorio\dirac-admin

.\APLICAR.ps1

Luego:
git diff
git status
git add .
git commit -m "Agregar login al admin"
git push

Toca frontend y backend:
- Render debe redeployar
- Vercel debe redeployar
