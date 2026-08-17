from pathlib import Path
ROOT=Path.cwd()

# ---------------- BACKEND OBRA ----------------
p=ROOT/'backend/app/routers/work_detail.py'
t=p.read_text(encoding='utf-8')
if 'class WorkInvoiceUpdate(BaseModel):' not in t:
    anchor='class WorkPaymentCreate(BaseModel):'
    if anchor not in t: raise SystemExit('ERROR: WorkPaymentCreate no encontrado')
    t=t.replace(anchor,'class WorkInvoiceUpdate(BaseModel):\n    document_number: str | None = None\n    description: str | None = None\n    issue_date: date | None = None\n    due_date: date | None = None\n    notes: str | None = None\n    amount: Decimal | None = None\n    vat_rate: Decimal | None = None\n\n\n@router.patch("/{work_id}/invoices/{invoice_id}")\ndef update_client_invoice(work_id: UUID, invoice_id: UUID, body: WorkInvoiceUpdate):\n    with db_cursor() as cur:\n        cur.execute(sql.SQL("""\n            SELECT * FROM {}.work_invoices\n            WHERE id=%s AND work_id=%s\n            FOR UPDATE\n        """).format(S), [invoice_id, work_id])\n        invoice = cur.fetchone()\n        if not invoice:\n            raise HTTPException(404, "Factura no encontrada")\n\n        new_amount = Decimal(str(body.amount)) if body.amount is not None else Decimal(str(invoice.get("total_amount") or 0))\n        if new_amount <= 0:\n            raise HTTPException(400, "El monto de la factura debe ser mayor a cero")\n\n        receivable_id = invoice.get("receivable_id")\n        paid = Decimal("0")\n        if receivable_id:\n            cur.execute(sql.SQL("""\n                SELECT COALESCE(SUM(amount),0) AS paid\n                FROM {}.financial_movements\n                WHERE receivable_id=%s AND type=\'ingreso\'\n            """).format(S), [receivable_id])\n            paid = Decimal(str(cur.fetchone()["paid"] or 0))\n            if new_amount < paid:\n                raise HTTPException(400, f"El monto no puede ser menor a lo ya cobrado ({paid})")\n\n        document_number = body.document_number if body.document_number is not None else invoice.get("invoice_number")\n        description = body.description if body.description is not None else invoice.get("description")\n        issue_date = body.issue_date or invoice.get("issue_date")\n        due_date = body.due_date\n        notes = body.notes if body.notes is not None else invoice.get("notes")\n\n        cur.execute(sql.SQL("""\n            UPDATE {}.work_invoices\n            SET invoice_number=%s,\n                description=%s,\n                issue_date=%s,\n                due_date=%s,\n                total_amount=%s,\n                notes=%s\n            WHERE id=%s\n            RETURNING *\n        """).format(S), [\n            document_number or None,\n            description,\n            issue_date,\n            due_date,\n            new_amount,\n            notes,\n            invoice_id,\n        ])\n        updated = cur.fetchone()\n\n        if receivable_id:\n            receivable_description = description or f"Factura de obra {document_number or \'\'}".strip()\n            new_status = "cobrado" if paid >= new_amount else ("parcial" if paid > 0 else "pendiente")\n            cur.execute(sql.SQL("""\n                UPDATE {}.receivables\n                SET document_number=%s,\n                    description=%s,\n                    issue_date=%s,\n                    due_date=%s,\n                    amount=%s,\n                    status=%s,\n                    notes=%s\n                WHERE id=%s AND work_id=%s\n            """).format(S), [\n                document_number or None,\n                receivable_description,\n                issue_date,\n                due_date,\n                new_amount,\n                new_status,\n                notes,\n                receivable_id,\n                work_id,\n            ])\n\n        return updated\n\n\n'+anchor,1)
p.write_text(t,encoding='utf-8')

# ---------------- BACKEND SERVICIO ----------------
p=ROOT/'backend/app/routers/service_detail.py'
t=p.read_text(encoding='utf-8')
if 'class ServiceInvoiceUpdate(BaseModel):' not in t:
    anchor='class ServicePaymentCreate(BaseModel):'
    if anchor not in t: raise SystemExit('ERROR: ServicePaymentCreate no encontrado')
    t=t.replace(anchor,'class ServiceInvoiceUpdate(BaseModel):\n    document_number: str | None = None\n    issue_date: date | None = None\n    due_date: date | None = None\n    notes: str | None = None\n\n\n@router.patch("/{service_id}/periods/{period_id}/invoice")\ndef update_period_invoice(service_id: UUID, period_id: UUID, body: ServiceInvoiceUpdate):\n    with db_cursor() as cur:\n        cur.execute(sql.SQL("""\n            SELECT sp.receivable_id, r.document_number, r.issue_date, r.due_date, r.notes\n            FROM {}.service_periods sp\n            JOIN {}.receivables r ON r.id=sp.receivable_id\n            WHERE sp.id=%s AND sp.service_id=%s\n            FOR UPDATE\n        """).format(S, S), [period_id, service_id])\n        row = cur.fetchone()\n        if not row:\n            raise HTTPException(404, "Factura del período no encontrada")\n\n        cur.execute(sql.SQL("""\n            UPDATE {}.receivables\n            SET document_number=%s,\n                issue_date=%s,\n                due_date=%s,\n                notes=%s\n            WHERE id=%s AND service_id=%s\n            RETURNING *\n        """).format(S), [\n            body.document_number if body.document_number is not None else row.get("document_number"),\n            body.issue_date or row.get("issue_date"),\n            body.due_date,\n            body.notes if body.notes is not None else row.get("notes"),\n            row["receivable_id"],\n            service_id,\n        ])\n        return cur.fetchone()\n\n\n'+anchor,1)
p.write_text(t,encoding='utf-8')

# ---------------- FRONTEND OBRA ----------------
p=ROOT/'front/src/components/WorkDetail.tsx'
t=p.read_text(encoding='utf-8')
old=' const [open,setOpen]=useState(false); const [upload,setUpload]=useState<any>(null);'
new=' const [open,setOpen]=useState(false); const [upload,setUpload]=useState<any>(null); const [editInvoice,setEditInvoice]=useState<any>(null); const [menuOpen,setMenuOpen]=useState<string|null>(null);'
start=t.find('function Invoices({workId,invoices,documents,reload}')
if start<0: raise SystemExit('ERROR: Invoices obra no encontrado')
idx=t.find(old,start)
if idx<0: raise SystemExit('ERROR: state Invoices obra no encontrado')
t=t[:idx]+new+t[idx+len(old):]
old=" const remove=async(r:any)=>{if(!confirm(`¿Eliminar la factura ${r.invoice_number||''}? Solo se permite si todavía no tiene cobros.`))return;"
new=" const remove=async(r:any)=>{setMenuOpen(null);if(!confirm(`¿Eliminar la factura ${r.invoice_number||''}? Solo se permite si todavía no tiene cobros.`))return;"
idx=t.find(old,start)
if idx<0: raise SystemExit('ERROR: remove obra no encontrado')
t=t[:idx]+new+t[idx+len(old):]
needle=' const view=async(id:string)=>'
idx=t.find(needle,start)
if idx<0: raise SystemExit('ERROR: view obra no encontrado')
save_edit=" const saveEdit=async(f:any)=>{await api.update(`works/${workId}/invoices`,editInvoice.id,f);setEditInvoice(null);setMenuOpen(null);await reload()};\n"
if 'const saveEdit=async(f:any)' not in t[start:idx]: t=t[:idx]+save_edit+t[idx:]
old='<td><button className="mini-button danger-text" onClick={()=>remove(r)}>Eliminar</button></td></tr>'
new='<td onClick={e=>e.stopPropagation()}><div className="invoice-row-menu"><button className="work-row-menu-button" aria-label="Opciones de factura" onClick={()=>setMenuOpen(menuOpen===r.id?null:r.id)}>⋯</button>{menuOpen===r.id&&<div className="work-row-menu-popover invoice-menu-popover"><button onClick={()=>{setMenuOpen(null);setEditInvoice(r)}}>Editar</button><button className="danger-text" onClick={()=>remove(r)}>Eliminar</button></div>}</div></td></tr>'
idx=t.find(old,start)
if idx<0: raise SystemExit('ERROR: botón Eliminar obra no encontrado')
t=t[:idx]+new+t[idx+len(old):]
old='{open&&<SimpleWorkInvoiceModal onClose={()=>setOpen(false)} onSave={save}/>} {upload&&<RelatedUploadModal'
new='{open&&<SimpleWorkInvoiceModal onClose={()=>setOpen(false)} onSave={save}/>} {editInvoice&&<WorkInvoiceEditModal invoice={editInvoice} onClose={()=>setEditInvoice(null)} onSave={saveEdit}/>} {upload&&<RelatedUploadModal'
idx=t.find(old,start)
if idx<0: raise SystemExit('ERROR: modal factura obra no encontrado')
t=t[:idx]+new+t[idx+len(old):]
anchor='function SimpleWorkInvoiceModal({onClose,onSave}'
idx=t.find(anchor,start)
if idx<0: raise SystemExit('ERROR: SimpleWorkInvoiceModal no encontrado')
if 'function WorkInvoiceEditModal(' not in t: t=t[:idx]+'function WorkInvoiceEditModal({invoice,onClose,onSave}:{invoice:any;onClose:()=>void;onSave:(x:any)=>Promise<void>}){\n const [f,setF]=useState<any>({document_number:invoice.invoice_number||\'\',description:invoice.description||\'\',issue_date:invoice.issue_date?String(invoice.issue_date).slice(0,10):\'\',due_date:invoice.due_date?String(invoice.due_date).slice(0,10):\'\',amount:String(invoice.total_amount||\'\'),notes:invoice.notes||\'\',vat_rate:21});\n const [saving,setSaving]=useState(false);\n const total=Number(f.amount||0);\n const vatRate=Number(f.vat_rate||0);\n const divisor=1+(vatRate/100);\n const net=divisor>0?total/divisor:total;\n const vat=total-net;\n const submit=async(e:any)=>{e.preventDefault();if(total<=0){alert(\'Ingresá un monto mayor a cero\');return}setSaving(true);try{await onSave({...f,amount:total,vat_rate:vatRate,due_date:f.due_date||null})}catch(x:any){alert(x.message)}finally{setSaving(false)}};\n return <div className="modal-backdrop"><div className="modal"><div className="modal-head"><div><span className="eyebrow">EDITAR FACTURA</span><h2>{invoice.invoice_number||\'Factura de obra\'}</h2><p>La factura sigue siendo independiente de los ítems.</p></div><button className="close-button" onClick={onClose}>×</button></div><form onSubmit={submit}><div className="form-grid"><label className="field"><span>Número de factura</span><input value={f.document_number} onChange={e=>setF({...f,document_number:e.target.value})}/></label><label className="field"><span>Concepto</span><input value={f.description} onChange={e=>setF({...f,description:e.target.value})}/></label><label className="field"><span>Fecha emisión</span><input type="date" value={f.issue_date} onChange={e=>setF({...f,issue_date:e.target.value})}/></label><label className="field"><span>Vencimiento</span><input type="date" value={f.due_date} onChange={e=>setF({...f,due_date:e.target.value})}/></label><label className="field"><span>Monto total (IVA incluido) *</span><input type="number" min="0.01" step="0.01" value={f.amount} onChange={e=>setF({...f,amount:e.target.value})}/></label><label className="field"><span>IVA</span><select value={f.vat_rate} onChange={e=>setF({...f,vat_rate:Number(e.target.value)})}><option value={0}>0%</option><option value={10.5}>10,5%</option><option value={21}>21%</option><option value={27}>27%</option></select></label><label className="field full"><span>Notas</span><textarea rows={3} value={f.notes} onChange={e=>setF({...f,notes:e.target.value})}/></label></div><div className="modal-note" style={{display:\'grid\',gap:6}}><div>Neto incluido: <b>{money(net)}</b></div><div>IVA incluido {vatRate}%: <b>{money(vat)}</b></div><div style={{fontSize:18}}>TOTAL FACTURA: <b>{money(total)}</b></div></div><div className="modal-actions"><button type="button" className="ghost-button" onClick={onClose}>Cancelar</button><button className="primary-button" disabled={saving||total<=0}>{saving?\'Guardando…\':\'Guardar cambios\'}</button></div></form></div></div>\n}\n\n'+t[idx:]
p.write_text(t,encoding='utf-8')

# ---------------- FRONTEND SERVICIO ----------------
p=ROOT/'front/src/components/ServiceDetail.tsx'
t=p.read_text(encoding='utf-8')
old=" const [invoicePeriod,setInvoicePeriod]=useState<any|null>(null); const [invoice,setInvoice]=useState({document_number:'',issue_date:today(),due_date:'',notes:'',vat_rate:21});"
new=" const [invoicePeriod,setInvoicePeriod]=useState<any|null>(null); const [invoice,setInvoice]=useState({document_number:'',issue_date:today(),due_date:'',notes:'',vat_rate:21}); const [editInvoice,setEditInvoice]=useState<any|null>(null); const [invoiceMenu,setInvoiceMenu]=useState<string|null>(null);"
if old in t: t=t.replace(old,new,1)
old="{tab==='billing'&&<Billing periods={periods} onInvoice="
new="{tab==='billing'&&<Billing periods={periods} menuOpen={invoiceMenu} setMenuOpen={setInvoiceMenu} onEdit={(p:any)=>{setInvoiceMenu(null);setEditInvoice(p)}} onInvoice="
if old in t: t=t.replace(old,new,1)
old='function Billing({periods,onInvoice,onUpload,onDelete,docs}:{periods:any[];onInvoice:(p:any)=>void;onUpload:(p:any)=>void;onDelete:(p:any)=>void;docs:any[]}){'
new='function Billing({periods,onInvoice,onEdit,onUpload,onDelete,docs,menuOpen,setMenuOpen}:{periods:any[];onInvoice:(p:any)=>void;onEdit:(p:any)=>void;onUpload:(p:any)=>void;onDelete:(p:any)=>void;docs:any[];menuOpen:string|null;setMenuOpen:(id:string|null)=>void}){'
if old in t: t=t.replace(old,new,1)
old='      <button className="mini-button" onClick={()=>onUpload(p)}>{hasPdf?\'Reemplazar / agregar PDF\':\'Subir factura PDF\'}</button>\n      {Number(p.paid_amount||0)<=0&&<button className="mini-button danger-text" onClick={()=>onDelete(p)}>Eliminar factura</button>}'
new='      <button className="mini-button" onClick={()=>onUpload(p)}>{hasPdf?\'Reemplazar / agregar PDF\':\'Subir factura PDF\'}</button>\n      <div className="invoice-row-menu"><button className="work-row-menu-button" aria-label="Opciones de factura" onClick={()=>setMenuOpen(menuOpen===p.id?null:p.id)}>⋯</button>{menuOpen===p.id&&<div className="work-row-menu-popover invoice-menu-popover"><button onClick={()=>onEdit(p)}>Editar</button>{Number(p.paid_amount||0)<=0&&<button className="danger-text" onClick={()=>onDelete(p)}>Eliminar</button>}</div>}</div>'
if old in t: t=t.replace(old,new,1)
needle='{payRow&&<PaymentModal'
idx=t.find(needle)
if idx>=0 and 'ServiceInvoiceEditModal row={editInvoice}' not in t:
    insert="{editInvoice&&<ServiceInvoiceEditModal row={editInvoice} saving={saving} close={()=>setEditInvoice(null)} submit={async(f:any)=>{setSaving(true);try{await api.update(`services/${serviceId}/periods/${editInvoice.id}`,\'invoice\',f);setEditInvoice(null);await load()}catch(e:any){alert(e.message)}finally{setSaving(false)}}}/>} \n  "
    t=t[:idx]+insert+t[idx:]
anchor='function PaymentModal({row,accounts,form,setForm,saving,close,submit}:any){'
idx=t.find(anchor)
if idx>=0 and 'function ServiceInvoiceEditModal(' not in t: t=t[:idx]+'function ServiceInvoiceEditModal({row,saving,close,submit}:any){\n const [f,setF]=useState<any>({document_number:row.document_number||\'\',issue_date:row.issue_date?String(row.issue_date).slice(0,10):today(),due_date:row.due_date?String(row.due_date).slice(0,10):\'\',notes:\'\'});\n return <div className="modal-backdrop"><div className="modal"><div className="modal-head"><div><span className="eyebrow">EDITAR FACTURA</span><h2>{row.document_number||`Mes ${row.period_number}`}</h2><p>El monto del período no se modifica.</p></div><button className="close-button" onClick={close}>×</button></div><div className="form-grid"><label className="field"><span>Número de factura *</span><input value={f.document_number} onChange={e=>setF({...f,document_number:e.target.value})}/></label><label className="field"><span>Fecha emisión</span><input type="date" value={f.issue_date} onChange={e=>setF({...f,issue_date:e.target.value})}/></label><label className="field"><span>Vencimiento</span><input type="date" value={f.due_date} onChange={e=>setF({...f,due_date:e.target.value})}/></label><label className="field full"><span>Notas</span><textarea rows={3} value={f.notes} onChange={e=>setF({...f,notes:e.target.value})}/></label></div><div className="modal-note">Total factura: <b>{money(row.invoice_total_amount||row.amount)}</b>.</div><div className="modal-actions"><button className="ghost-button" onClick={close}>Cancelar</button><button className="primary-button" disabled={saving||!String(f.document_number).trim()} onClick={()=>submit({...f,due_date:f.due_date||null})}>{saving?\'Guardando…\':\'Guardar cambios\'}</button></div></div></div>\n}\n\n'+t[idx:]
p.write_text(t,encoding='utf-8')

# CSS
p=ROOT/'front/app/globals.css'
t=p.read_text(encoding='utf-8')
if '/* FACTURA MENU COMPLETO */' not in t:
    t += '\n/* FACTURA MENU COMPLETO */\n.invoice-row-menu{position:relative;display:inline-flex}\n.invoice-menu-popover{right:0;left:auto;min-width:130px;z-index:50}\n'
p.write_text(t,encoding='utf-8')
print('OK: menú, edición y eliminación de facturas aplicado.')