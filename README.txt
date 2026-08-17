FACTURACION ANTICIPADA EN OBRAS

- Ejecución física, facturación y cobro quedan independientes.
- Cualquier ítem no cancelado puede facturarse aunque todavía no esté ejecutado.
- Tope: valor contractual del ítem menos lo ya facturado.
- El modal muestra cuánto queda como facturación anticipada respecto de ejecución.
- IVA sigue separado; Por cobrar se crea por el total con IVA.
- El Resumen agrega:
  * Ejecutado no facturado
  * Facturación anticipada
  * Cobro adelantado vs ejecución

No requiere SQL.

Aplicar:
1. Copiar tools/ y APLICAR.ps1 a la raíz de dirac-admin.
2. Ejecutar: .\APLICAR.ps1
3. Revisar: git diff ; git status
4. Subir: git add . ; git commit -m "Habilitar facturacion anticipada en obras" ; git push
