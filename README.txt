FIX STORAGE SERVICIOS

Bucket usado por Servicios:
administracion-servicios

Corrección:
- detecta NoSuchBucket aunque Supabase no responda 404 exacto
- crea automáticamente el bucket privado
- mantiene límite de 20 MB

Aplicar:
.\APLICAR.ps1

Luego:
git diff
git status
git add .
git commit -m "Corregir bucket de documentos de servicios"
git push

Solo requiere Render.
