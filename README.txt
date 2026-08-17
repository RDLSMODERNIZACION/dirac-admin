FACTURAS EDITABLES

Obras y Servicios:
- menú ⋯ a la derecha
- Editar
- Eliminar
- Editar corrige datos administrativos sin cambiar importes.
- Eliminar conserva la regla de no permitir borrar si ya hay cobros.

Aplicar:
.\APLICAR.ps1

Luego:
git diff
git status
git add .
git commit -m "Permitir editar facturas de obras y servicios"
git push

Requiere Render + Vercel.
