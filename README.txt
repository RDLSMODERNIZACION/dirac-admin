FINANZAS > POR PAGAR COMPLETO

Agrega al alta simple:
- Obra opcional
- Ítem de obra opcional
- Al elegir obra, solo aparecen sus ítems
- El vínculo queda guardado en payables.work_item_id

Agrega flujo de pago:
- Botón Pagar
- Elegir cuenta
- Monto total o parcial
- Fecha
- Notas
- Crea movimiento financiero tipo EGRESO
- Se debita automáticamente de la cuenta porque el saldo se calcula desde movimientos
- Estado de payable: pendiente / parcial / pagado

Después del pago:
- Si está asociado a una obra, abre modal para subir comprobante PDF
- El comprobante queda como work_document
- related_type = financial_movement
- related_id = movimiento del pago

No requiere SQL manual:
el backend agrega payables.work_item_id automáticamente.

Aplicar:
.\APLICAR.ps1

Luego:
git diff
git status
git add .
git commit -m "Completar por pagar con obra item y pagos"
git push

Requiere Render + Vercel.
