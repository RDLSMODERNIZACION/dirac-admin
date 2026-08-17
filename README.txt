FIX VERCEL - RESOURCEMANAGER

Error:
Expected 2 arguments, but got 1.

Corrige:
api.post<any>(`/api/works/${r.id}/generate-receivables`)

por:
api.post<any>(`/api/works/${r.id}/generate-receivables`, {})

Aplicar:
.\APLICAR.ps1

Luego:
git diff
git status
git add .
git commit -m "Corregir api post en ResourceManager"
git push

Solo requiere Vercel.
