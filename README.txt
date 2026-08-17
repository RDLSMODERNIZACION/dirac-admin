FIX PLANNING - FAILED TO FETCH / CORS APARENTE

Problema:
GET /api/planning/tasks generaba un error interno en el backend.
El navegador lo mostraba como CORS porque Render devolvía la respuesta 500
sin Access-Control-Allow-Origin.

Causa:
Se intentaba ejecutar .format() sobre un psycopg.sql.Composed.

Solución:
Se formatea task_select_sql() ANTES de concatenar el ORDER BY.

Aplicar desde la raíz:
.\APLICAR.ps1

Luego:
git diff
git add .
git commit -m "Fix planning tasks query"
git push

IMPORTANTE:
Este cambio requiere redeploy del BACKEND en Render.
No hace falta SQL.
