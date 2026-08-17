from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

p = ROOT / "backend/app/routers/work_detail.py"
t = p.read_text(encoding="utf-8")

pairs = [
    ('        if body.vat_rate < 0 or body.vat_rate > 100:\n            raise HTTPException(400, "La alícuota de IVA no es válida")\n        vat_amount = (total * body.vat_rate / Decimal("100")).quantize(Decimal("0.01"))\n        invoice_total = total + vat_amount\n', '        if body.vat_rate < 0 or body.vat_rate > 100:\n            raise HTTPException(400, "La alícuota de IVA no es válida")\n\n        # Los importes de los ítems de obra YA incluyen IVA.\n        # El monto seleccionado es el TOTAL FINAL de la factura.\n        invoice_total = total.quantize(Decimal("0.01"))\n        divisor = Decimal("1") + (body.vat_rate / Decimal("100"))\n        net_amount = (\n            (invoice_total / divisor).quantize(Decimal("0.01"))\n            if divisor > 0\n            else invoice_total\n        )\n        vat_amount = invoice_total - net_amount\n'),
    ('        invoice["net_amount"] = total\n        invoice["vat_rate"] = body.vat_rate\n        invoice["vat_amount"] = vat_amount\n        invoice["total_amount"] = invoice_total', '        invoice["net_amount"] = net_amount\n        invoice["vat_rate"] = body.vat_rate\n        invoice["vat_amount"] = vat_amount\n        invoice["total_amount"] = invoice_total'),
]
for old,new in pairs:
    if old not in t:
        raise SystemExit("ERROR: no encontré un bloque esperado en work_detail.py")
    t = t.replace(old,new,1)
p.write_text(t, encoding="utf-8")

p = ROOT / "front/src/components/WorkDetail.tsx"
t = p.read_text(encoding="utf-8")

t = t.replace("['unit_price','Precio unitario','number']",
              "['unit_price','Precio unitario (IVA incluido)','number']")
t = t.replace("Valor total de ítems activos:",
              "Valor total de ítems activos (IVA incluido):")

old = ' const netTotal=eligible.reduce((a:number,x:any)=>a+selectedAmount(x),0);\n const advanceTotal=eligible.reduce((a:number,x:any)=>a+advanceFor(x),0);\n const vatRate=Number(head.vat_rate||0);\n const vatAmount=netTotal*vatRate/100;\n const invoiceTotal=netTotal+vatAmount;'
new = ' const invoiceTotal=eligible.reduce((a:number,x:any)=>a+selectedAmount(x),0);\n const advanceTotal=eligible.reduce((a:number,x:any)=>a+advanceFor(x),0);\n const vatRate=Number(head.vat_rate||0);\n const divisor=1+(vatRate/100);\n const netTotal=divisor>0?invoiceTotal/divisor:invoiceTotal;\n const vatAmount=invoiceTotal-netTotal;'
if old not in t:
    raise SystemExit("ERROR: no encontré los cálculos del modal de factura")
t = t.replace(old,new,1)

t = t.replace("<span>Neto a facturar</span><strong>{money(netTotal)}</strong>",
              "<span>Neto incluido</span><strong>{money(netTotal)}</strong>")
t = t.replace("<span>IVA {vatRate}%</span><strong>{money(vatAmount)}</strong>",
              "<span>IVA incluido {vatRate}%</span><strong>{money(vatAmount)}</strong>")
t = t.replace("<span>Total factura</span><strong>{money(invoiceTotal)}</strong>",
              "<span>Total factura (IVA incluido)</span><strong>{money(invoiceTotal)}</strong>")
t = t.replace("La facturación puede adelantarse a la ejecución. El anticipo se muestra separado para control.",
              "Los importes de los ítems ya incluyen IVA. La facturación puede adelantarse a la ejecución y el anticipo se muestra separado.")
t = t.replace("<span>Valor contractual</span>",
              "<span>Valor contractual IVA incl.</span>")

p.write_text(t, encoding="utf-8")

print("OK: Obras unificadas a importes IVA incluido.")
