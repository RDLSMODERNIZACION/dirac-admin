GANTT - COLUMNA OBRA/TAREA FIJA

Hace sticky la columna izquierda del cronograma.

Al desplazar horizontalmente:
- Obra / tarea queda visible.
- Las filas de obra quedan visibles.
- Las filas de tarea quedan visibles.
- Solo se desplaza la parte de calendario.

Aplicar desde la raíz de dirac-admin:
.\APLICAR.ps1

Luego:
git diff
git status
git add .
git commit -m "Fijar columna obra tarea en cronograma"
git push

Solo requiere Vercel.
