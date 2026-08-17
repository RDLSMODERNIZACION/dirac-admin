from pathlib import Path

p = Path.cwd() / "front/src/components/WorkDetail.tsx"
t = p.read_text(encoding="utf-8")

# Helper: acepta coma o punto como separador decimal.
helper = """function parseInvoiceAmount(v:any){
 const s=String(v??'').trim();
 if(!s)return 0;
 if(s.includes(',')&&s.includes('.'))return Number(s.replace(/\\./g,'').replace(',','.'));
 if(s.includes(','))return Number(s.replace(',','.'));
 return Number(s);
}

"""

anchor = "function Invoices({workId,invoices,documents,reload}"
if "function parseInvoiceAmount(" not in t:
    idx = t.find(anchor)
    if idx < 0:
        raise SystemExit("ERROR: no encontré el bloque de facturación de obra")
    t = t[:idx] + helper + t[idx:]

# Tanto Nueva factura como Editar deben usar el parser flexible.
count_total = t.count("const total=Number(f.amount||0);")
if count_total == 0:
    raise SystemExit("ERROR: no encontré el cálculo del monto de factura")
t = t.replace("const total=Number(f.amount||0);", "const total=parseInvoiceAmount(f.amount);")

# Cambiar inputs number por text + teclado decimal.
old = '<input type="number" min="0.01" step="0.01" value={f.amount} onChange={e=>setF({...f,amount:e.target.value})}/>'
new = '<input type="text" inputMode="decimal" placeholder="Ej: 26534914,20" value={f.amount} onChange={e=>setF({...f,amount:e.target.value})}/>'
count_inputs = t.count(old)
if count_inputs == 0:
    raise SystemExit("ERROR: no encontré el campo Monto total")
t = t.replace(old, new)

p.write_text(t, encoding="utf-8")
print(f"OK: decimales habilitados en {count_inputs} campo(s) de monto de factura.")
