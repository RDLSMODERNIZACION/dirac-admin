FIX WORKS-BOARD CHECKLIST

Corrige:
IndexError: tuple index out of range
en backend/app/routers/works_board.py

Causa:
psycopg SQL.format interpretaba '{}'::jsonb como placeholders.

Solución:
- reemplaza '{}'::jsonb por jsonb_build_object()
- vuelve a 11 identificadores S en .format(...)

Aplicar:
.\APLICAR.ps1

Luego:
git diff
git status
git add .
git commit -m "Corregir works board checklist"
git push

Solo requiere deploy de Render.
