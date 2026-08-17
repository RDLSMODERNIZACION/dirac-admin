FIX STORAGE AUTO BUCKET V2

Corrige el parche anterior.
Verifica el bucket administracion-obras y lo crea automáticamente si no existe.

Aplicar desde la raíz:
.\APLICAR.ps1

Luego:
git diff
git status
git add .
git commit -m "Corregir auto creacion bucket storage"
git push

Solo requiere Render.
