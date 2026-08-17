FIX VERCEL - PLANNING TYPESCRIPT

Error:
Parameter 'r' implicitly has an 'any' type.

Corrige:
onEdit={r=>...}

por:
onEdit={(r:any)=>...}

Aplicar:
.\APLICAR.ps1

Luego:
git diff
git status
git add .
git commit -m "Corregir tipo en Planning"
git push

Solo requiere Vercel.
