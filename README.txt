OBRAS - TODOS LOS IMPORTES IVA INCLUIDO

Nueva regla:
- Contrato: IVA incluido
- Ítems: IVA incluido
- Ejecutado: IVA incluido
- Facturado: IVA incluido
- Cobrado: IVA incluido
- Pendiente: IVA incluido

FACTURAS
El importe seleccionado desde los ítems ya es el TOTAL FINAL.
El sistema NO vuelve a sumar IVA.

Ejemplo:
Monto seleccionado: $12.100.000
IVA 21%

Neto incluido: $10.000.000
IVA incluido:  $2.100.000
Total factura: $12.100.000

IMPORTANTE
Los ítems existentes que fueron cargados como NETOS deben editarse una sola vez
y pasarse a precio final IVA incluido.

No requiere cambios de estructura SQL.

Aplicar:
1. Copiar tools/, backend/sql/ y APLICAR.ps1 a la raíz de dirac-admin.
2. Ejecutar:
   .\APLICAR.ps1
3. Revisar:
   git diff
   git status
4. Subir:
   git add .
   git commit -m "Unificar obras a importes IVA incluido"
   git push

Requiere deploy de Render y Vercel.
