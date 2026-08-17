from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

# backend
p=ROOT/"backend/app/routers/service_detail.py"
t=p.read_text(encoding="utf-8")
marker='@router.delete("/{service_id}/periods/{period_id}/invoice")'
if marker not in t:
    t=t.rstrip()+'\n\n@router.delete("/{service_id}/periods/{period_id}/invoice")\ndef delete_period_invoice(service_id: UUID, period_id: UUID):\n    """Elimina una factura de servicio solo si todavía no tiene cobros."""\n    with db_cursor() as cur:\n        cur.execute(sql.SQL("""\n            SELECT sp.*, r.id AS receivable_id, r.document_number, r.amount AS receivable_amount\n            FROM {}.service_periods sp\n            LEFT JOIN {}.receivables r ON r.id=sp.receivable_id\n            WHERE sp.id=%s AND sp.service_id=%s\n            FOR UPDATE\n        """).format(S, S), [period_id, service_id])\n        period = cur.fetchone()\n\n        if not period:\n            raise HTTPException(404, "Período no encontrado")\n\n        receivable_id = period.get("receivable_id")\n        if not receivable_id:\n            raise HTTPException(400, "Este período no tiene una factura para eliminar")\n\n        cur.execute(sql.SQL("""\n            SELECT COALESCE(SUM(amount),0) AS paid\n            FROM {}.financial_movements\n            WHERE receivable_id=%s AND type=\'ingreso\'\n        """).format(S), [receivable_id])\n        paid = _money(cur.fetchone()["paid"])\n\n        if paid > 0:\n            raise HTTPException(\n                400,\n                "No se puede eliminar una factura que ya tiene cobros registrados. Primero hay que corregir o eliminar esos cobros."\n            )\n\n        # Desvincular primero el período para volver a dejarlo facturable.\n        cur.execute(\n            sql.SQL("UPDATE {}.service_periods SET receivable_id=NULL WHERE id=%s").format(S),\n            [period_id],\n        )\n\n        # Quitar referencias documentales a esa factura para evitar vínculos huérfanos.\n        cur.execute(sql.SQL("""\n            UPDATE {}.service_documents\n            SET related_type=NULL, related_id=NULL\n            WHERE service_id=%s\n              AND related_type=\'invoice\'\n              AND related_id=%s\n        """).format(S), [service_id, receivable_id])\n\n        cur.execute(\n            sql.SQL("DELETE FROM {}.receivables WHERE id=%s AND service_id=%s").format(S),\n            [receivable_id, service_id],\n        )\n\n    return {"ok": True, "period_id": str(period_id)}\n'+"\n"
p.write_text(t,encoding="utf-8")

# frontend
p=ROOT/"front/src/components/ServiceDetail.tsx"
t=p.read_text(encoding="utf-8")

old_call="""  {tab==='billing'&&<Billing periods={periods} onInvoice={(p:any)=>{setInvoicePeriod(p);setInvoice({document_number:'',issue_date:today(),due_date:String(p.due_date||'').slice(0,10),notes:'',vat_rate:21})}} onUpload={(p:any)=>setUpload({type:'factura',title:`Factura ${p.document_number||p.period_number}`,related_type:'invoice',related_id:p.receivable_id})} docs={docs}/>} """
new_call="""  {tab==='billing'&&<Billing periods={periods} onInvoice={(p:any)=>{setInvoicePeriod(p);setInvoice({document_number:'',issue_date:today(),due_date:String(p.due_date||'').slice(0,10),notes:'',vat_rate:21})}} onUpload={(p:any)=>setUpload({type:'factura',title:`Factura ${p.document_number||p.period_number}`,related_type:'invoice',related_id:p.receivable_id})} onDelete={async(p:any)=>{if(!confirm(`¿Eliminar la factura ${p.document_number||`Mes ${p.period_number}`}? El período quedará disponible para volver a facturar.`))return;try{await api.remove(`services/${serviceId}/periods/${p.id}`,'invoice');await load()}catch(e:any){alert(e.message)}}} docs={docs}/>} """

if old_call not in t:
    raise SystemExit("ERROR: no encontré llamada a Billing en ServiceDetail.tsx")
t=t.replace(old_call,new_call,1)

old_sig="""function Billing({periods,onInvoice,onUpload,docs}:{periods:any[];onInvoice:(p:any)=>void;onUpload:(p:any)=>void;docs:any[]})"""
new_sig="""function Billing({periods,onInvoice,onUpload,onDelete,docs}:{periods:any[];onInvoice:(p:any)=>void;onUpload:(p:any)=>void;onDelete:(p:any)=>void;docs:any[]})"""
if old_sig not in t:
    raise SystemExit("ERROR: no encontré firma de Billing")
t=t.replace(old_sig,new_sig,1)

old_actions="""{!p.receivable_id?<button className="mini-button" onClick={()=>onInvoice(p)}>Facturar</button>:<button className="mini-button" onClick={()=>onUpload(p)}>{hasPdf?'Reemplazar / agregar PDF':'Subir factura PDF'}</button>}"""
new_actions="""{!p.receivable_id
  ? <button className="mini-button" onClick={()=>onInvoice(p)}>Facturar</button>
  : <>
      <button className="mini-button" onClick={()=>onUpload(p)}>{hasPdf?'Reemplazar / agregar PDF':'Subir factura PDF'}</button>
      {Number(p.paid_amount||0)<=0&&<button className="mini-button danger-text" onClick={()=>onDelete(p)}>Eliminar factura</button>}
    </>
}"""
if old_actions not in t:
    raise SystemExit("ERROR: no encontré acciones de facturación")
t=t.replace(old_actions,new_actions,1)

p.write_text(t,encoding="utf-8")
print("OK: eliminar factura de servicio habilitado.")
