FACTURAS - MENU + EDITAR + ELIMINAR

OBRAS
- mantiene factura independiente de items
- botón ⋯ a la derecha
- Editar
- Eliminar
- Editar permite cambiar:
  número
  concepto
  emisión
  vencimiento
  monto total
  IVA visual
  notas
- si ya hay cobros, no permite bajar el monto por debajo de lo cobrado

SERVICIOS
- botón ⋯
- Editar
- Eliminar
- mantiene monto fijo del período

Aplicar desde raíz:
.\APLICAR.ps1

Luego:
git diff
git status
git add .
git commit -m "Agregar edicion y menu de facturas"
git push

Requiere Render + Vercel.
