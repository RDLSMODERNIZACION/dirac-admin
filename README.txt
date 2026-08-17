ORDEN PREDETERMINADO: FECHA FIN

Cambios:
- Obras: el selector "Ordenar por" inicia en "Fecha fin".
- Servicios: el selector "Ordenar por" inicia en "Fecha fin".
- Trabajos > Todos: la lista queda ordenada por fecha fin ascendente.
- Los registros sin fecha fin quedan al final.
- En Trabajos > Todos se agrega la columna "Fecha fin".

No modifica backend ni datos.

Aplicar:
.\APLICAR.ps1

Luego:
git diff
git add .
git commit -m "Ordenar trabajos por fecha fin"
git push

Solo requiere Vercel.
