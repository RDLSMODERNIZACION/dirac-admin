SACAR COMPRAS DEL SIDEBAR

Cambios:
- Elimina Compras del menú lateral.
- Elimina Compras de la navegación principal.
- No borra tablas.
- No borra compras existentes.
- No modifica backend.
- Finanzas queda como módulo principal para pagos y obligaciones.

Aplicar:
.\APLICAR.ps1

Luego:
git diff
git add .
git commit -m "Sacar compras del sidebar"
git push

Solo requiere deploy de Vercel.
