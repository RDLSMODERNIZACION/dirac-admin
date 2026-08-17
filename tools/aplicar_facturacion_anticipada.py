from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

p = ROOT / 'backend/app/routers/work_detail.py'
t = p.read_text(encoding='utf-8')

repls = [
("GREATEST(0, (wi.budget_amount * wi.progress_percent / 100.0) - COALESCE(b.billed_amount,0)) AS available_to_invoice",
 "GREATEST(0, wi.budget_amount - COALESCE(b.billed_amount,0)) AS available_to_invoice"),
('''        available_to_invoice = sum((Decimal(str(x.get("available_to_invoice") or 0)) for x in items if x.get("status") != "cancelado"), Decimal("0"))\n        collected = Decimal("0")''',
 '''        available_to_invoice = sum((Decimal(str(x.get("available_to_invoice") or 0)) for x in items if x.get("status") != "cancelado"), Decimal("0"))\n        net_billed = sum((Decimal(str(x.get("billed_amount") or 0)) for x in items if x.get("status") != "cancelado"), Decimal("0"))\n        advanced_invoicing = max(Decimal("0"), net_billed - executed_amount)\n        executed_unbilled = max(Decimal("0"), executed_amount - net_billed)\n        collected = Decimal("0")'''),
('''        collected = Decimal(str(cur.fetchone()["total"] or 0))\n        paid = Decimal("0")''',
 '''        collected = Decimal(str(cur.fetchone()["total"] or 0))\n        collected_ahead_execution = max(Decimal("0"), collected - executed_amount)\n        paid = Decimal("0")'''),
('''            "available_to_invoice": available_to_invoice,\n            "collected": collected,\n            "pending_collection": max(Decimal("0"), invoiced - collected),''',
 '''            "available_to_invoice": available_to_invoice,\n            "net_billed": net_billed,\n            "advanced_invoicing": advanced_invoicing,\n            "executed_unbilled": executed_unbilled,\n            "collected": collected,\n            "collected_ahead_execution": collected_ahead_execution,\n            "pending_collection": max(Decimal("0"), invoiced - collected),'''),
('''            executed = Decimal(str(item.get("executed_amount") or 0))\n            billed = Decimal(str(item.get("billed_amount") or 0))\n            available = max(Decimal("0"), executed - billed)\n            if req.amount > available:\n                raise HTTPException(\n                    400,\n                    f"{item.get('code') or item['description']}: disponible {available}, solicitado {req.amount}"\n                )\n            validated.append((item, req.amount, executed))''',
 '''            executed = Decimal(str(item.get("executed_amount") or 0))\n            billed = Decimal(str(item.get("billed_amount") or 0))\n            contractual = Decimal(str(item.get("budget_amount") or 0))\n            available = max(Decimal("0"), contractual - billed)\n            if req.amount > available:\n                raise HTTPException(\n                    400,\n                    f"{item.get('code') or item['description']}: saldo contractual disponible {available}, solicitado {req.amount}"\n                )\n            validated.append((item, req.amount, executed))''')
]
for old,new in repls:
    if old not in t:
        raise SystemExit('ERROR backend: patrón no encontrado: '+old[:80])
    t=t.replace(old,new,1)
p.write_text(t,encoding='utf-8')

p = ROOT / 'front/src/components/WorkDetail.tsx'
t = p.read_text(encoding='utf-8')
t=t.replace('El avance es automático: Pendiente y En ejecución = 0%; Completado = 100%. Solo los ítems completados quedan disponibles para facturar.', 'El avance físico y la facturación son independientes. Pendiente y En ejecución = 0%; Completado = 100%. Un ítem puede facturarse anticipadamente hasta su valor contractual.')
t=t.replace('Seleccioná los ítems completados y el importe que corresponde facturar de cada uno.', 'Podés facturar ítems ejecutados o anticipadamente. El sistema identifica cuánto de la factura queda adelantado respecto de la ejecución.')
needle='<Info l="Facturado acumulado" v={money(m.invoiced)}/><Info l="Pendiente de cobro" v={money(m.pending_collection)}/>'
if needle in t:
    t=t.replace(needle, needle+'<Info l="Ejecutado no facturado" v={money(m.executed_unbilled||0)}/><Info l="Facturación anticipada" v={money(m.advanced_invoicing||0)}/><Info l="Cobro adelantado vs ejecución" v={money(m.collected_ahead_execution||0)}/>',1)

start=t.find('function InvoiceByItemsModal(')
end=t.find('\nfunction Documents(', start)
if start==-1 or end==-1:
    raise SystemExit('ERROR frontend: no encontré InvoiceByItemsModal/Documents')
new_modal = r'''function InvoiceByItemsModal({items,onClose,onSave}:{items:any[];onClose:()=>void;onSave:(x:any)=>Promise<void>}){
 const eligible=items.filter((x:any)=>x.status!=='cancelado'&&Number(x.available_to_invoice||0)>0);
 const [head,setHead]=useState<any>({document_number:'',description:'',issue_date:new Date().toISOString().slice(0,10),due_date:'',notes:'',vat_rate:21});
 const [selected,setSelected]=useState<Record<string,boolean>>({});
 const [amounts,setAmounts]=useState<Record<string,number>>({});
 const [saving,setSaving]=useState(false);
 const selectedAmount=(x:any)=>selected[x.id]?Number(amounts[x.id]||0):0;
 const executedAvailable=(x:any)=>Math.max(0,Number(x.executed_amount||0)-Number(x.billed_amount||0));
 const advanceFor=(x:any)=>Math.max(0,selectedAmount(x)-executedAvailable(x));
 const netTotal=eligible.reduce((a:number,x:any)=>a+selectedAmount(x),0);
 const advanceTotal=eligible.reduce((a:number,x:any)=>a+advanceFor(x),0);
 const vatRate=Number(head.vat_rate||0);
 const vatAmount=netTotal*vatRate/100;
 const invoiceTotal=netTotal+vatAmount;
 const toggle=(x:any,v:boolean)=>{setSelected(o=>({...o,[x.id]:v}));if(v&&amounts[x.id]===undefined)setAmounts(o=>({...o,[x.id]:Number(x.available_to_invoice||0)}))};
 const submit=async(e:any)=>{e.preventDefault();const lines=eligible.filter(x=>selected[x.id]).map(x=>({work_item_id:x.id,amount:Number(amounts[x.id]||0)})).filter(x=>x.amount>0);if(!lines.length){alert('Seleccioná al menos un ítem con monto mayor que cero');return}for(const x of eligible){if(selected[x.id]&&Number(amounts[x.id]||0)>Number(x.available_to_invoice||0)+0.01){alert(`${x.code}: el monto supera el saldo contractual disponible`);return}}setSaving(true);try{await onSave({...head,vat_rate:vatRate,due_date:head.due_date||null,items:lines})}catch(x:any){alert(x.message)}finally{setSaving(false)}};
 return <div className="modal-backdrop"><div className="modal invoice-modal"><div className="modal-head"><div><h2>Nueva factura de obra</h2><p>La facturación puede adelantarse a la ejecución. El anticipo se muestra separado para control.</p></div><button className="close-button" onClick={onClose}>×</button></div><form onSubmit={submit}><div className="form-grid"><label className="field"><span>Número de factura</span><input value={head.document_number} onChange={e=>setHead({...head,document_number:e.target.value})}/></label><label className="field"><span>Concepto general</span><input value={head.description} onChange={e=>setHead({...head,description:e.target.value})}/></label><label className="field"><span>Fecha emisión</span><input type="date" value={head.issue_date} onChange={e=>setHead({...head,issue_date:e.target.value})}/></label><label className="field"><span>Vencimiento</span><input type="date" value={head.due_date} onChange={e=>setHead({...head,due_date:e.target.value})}/></label><label className="field"><span>IVA</span><select value={head.vat_rate} onChange={e=>setHead({...head,vat_rate:Number(e.target.value)})}><option value={0}>0%</option><option value={10.5}>10,5%</option><option value={21}>21%</option><option value={27}>27%</option></select></label></div><div className="invoice-picker"><div className="invoice-picker-head"><span>Facturar</span><span>Ítem</span><span>Valor contractual</span><span>Ejecutado</span><span>Ya facturado</span><span>Saldo contractual</span><span>Monto ahora</span><span>Anticipo</span></div>{eligible.length===0?<div className="invoice-empty">No hay ítems con saldo contractual pendiente de facturar.</div>:eligible.map((x:any)=>{const advance=advanceFor(x);return <div className={`invoice-picker-row ${selected[x.id]?'selected':''}`} key={x.id}><label className="invoice-check"><input type="checkbox" checked={!!selected[x.id]} onChange={e=>toggle(x,e.target.checked)}/></label><div><b>{x.code}</b><small>{x.description}</small><small>Estado: {String(x.status||'').replaceAll('_',' ')}</small></div><span>{money(x.budget_amount)}</span><span>{money(x.executed_amount)}</span><span>{money(x.billed_amount)}</span><b>{money(x.available_to_invoice)}</b><input type="number" step="0.01" min="0" max={Number(x.available_to_invoice||0)} disabled={!selected[x.id]} value={selected[x.id]?amounts[x.id]??'':''} onChange={e=>setAmounts(o=>({...o,[x.id]:Number(e.target.value)}))}/><span className={advance>0?'danger-text':''}><b>{advance>0?money(advance):'—'}</b></span></div>})}</div>{advanceTotal>0&&<div className="requirement-warning" style={{marginTop:14}}>Esta factura incluye <b>{money(advanceTotal)}</b> de facturación anticipada respecto de lo ejecutado actualmente.</div>}<label className="field full" style={{marginTop:14}}><span>Notas</span><input value={head.notes} onChange={e=>setHead({...head,notes:e.target.value})}/></label><div className="invoice-total" style={{display:'grid',gap:7}}><div style={{display:'flex',justifyContent:'space-between',width:'100%'}}><span>Neto a facturar</span><strong>{money(netTotal)}</strong></div><div style={{display:'flex',justifyContent:'space-between',width:'100%'}}><span>IVA {vatRate}%</span><strong>{money(vatAmount)}</strong></div>{advanceTotal>0&&<div style={{display:'flex',justifyContent:'space-between',width:'100%'}}><span>Facturación anticipada</span><strong className="danger-text">{money(advanceTotal)}</strong></div>}<div style={{display:'flex',justifyContent:'space-between',width:'100%',fontSize:17}}><span>Total factura</span><strong>{money(invoiceTotal)}</strong></div></div><div className="modal-actions"><button type="button" className="ghost-button" onClick={onClose}>Cancelar</button><button className="primary-button" disabled={saving||netTotal<=0}>{saving?'Guardando…':'Crear factura'}</button></div></form></div></div>
}'''
t=t[:start]+new_modal+t[end:]
p.write_text(t,encoding='utf-8')
print('OK: facturación anticipada habilitada.')
