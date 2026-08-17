FACTURA DE OBRA POR MONTO DIRECTO

Nueva lógica:
- La factura NO se vincula a ítems.
- Se ingresa directamente:
  número
  concepto
  emisión
  vencimiento
  monto total IVA incluido
  IVA
  notas
- Los ítems quedan solo para ejecución y avance.
- Facturado = suma de facturas.
- Disponible a facturar = contrato - facturado.
- Ejecutado no facturado y facturación anticipada comparan ejecución vs facturación total.
- Las facturas históricas por ítems se conservan.

Aplicar desde la raíz:
.\APLICAR.ps1

Luego:
git diff
git status
git add .
git commit -m "Desacoplar facturacion de obra de los items"
git push

Requiere Render + Vercel.
