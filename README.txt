FINANZAS > POR PAGAR SIMPLE

Reemplaza el formulario genérico de cuentas por pagar por un alta simple
similar al modal "Agregar costo" dentro de una obra.

Campos:
- Fecha
- Proveedor / contratista
- Rubro
- Concepto
- Cantidad
- Unidad
- Precio unitario
- Vencimiento
- Factura proveedor

Monto:
Cantidad x Precio unitario

Se guarda en la misma tabla payables.
No requiere backend ni SQL.

Aplicar:
.\APLICAR.ps1

Luego:
git diff
git add .
git commit -m "Simplificar alta de cuentas por pagar"
git push

Solo requiere Vercel.
