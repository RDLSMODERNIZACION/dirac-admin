from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
# If copied into repo root/tools, ROOT is repo root. If run from extracted patch/tools, use cwd.
repo = Path.cwd()
if not (repo / 'backend').exists() or not (repo / 'front').exists():
    repo = ROOT

files = {
    'work_backend': repo / 'backend/app/routers/work_detail.py',
    'service_backend': repo / 'backend/app/routers/service_detail.py',
    'work_front': repo / 'front/src/components/WorkDetail.tsx',
    'service_front': repo / 'front/src/components/ServiceDetail.tsx',
}
for name,p in files.items():
    if not p.exists():
        raise SystemExit(f'No encontré {p}. Ejecutá este script desde la raíz del repo dirac-admin.')

def write(p, text):
    p.write_text(text, encoding='utf-8')
    print('OK:', p.relative_to(repo))

# ---------- backend obra ----------
p = files['work_backend']; s = p.read_text(encoding='utf-8')
if 'vat_rate: Decimal = Decimal("21")' not in s:
    s = s.replace(
'''class InvoiceCreate(BaseModel):\n    description: str | None = None\n    document_number: str | None = None\n    issue_date: date = date.today()\n    due_date: date | None = None\n    notes: str | None = None\n    items: list[InvoiceItemCreate]''',
'''class InvoiceCreate(BaseModel):\n    description: str | None = None\n    document_number: str | None = None\n    issue_date: date = date.today()\n    due_date: date | None = None\n    notes: str | None = None\n    vat_rate: Decimal = Decimal("21")\n    items: list[InvoiceItemCreate]''')

marker = '''            validated.append((item, req.amount, executed))\n            total += req.amount\n\n        cur.execute(sql.SQL("""'''
if marker in s and 'invoice_total = total + vat_amount' not in s:
    s = s.replace(marker, '''            validated.append((item, req.amount, executed))\n            total += req.amount\n\n        if body.vat_rate < 0 or body.vat_rate > 100:\n            raise HTTPException(400, "La alícuota de IVA no es válida")\n        vat_amount = (total * body.vat_rate / Decimal("100")).quantize(Decimal("0.01"))\n        invoice_total = total + vat_amount\n\n        cur.execute(sql.SQL("""''')

# Replace only create invoice block usages: total -> invoice_total in invoice header + receivable.
s = s.replace('body.description, body.issue_date, body.due_date, total, body.notes])\n        invoice = cur.fetchone()',
              'body.description, body.issue_date, body.due_date, invoice_total, body.notes])\n        invoice = cur.fetchone()')
s = s.replace('body.issue_date, body.due_date, total, body.notes])\n        receivable_id = cur.fetchone()["id"]',
              'body.issue_date, body.due_date, invoice_total, body.notes])\n        receivable_id = cur.fetchone()["id"]')
s = s.replace('invoice["total_amount"] = total\n        return invoice',
              'invoice["net_amount"] = total\n        invoice["vat_rate"] = body.vat_rate\n        invoice["vat_amount"] = vat_amount\n        invoice["total_amount"] = invoice_total\n        return invoice')
write(p,s)

# ---------- backend servicio ----------
p = files['service_backend']; s = p.read_text(encoding='utf-8')
# add gross invoice amount to period result
if 'r.amount AS invoice_total_amount' not in s:
    s = s.replace('r.issue_date,\n                   r.status AS receivable_status,',
                  'r.issue_date,\n                   r.amount AS invoice_total_amount,\n                   r.status AS receivable_status,')
# metrics gross billed, net pending invoice
old = '''        invoiced = sum((_money(p["amount"]) for p in periods if p.get("receivable_id")), Decimal("0"))\n        collected = sum((_money(p.get("paid_amount")) for p in periods), Decimal("0"))\n        contract = _money(service.get("contract_amount"))'''
new = '''        invoiced_net = sum((_money(p["amount"]) for p in periods if p.get("receivable_id")), Decimal("0"))\n        invoiced = sum((_money(p.get("invoice_total_amount") or p["amount"]) for p in periods if p.get("receivable_id")), Decimal("0"))\n        collected = sum((_money(p.get("paid_amount")) for p in periods), Decimal("0"))\n        contract = _money(service.get("contract_amount"))'''
s = s.replace(old,new)
s = s.replace('"pending_invoice": max(Decimal("0"), contract - invoiced),',
              '"pending_invoice": max(Decimal("0"), contract - invoiced_net),')
# request field
if 'vat_rate: Decimal = Decimal("21")' not in s:
    s = s.replace('''class PeriodInvoiceCreate(BaseModel):\n    document_number: str\n    issue_date: date = date.today()\n    due_date: date | None = None\n    notes: str | None = None''',
                  '''class PeriodInvoiceCreate(BaseModel):\n    document_number: str\n    issue_date: date = date.today()\n    due_date: date | None = None\n    notes: str | None = None\n    vat_rate: Decimal = Decimal("21")''')
# invoice computation before insert
marker = '''        description = f"{period['service_name']} - período {period['period_number']} ({period['period_start']} a {period['period_end']})"\n        due = body.due_date or period.get("due_date")\n        cur.execute(sql.SQL("""'''
if marker in s and 'invoice_total = net_amount + vat_amount' not in s:
    s = s.replace(marker, '''        description = f"{period['service_name']} - período {period['period_number']} ({period['period_start']} a {period['period_end']})"\n        due = body.due_date or period.get("due_date")\n        if body.vat_rate < 0 or body.vat_rate > 100:\n            raise HTTPException(400, "La alícuota de IVA no es válida")\n        net_amount = _money(period["amount"])\n        vat_amount = (net_amount * body.vat_rate / Decimal("100")).quantize(Decimal("0.01"))\n        invoice_total = net_amount + vat_amount\n        cur.execute(sql.SQL("""''')
s = s.replace('body.issue_date, due, period["amount"], body.notes])',
              'body.issue_date, due, invoice_total, body.notes])')
write(p,s)

# ---------- frontend obra: replace InvoiceByItemsModal only ----------
p = files['work_front']; s = p.read_text(encoding='utf-8')
start = s.find('function InvoiceByItemsModal(')
end = s.find('\nfunction Documents(', start)
if start < 0 or end < 0:
    raise SystemExit('No pude localizar InvoiceByItemsModal en WorkDetail.tsx')
new_func = r'''function InvoiceByItemsModal({items,onClose,onSave}:{items:any[];onClose:()=>void;onSave:(x:any)=>Promise<void>}){
 const eligible=items.filter((x:any)=>x.status!=='cancelado'&&Number(x.available_to_invoice||0)>0);
 const [head,setHead]=useState<any>({document_number:'',description:'',issue_date:new Date().toISOString().slice(0,10),due_date:'',notes:'',vat_rate:21});
 const [selected,setSelected]=useState<Record<string,boolean>>({});const [amounts,setAmounts]=useState<Record<string,number>>({});const [saving,setSaving]=useState(false);
 const net=eligible.reduce((a:number,x:any)=>a+(selected[x.id]?Number(amounts[x.id]||0):0),0);
 const vat=net*Number(head.vat_rate||0)/100; const total=net+vat;
 const toggle=(x:any,v:boolean)=>{setSelected(o=>({...o,[x.id]:v}));if(v&&amounts[x.id]===undefined)setAmounts(o=>({...o,[x.id]:Number(x.available_to_invoice||0)}))};
 const submit=async(e:any)=>{e.preventDefault();const lines=eligible.filter(x=>selected[x.id]).map(x=>({work_item_id:x.id,amount:Number(amounts[x.id]||0)})).filter(x=>x.amount>0);if(!lines.length){alert('Seleccioná al menos un ítem con monto mayor que cero');return}for(const x of eligible){if(selected[x.id]&&Number(amounts[x.id]||0)>Number(x.available_to_invoice||0)+0.01){alert(`${x.code}: el monto supera lo disponible para facturar`);return}}setSaving(true);try{await onSave({...head,vat_rate:Number(head.vat_rate||0),due_date:head.due_date||null,items:lines})}catch(x:any){alert(x.message)}finally{setSaving(false)}};
 return <div className="modal-backdrop"><div className="modal invoice-modal"><div className="modal-head"><div><h2>Nueva factura por avance</h2><p>Los importes de los ítems son netos. El IVA se agrega al total de la factura y a la cuenta por cobrar.</p></div><button className="close-button" onClick={onClose}>×</button></div><form onSubmit={submit}>
 <div className="form-grid"><label className="field"><span>Número de factura</span><input value={head.document_number} onChange={e=>setHead({...head,document_number:e.target.value})}/></label><label className="field"><span>Concepto general</span><input value={head.description} onChange={e=>setHead({...head,description:e.target.value})}/></label><label className="field"><span>Fecha emisión</span><input type="date" value={head.issue_date} onChange={e=>setHead({...head,issue_date:e.target.value})}/></label><label className="field"><span>Vencimiento</span><input type="date" value={head.due_date} onChange={e=>setHead({...head,due_date:e.target.value})}/></label><label className="field"><span>IVA</span><select value={head.vat_rate} onChange={e=>setHead({...head,vat_rate:Number(e.target.value)})}><option value={0}>0% / Sin IVA</option><option value={10.5}>10,5%</option><option value={21}>21%</option><option value={27}>27%</option></select></label></div>
 <div className="invoice-picker"><div className="invoice-picker-head"><span>Facturar</span><span>Ítem</span><span>Importe ítem</span><span>Avance</span><span>Ejecutado</span><span>Ya facturado</span><span>Disponible</span><span>Monto ahora</span></div>{eligible.length===0?<div className="invoice-empty">No hay ítems completados con saldo disponible para facturar.</div>:eligible.map((x:any)=><div className={`invoice-picker-row ${selected[x.id]?'selected':''}`} key={x.id}><label className="invoice-check"><input type="checkbox" checked={!!selected[x.id]} onChange={e=>toggle(x,e.target.checked)}/></label><div><b>{x.code}</b><small>{x.description}</small></div><span>{money(x.budget_amount)}</span><span>{Number(x.progress_percent||0).toFixed(1)}%</span><span>{money(x.executed_amount)}</span><span>{money(x.billed_amount)}</span><b>{money(x.available_to_invoice)}</b><input type="number" step="0.01" min="0" max={Number(x.available_to_invoice||0)} disabled={!selected[x.id]} value={selected[x.id]?amounts[x.id]??'':''} onChange={e=>setAmounts(o=>({...o,[x.id]:Number(e.target.value)}))}/></div>)}</div>
 <label className="field full" style={{marginTop:14}}><span>Notas</span><input value={head.notes} onChange={e=>setHead({...head,notes:e.target.value})}/></label>
 <div className="invoice-total" style={{display:'grid',gap:6}}><div><span>Neto</span><strong>{money(net)}</strong></div><div><span>IVA {Number(head.vat_rate||0).toLocaleString('es-AR')}%</span><strong>{money(vat)}</strong></div><div><span>TOTAL FACTURA</span><strong>{money(total)}</strong></div></div>
 <div className="modal-actions"><button type="button" className="ghost-button" onClick={onClose}>Cancelar</button><button className="primary-button" disabled={saving||net<=0}>{saving?'Guardando…':'Crear factura'}</button></div></form></div></div>
}'''
s = s[:start] + new_func + s[end:]
write(p,s)

# ---------- frontend servicio ----------
p = files['service_front']; s = p.read_text(encoding='utf-8')
# invoice form state default and reset
s = s.replace("const [invoicePeriod,setInvoicePeriod]=useState<any|null>(null); const [invoice,setInvoice]=useState({document_number:'',issue_date:today(),due_date:'',notes:''});",
              "const [invoicePeriod,setInvoicePeriod]=useState<any|null>(null); const [invoice,setInvoice]=useState({document_number:'',issue_date:today(),due_date:'',notes:'',vat_rate:21});")
s = s.replace("setInvoice({document_number:'',issue_date:today(),due_date:String(p.due_date||'').slice(0,10),notes:''})",
              "setInvoice({document_number:'',issue_date:today(),due_date:String(p.due_date||'').slice(0,10),notes:'',vat_rate:21})")
# Payments due should use gross invoice total
s = s.replace("const due=Math.max(0,Number(p.amount||0)-Number(p.paid_amount||0));",
              "const due=Math.max(0,Number(p.invoice_total_amount||p.amount||0)-Number(p.paid_amount||0));")

# replace Billing function
st = s.find('function Billing('); en = s.find('\n\nfunction Payments(', st)
if st<0 or en<0: raise SystemExit('No pude localizar Billing en ServiceDetail.tsx')
billing = r'''function Billing({periods,onInvoice,onUpload,docs}:{periods:any[];onInvoice:(p:any)=>void;onUpload:(p:any)=>void;docs:any[]}){return <Card><SectionTitle title="Facturación por período" subtitle="El monto del servicio es neto. Al facturar se agrega el IVA y el total con IVA pasa a Por cobrar."/><div className="table-wrap"><table><thead><tr><th>Período</th><th>Vigencia</th><th>Vencimiento</th><th>Neto</th><th>IVA</th><th>Total factura</th><th>Factura</th><th>Estado</th><th>Acciones</th></tr></thead><tbody>{periods.map(p=>{const hasPdf=docs.some((d:any)=>d.related_type==='invoice'&&d.related_id===p.receivable_id);const net=Number(p.amount||0);const total=Number(p.invoice_total_amount||p.amount||0);const iva=Math.max(0,total-net);return <tr key={p.id}><td><b>Mes {p.period_number}</b></td><td>{dateAR(p.period_start)} → {dateAR(p.period_end)}</td><td>{dateAR(p.due_date)}</td><td><b>{money(net)}</b></td><td>{p.receivable_id?money(iva):'—'}</td><td><b>{p.receivable_id?money(total):'—'}</b></td><td>{p.document_number||'—'}</td><td>{p.receivable_id?<Status tone={p.receivable_status==='cobrado'?'green':p.receivable_status==='parcial'?'blue':'yellow'}>{p.receivable_status||'facturado'}</Status>:<Status tone="gray">Pendiente</Status>}</td><td><div className="row-actions">{!p.receivable_id?<button className="mini-button" onClick={()=>onInvoice(p)}>Facturar</button>:<button className="mini-button" onClick={()=>onUpload(p)}>{hasPdf?'Reemplazar / agregar PDF':'Subir factura PDF'}</button>}</div></td></tr>})}</tbody></table></div></Card>}'''
s = s[:st] + billing + s[en:]
# replace Payments function
a = s.find('function Payments('); b = s.find('\n\nfunction Documents(', a)
if a<0 or b<0: raise SystemExit('No pude localizar Payments en ServiceDetail.tsx')
payments = r'''function Payments({rows,onPay,onUpload}:{rows:any[];onPay:(p:any)=>void;onUpload:(p:any)=>void}){if(rows.length===0)return <Card><Empty text="Todavía no hay facturas para cobrar."/></Card>;return <Card><SectionTitle title="Cobros" subtitle="El saldo a cobrar corresponde al total de la factura, IVA incluido."/><div className="table-wrap"><table><thead><tr><th>Factura</th><th>Período</th><th>Total factura</th><th>Cobrado</th><th>Saldo</th><th>Estado</th><th>Acciones</th></tr></thead><tbody>{rows.map(p=>{const invoiceTotal=Number(p.invoice_total_amount||p.amount||0);const balance=Math.max(0,invoiceTotal-Number(p.paid_amount||0));return <tr key={p.id}><td><b>{p.document_number||'—'}</b></td><td>Mes {p.period_number}</td><td>{money(invoiceTotal)}</td><td>{money(p.paid_amount)}</td><td><b>{money(balance)}</b></td><td><Status tone={balance<=0?'green':Number(p.paid_amount)>0?'blue':'yellow'}>{balance<=0?'Cobrado':Number(p.paid_amount)>0?'Parcial':'Pendiente'}</Status></td><td><div className="row-actions">{balance>0&&<button className="mini-button" onClick={()=>onPay(p)}>Registrar cobro</button>}{Number(p.paid_amount)>0&&<button className="mini-button" onClick={()=>onUpload(p)}>Subir comprobante</button>}</div></td></tr>})}</tbody></table></div></Card>}'''
s = s[:a] + payments + s[b:]
# replace InvoiceModal
x = s.find('function InvoiceModal('); y = s.find('\n\nfunction PaymentModal(', x)
if x<0 or y<0: raise SystemExit('No pude localizar InvoiceModal en ServiceDetail.tsx')
invmodal = r'''function InvoiceModal({row,form,setForm,saving,close,submit}:any){const net=Number(row.amount||0);const vat=net*Number(form.vat_rate||0)/100;const total=net+vat;return <div className="modal-backdrop"><div className="modal"><div className="modal-head"><div><span className="eyebrow">FACTURAR</span><h2>Mes {row.period_number}</h2><p>El monto del período es neto. El IVA se suma al total a cobrar.</p></div><button className="close-button" onClick={close}>×</button></div><div className="form-grid"><label className="field"><span>Número de factura *</span><input value={form.document_number} onChange={e=>setForm({...form,document_number:e.target.value})}/></label><label className="field"><span>Fecha emisión</span><input type="date" value={form.issue_date} onChange={e=>setForm({...form,issue_date:e.target.value})}/></label><label className="field"><span>Vencimiento</span><input type="date" value={form.due_date} onChange={e=>setForm({...form,due_date:e.target.value})}/></label><label className="field"><span>IVA</span><select value={form.vat_rate} onChange={e=>setForm({...form,vat_rate:Number(e.target.value)})}><option value={0}>0% / Sin IVA</option><option value={10.5}>10,5%</option><option value={21}>21%</option><option value={27}>27%</option></select></label><label className="field full"><span>Notas</span><textarea rows={3} value={form.notes} onChange={e=>setForm({...form,notes:e.target.value})}/></label></div><div className="modal-note" style={{display:'grid',gap:6}}><div>Neto: <b>{money(net)}</b></div><div>IVA {Number(form.vat_rate||0).toLocaleString('es-AR')}%: <b>{money(vat)}</b></div><div style={{fontSize:18}}>TOTAL FACTURA: <b>{money(total)}</b></div></div><div className="modal-actions"><button className="ghost-button" onClick={close}>Cancelar</button><button className="primary-button" disabled={saving||!form.document_number.trim()} onClick={submit}>{saving?'Guardando…':'Crear factura'}</button></div></div></div>}'''
s = s[:x] + invmodal + s[y:]
write(p,s)
print('\nIVA aplicado. No requiere migración SQL.')
