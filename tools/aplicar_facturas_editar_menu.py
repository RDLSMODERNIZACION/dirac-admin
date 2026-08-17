from pathlib import Path

ROOT = Path.cwd()

def rep(t, old, new, label):
    if old not in t:
        raise SystemExit(f"ERROR: no encontré {label}")
    return t.replace(old, new, 1)

# backend obra
p=ROOT/'backend/app/routers/work_detail.py'
t=p.read_text(encoding='utf-8')
if 'class InvoiceHeaderUpdate(BaseModel):' not in t:
    anchor='class WorkPaymentCreate(BaseModel):'
    block='''class InvoiceHeaderUpdate(BaseModel):\n    document_number: str | None = None\n    description: str | None = None\n    issue_date: date | None = None\n    due_date: date | None = None\n    notes: str | None = None\n\n\n@router.patch("/{work_id}/invoices/{invoice_id}")\ndef update_client_invoice(work_id: UUID, invoice_id: UUID, body: InvoiceHeaderUpdate):\n    with db_cursor() as cur:\n        cur.execute(sql.SQL("SELECT * FROM {}.work_invoices WHERE id=%s AND work_id=%s FOR UPDATE").format(S), [invoice_id, work_id])\n        invoice=cur.fetchone()\n        if not invoice:\n            raise HTTPException(404,"Factura no encontrada")\n        document_number=body.document_number if body.document_number is not None else invoice.get("invoice_number")\n        description=body.description if body.description is not None else invoice.get("description")\n        issue_date=body.issue_date or invoice.get("issue_date")\n        due_date=body.due_date\n        notes=body.notes if body.notes is not None else invoice.get("notes")\n        cur.execute(sql.SQL("""\n            UPDATE {}.work_invoices\n            SET invoice_number=%s,description=%s,issue_date=%s,due_date=%s,notes=%s\n            WHERE id=%s RETURNING *\n        """).format(S),[document_number or None,description,issue_date,due_date,notes,invoice_id])\n        updated=cur.fetchone()\n        if invoice.get("receivable_id"):\n            cur.execute(sql.SQL("""\n                UPDATE {}.receivables\n                SET document_number=%s,description=%s,issue_date=%s,due_date=%s,notes=%s\n                WHERE id=%s AND work_id=%s\n            """).format(S),[\n                document_number or None,\n                description or f"Factura de obra {document_number or ''}".strip(),\n                issue_date,due_date,notes,invoice["receivable_id"],work_id\n            ])\n        return updated\n\n\n'''
    if anchor not in t: raise SystemExit('ERROR: WorkPaymentCreate')
    t=t.replace(anchor,block+anchor,1)
p.write_text(t,encoding='utf-8')

# backend servicio
p=ROOT/'backend/app/routers/service_detail.py'
t=p.read_text(encoding='utf-8')
if 'class PeriodInvoiceUpdate(BaseModel):' not in t:
    anchor='class ServicePaymentCreate(BaseModel):'
    block='''class PeriodInvoiceUpdate(BaseModel):\n    document_number: str | None = None\n    issue_date: date | None = None\n    due_date: date | None = None\n    notes: str | None = None\n\n\n@router.patch("/{service_id}/periods/{period_id}/invoice")\ndef update_period_invoice(service_id: UUID, period_id: UUID, body: PeriodInvoiceUpdate):\n    with db_cursor() as cur:\n        cur.execute(sql.SQL("""\n            SELECT sp.receivable_id,r.document_number,r.issue_date,r.due_date,r.notes\n            FROM {}.service_periods sp\n            JOIN {}.receivables r ON r.id=sp.receivable_id\n            WHERE sp.id=%s AND sp.service_id=%s\n            FOR UPDATE\n        """).format(S,S),[period_id,service_id])\n        row=cur.fetchone()\n        if not row:\n            raise HTTPException(404,"Factura del período no encontrada")\n        cur.execute(sql.SQL("""\n            UPDATE {}.receivables\n            SET document_number=%s,issue_date=%s,due_date=%s,notes=%s\n            WHERE id=%s AND service_id=%s RETURNING *\n        """).format(S),[\n            body.document_number if body.document_number is not None else row.get("document_number"),\n            body.issue_date or row.get("issue_date"),\n            body.due_date,\n            body.notes if body.notes is not None else row.get("notes"),\n            row["receivable_id"],service_id\n        ])\n        return cur.fetchone()\n\n\n'''
    if anchor not in t: raise SystemExit('ERROR: ServicePaymentCreate')
    t=t.replace(anchor,block+anchor,1)
p.write_text(t,encoding='utf-8')

# frontend obra
p=ROOT/'front/src/components/WorkDetail.tsx'
t=p.read_text(encoding='utf-8')
t=rep(t,
" const [open,setOpen]=useState(false); const [upload,setUpload]=useState<any>(null);",
" const [open,setOpen]=useState(false); const [upload,setUpload]=useState<any>(null); const [editInvoice,setEditInvoice]=useState<any>(null); const [menuOpen,setMenuOpen]=useState<string|null>(null);",
'estado facturas obra')
t=rep(t,
" const remove=async(r:any)=>{if(!confirm(`¿Eliminar la factura ${r.invoice_number||''}? Solo se permite si todavía no tiene cobros.`))return;",
" const remove=async(r:any)=>{setMenuOpen(null);if(!confirm(`¿Eliminar la factura ${r.invoice_number||''}? Solo se permite si todavía no tiene cobros.`))return;",
'remove obra')
idx=t.find(' const view=async(id:string)=>',t.find('function Invoices('))
if idx<0: raise SystemExit('ERROR: view obra')
t=t[:idx]+" const saveEdit=async(f:any)=>{await api.patch(`/api/works/${workId}/invoices/${editInvoice.id}`,f);setEditInvoice(null);setMenuOpen(null);await reload()};\n"+t[idx:]
t=rep(t,
'<td><button className="mini-button danger-text" onClick={()=>remove(r)}>Eliminar</button></td></tr>',
'<td onClick={e=>e.stopPropagation()}><div className="invoice-row-menu"><button className="work-row-menu-button" onClick={()=>setMenuOpen(menuOpen===r.id?null:r.id)}>⋯</button>{menuOpen===r.id&&<div className="work-row-menu-popover invoice-menu-popover"><button onClick={()=>{setMenuOpen(null);setEditInvoice(r)}}>Editar</button><button className="danger-text" onClick={()=>remove(r)}>Eliminar</button></div>}</div></td></tr>',
'menu obra')
t=rep(t,
'{open&&<InvoiceByItemsModal items={items} onClose={()=>setOpen(false)} onSave={save}/>} {upload&&<RelatedUploadModal',
'{open&&<InvoiceByItemsModal items={items} onClose={()=>setOpen(false)} onSave={save}/>} {editInvoice&&<InvoiceHeaderEditModal invoice={editInvoice} onClose={()=>setEditInvoice(null)} onSave={saveEdit}/>} {upload&&<RelatedUploadModal',
'modal obra')
if 'function InvoiceHeaderEditModal(' not in t:
    anchor='function InvoiceByItemsModal({items,onClose,onSave}'
    idx=t.find(anchor)
    if idx<0: raise SystemExit('ERROR: InvoiceByItemsModal')
    block='''function InvoiceHeaderEditModal({invoice,onClose,onSave}:{invoice:any;onClose:()=>void;onSave:(x:any)=>Promise<void>}){\n const [f,setF]=useState<any>({document_number:invoice.invoice_number||'',description:invoice.description||'',issue_date:invoice.issue_date?String(invoice.issue_date).slice(0,10):'',due_date:invoice.due_date?String(invoice.due_date).slice(0,10):'',notes:invoice.notes||''});const [saving,setSaving]=useState(false);\n const submit=async(e:any)=>{e.preventDefault();setSaving(true);try{await onSave({...f,due_date:f.due_date||null})}catch(x:any){alert(x.message)}finally{setSaving(false)}};\n return <div className="modal-backdrop"><div className="modal"><div className="modal-head"><div><span className="eyebrow">EDITAR FACTURA</span><h2>{invoice.invoice_number||'Factura de obra'}</h2><p>Se mantienen el importe total y los ítems facturados.</p></div><button className="close-button" onClick={onClose}>×</button></div><form onSubmit={submit}><div className="form-grid"><label className="field"><span>Número de factura</span><input value={f.document_number} onChange={e=>setF({...f,document_number:e.target.value})}/></label><label className="field"><span>Concepto</span><input value={f.description} onChange={e=>setF({...f,description:e.target.value})}/></label><label className="field"><span>Fecha emisión</span><input type="date" value={f.issue_date} onChange={e=>setF({...f,issue_date:e.target.value})}/></label><label className="field"><span>Vencimiento</span><input type="date" value={f.due_date} onChange={e=>setF({...f,due_date:e.target.value})}/></label><label className="field full"><span>Notas</span><textarea rows={3} value={f.notes} onChange={e=>setF({...f,notes:e.target.value})}/></label></div><div className="modal-note">Total factura: <b>{money(invoice.total_amount)}</b>. El importe y los ítems no cambian.</div><div className="modal-actions"><button type="button" className="ghost-button" onClick={onClose}>Cancelar</button><button className="primary-button" disabled={saving}>{saving?'Guardando…':'Guardar cambios'}</button></div></form></div></div>\n}\n\n'''
    t=t[:idx]+block+t[idx:]
p.write_text(t,encoding='utf-8')

# frontend servicio
p=ROOT/'front/src/components/ServiceDetail.tsx'
t=p.read_text(encoding='utf-8')
t=rep(t,
" const [invoicePeriod,setInvoicePeriod]=useState<any|null>(null); const [invoice,setInvoice]=useState({document_number:'',issue_date:today(),due_date:'',notes:'',vat_rate:21});",
" const [invoicePeriod,setInvoicePeriod]=useState<any|null>(null); const [invoice,setInvoice]=useState({document_number:'',issue_date:today(),due_date:'',notes:'',vat_rate:21}); const [editInvoice,setEditInvoice]=useState<any|null>(null); const [invoiceMenu,setInvoiceMenu]=useState<string|null>(null);",
'estado factura servicio')
t=rep(t,
"{tab==='billing'&&<Billing periods={periods} onInvoice=",
"{tab==='billing'&&<Billing periods={periods} menuOpen={invoiceMenu} setMenuOpen={setInvoiceMenu} onEdit={(p:any)=>{setInvoiceMenu(null);setEditInvoice(p)}} onInvoice=",
'llamada Billing')
t=rep(t,
'function Billing({periods,onInvoice,onUpload,onDelete,docs}:{periods:any[];onInvoice:(p:any)=>void;onUpload:(p:any)=>void;onDelete:(p:any)=>void;docs:any[]}){',
'function Billing({periods,onInvoice,onEdit,onUpload,onDelete,docs,menuOpen,setMenuOpen}:{periods:any[];onInvoice:(p:any)=>void;onEdit:(p:any)=>void;onUpload:(p:any)=>void;onDelete:(p:any)=>void;docs:any[];menuOpen:string|null;setMenuOpen:(id:string|null)=>void}){',
'firma Billing')
t=rep(t,
'''      <button className="mini-button" onClick={()=>onUpload(p)}>{hasPdf?'Reemplazar / agregar PDF':'Subir factura PDF'}</button>\n      {Number(p.paid_amount||0)<=0&&<button className="mini-button danger-text" onClick={()=>onDelete(p)}>Eliminar factura</button>}''',
'''      <button className="mini-button" onClick={()=>onUpload(p)}>{hasPdf?'Reemplazar / agregar PDF':'Subir factura PDF'}</button>\n      <div className="invoice-row-menu"><button className="work-row-menu-button" onClick={()=>setMenuOpen(menuOpen===p.id?null:p.id)}>⋯</button>{menuOpen===p.id&&<div className="work-row-menu-popover invoice-menu-popover"><button onClick={()=>onEdit(p)}>Editar</button>{Number(p.paid_amount||0)<=0&&<button className="danger-text" onClick={()=>onDelete(p)}>Eliminar</button>}</div>}</div>''',
'acciones servicio')
idx=t.find('{payRow&&<PaymentModal')
if idx<0: raise SystemExit('ERROR: payRow')
t=t[:idx]+'''{editInvoice&&<ServiceInvoiceEditModal row={editInvoice} saving={saving} close={()=>setEditInvoice(null)} submit={async(f:any)=>{setSaving(true);try{await api.patch(`/api/services/${serviceId}/periods/${editInvoice.id}/invoice`,f);setEditInvoice(null);await load()}catch(e:any){alert(e.message)}finally{setSaving(false)}}}/>} \n  '''+t[idx:]
if 'function ServiceInvoiceEditModal(' not in t:
    anchor='function PaymentModal({row,accounts,form,setForm,saving,close,submit}:any){'
    idx=t.find(anchor)
    if idx<0: raise SystemExit('ERROR: PaymentModal función')
    block='''function ServiceInvoiceEditModal({row,saving,close,submit}:any){\n const [f,setF]=useState<any>({document_number:row.document_number||'',issue_date:row.issue_date?String(row.issue_date).slice(0,10):today(),due_date:row.due_date?String(row.due_date).slice(0,10):'',notes:''});\n return <div className="modal-backdrop"><div className="modal"><div className="modal-head"><div><span className="eyebrow">EDITAR FACTURA</span><h2>{row.document_number||`Mes ${row.period_number}`}</h2><p>El monto del período no se modifica.</p></div><button className="close-button" onClick={close}>×</button></div><div className="form-grid"><label className="field"><span>Número de factura *</span><input value={f.document_number} onChange={e=>setF({...f,document_number:e.target.value})}/></label><label className="field"><span>Fecha emisión</span><input type="date" value={f.issue_date} onChange={e=>setF({...f,issue_date:e.target.value})}/></label><label className="field"><span>Vencimiento</span><input type="date" value={f.due_date} onChange={e=>setF({...f,due_date:e.target.value})}/></label><label className="field full"><span>Notas</span><textarea rows={3} value={f.notes} onChange={e=>setF({...f,notes:e.target.value})}/></label></div><div className="modal-note">Total factura: <b>{money(row.invoice_total_amount||row.amount)}</b>.</div><div className="modal-actions"><button className="ghost-button" onClick={close}>Cancelar</button><button className="primary-button" disabled={saving||!String(f.document_number).trim()} onClick={()=>submit({...f,due_date:f.due_date||null})}>{saving?'Guardando…':'Guardar cambios'}</button></div></div></div>\n}\n\n'''
    t=t[:idx]+block+t[idx:]
p.write_text(t,encoding='utf-8')

# css
p=ROOT/'front/app/globals.css'
t=p.read_text(encoding='utf-8')
if '/* FACTURAS MENU TRES PUNTOS */' not in t:
    t+='''\n\n/* FACTURAS MENU TRES PUNTOS */\n.invoice-row-menu{position:relative;display:inline-flex}\n.invoice-menu-popover{right:0;left:auto;min-width:130px;z-index:40}\n'''
p.write_text(t,encoding='utf-8')

print('OK: facturas editables y menú de tres puntos aplicado.')
