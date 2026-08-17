FIX ADMINISTRACION - FECHA FIN

Problema:
Obras actualizaba la fecha fin en su propio estado,
pero Administración conservaba una copia vieja en adminRows.

Solución:
al entrar a Administración se vuelve a ejecutar load()
y se consulta nuevamente /api/works-board.

Aplicar:
.\APLICAR.ps1

Luego:
git diff
git status
git add .
git commit -m "Refrescar administracion al cambiar de pestaña"
git push

Solo requiere Vercel.
