FIX - SINCRONIZAR POR PAGAR CON COSTOS DE OBRA

Problema:
Finanzas > Por pagar guardaba en payables.
Obra > Costos lee work_costs.

Solución:
- Los costos nuevos con obra crean también work_costs.
- Quedan unidos por payable_id.
- Se guarda también work_item_id.
- Conserva cantidad, unidad y precio unitario.
- Al pagar, sincroniza payment_status de work_costs.
- WorkDetail devuelve el ítem asociado.

Importante:
Este fix sincroniza los costos NUEVOS.
Los viejos ya creados solo en payables no se migran automáticamente.

Aplicar:
.\APLICAR.ps1

Luego:
git add .
git commit -m "Sincronizar por pagar con costos de obra"
git push

Requiere Render + Vercel.
