from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

p = ROOT / "backend/app/routers/service_detail.py"
t = p.read_text(encoding="utf-8")
old = '        net_amount = _money(period["amount"])\n        vat_amount = (net_amount * body.vat_rate / Decimal("100")).quantize(Decimal("0.01"))\n        invoice_total = net_amount + vat_amount\n'
new = '        # El monto del período YA incluye IVA.\n        invoice_total = _money(period["amount"]).quantize(Decimal("0.01"))\n\n        divisor = Decimal("1") + (body.vat_rate / Decimal("100"))\n        net_amount = (\n            (invoice_total / divisor).quantize(Decimal("0.01"))\n            if divisor > 0\n            else invoice_total\n        )\n        vat_amount = invoice_total - net_amount\n'
if old not in t:
    raise SystemExit("ERROR: no encontré el cálculo de IVA en service_detail.py")
t = t.replace(old, new, 1)
p.write_text(t, encoding="utf-8")

p = ROOT / "front/src/components/ServiceDetail.tsx"
t = p.read_text(encoding="utf-8")

old = 'function InvoiceModal({row,form,setForm,saving,close,submit}:any){const net=Number(row.amount||0);const vat=net*Number(form.vat_rate||0)/100;const total=net+vat;'
new = 'function InvoiceModal({row,form,setForm,saving,close,submit}:any){const total=Number(row.amount||0);const vatRate=Number(form.vat_rate||0);const divisor=1+(vatRate/100);const net=divisor>0?total/divisor:total;const vat=total-net;'
if old not in t:
    raise SystemExit("ERROR: no encontré InvoiceModal en ServiceDetail.tsx")
t = t.replace(old, new, 1)

t = t.replace(
    "El monto del período es neto. El IVA se suma al total a cobrar.",
    "El monto del período ya incluye IVA. El sistema muestra la composición neto + IVA sin modificar el total."
)

t = t.replace(
    'subtitle="El monto del servicio es neto. Al facturar se agrega el IVA y el total con IVA pasa a Por cobrar."',
    'subtitle="El monto mensual ya incluye IVA. Al facturar se descompone en neto e IVA sin modificar el total."'
)

t = t.replace("<th>Neto</th>", "<th>Monto período</th>")

old = "<div>Neto: <b>{money(net)}</b></div><div>IVA {Number(form.vat_rate||0).toLocaleString('es-AR')}%: <b>{money(vat)}</b></div><div style={{fontSize:18}}>TOTAL FACTURA: <b>{money(total)}</b></div>"
new = "<div>Neto incluido: <b>{money(net)}</b></div><div>IVA incluido {vatRate.toLocaleString('es-AR')}%: <b>{money(vat)}</b></div><div style={{fontSize:18}}>TOTAL FACTURA: <b>{money(total)}</b></div>"
if old not in t:
    raise SystemExit("ERROR: no encontré el resumen Neto/IVA/Total")
t = t.replace(old, new, 1)

p.write_text(t, encoding="utf-8")

print("OK: Servicios ahora usa importes IVA incluido igual que Obras.")
