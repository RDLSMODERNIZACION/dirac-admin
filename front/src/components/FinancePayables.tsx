'use client';

import { useEffect,useMemo,useState } from 'react';
import { api } from '@/src/lib/api';
import { Card,Empty,ErrorBox,Loading,SectionTitle,Status } from './ui';

const money=(v:any)=>`$ ${Number(v||0).toLocaleString('es-AR',{maximumFractionDigits:2})}`;
const dateAR=(v:any)=>v?new Date(`${String(v).slice(0,10)}T12:00:00`).toLocaleDateString('es-AR'):'—';

const RUBROS=[
 ['mano_obra','Mano de obra'],['materiales','Materiales'],['servicios','Servicios'],
 ['flota','Flota vehicular'],['marketing','Marketing'],['alquiler','Alquiler'],
 ['transporte','Transporte'],['impuestos','Impuestos'],['otros','Otros'],
];

export function FinancePayables(){
 const [rows,setRows]=useState<any[]|null>(null);
 const [suppliers,setSuppliers]=useState<any[]>([]);
 const [works,setWorks]=useState<any[]>([]);
 const [accounts,setAccounts]=useState<any[]>([]);
 const [error,setError]=useState('');
 const [open,setOpen]=useState(false);
 const [pay,setPay]=useState<any|null>(null);
 const [upload,setUpload]=useState<any|null>(null);
 const [query,setQuery]=useState('');

 const load=async()=>{
  try{
   const [p,s,w,a]=await Promise.all([
    api.get<any[]>('/api/finance-payables'),
    api.list<any>('suppliers','?limit=500'),
    api.list<any>('works','?limit=500'),
    api.list<any>('accounts','?limit=500'),
   ]);
   setRows(p);
   setSuppliers(s.filter((x:any)=>x.is_active!==false));
   setWorks(w);
   setAccounts(a.filter((x:any)=>x.is_active!==false));
   setError('');
  }catch(e:any){setError(e.message||String(e))}
 };
 useEffect(()=>{void load()},[]);

 const filtered=useMemo(()=>{
  if(!rows)return [];
  const q=query.trim().toLowerCase();
  return rows.filter((r:any)=>!q||`${r.supplier_name||''} ${r.description||''} ${r.document_number||''} ${r.work_name||''} ${r.work_item_description||''}`.toLowerCase().includes(q));
 },[rows,query]);

 if(error)return <ErrorBox message={error} onRetry={load}/>;
 if(!rows)return <Loading/>;

 const pending=rows.reduce((a:number,x:any)=>a+Number(x.pending_amount||0),0);
 const today=new Date().toISOString().slice(0,10);
 const overdue=rows.filter((x:any)=>Number(x.pending_amount)>0&&x.due_date&&String(x.due_date).slice(0,10)<today).reduce((a:number,x:any)=>a+Number(x.pending_amount||0),0);

 const remove=async(r:any)=>{
  if(Number(r.paid_amount||0)>0){alert('No se puede eliminar desde acá porque ya tiene pagos registrados.');return}
  if(!confirm(`¿Eliminar "${r.description||''}"?`))return;
  try{await api.remove('payables',r.id);await load()}catch(e:any){alert(e.message||String(e))}
 };

 return <div className="page-stack finance-payables-simple">
  <div className="kpi-grid three">
   <div className="card kpi"><span className="kpi-label">Pendiente</span><strong>{money(pending)}</strong><small>Saldo aún no pagado</small></div>
   <div className="card kpi warn"><span className="kpi-label">Vencido</span><strong>{money(overdue)}</strong><small>Obligaciones fuera de término</small></div>
   <div className="card kpi"><span className="kpi-label">Registros</span><strong>{rows.length}</strong><small>Cuentas por pagar</small></div>
  </div>

  <Card>
   <SectionTitle title="Por pagar" subtitle="Costos y obligaciones con proveedores / contratistas." action={<button className="primary-button" onClick={()=>setOpen(true)}>+ Nuevo</button>}/>
   <div className="finance-payable-toolbar"><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Buscar proveedor, obra, ítem, concepto o factura…"/></div>

   {filtered.length===0?<Empty text="Todavía no hay cuentas por pagar."/>:<div className="table-wrap"><table>
    <thead><tr><th>Proveedor</th><th>Obra / Ítem</th><th>Concepto</th><th>Vence</th><th>Total</th><th>Pagado</th><th>Saldo</th><th>Estado</th><th>Acciones</th></tr></thead>
    <tbody>{filtered.map((r:any)=>{
     const isOverdue=Number(r.pending_amount)>0&&r.due_date&&String(r.due_date).slice(0,10)<today;
     return <tr key={r.id}>
      <td><b>{r.supplier_name||'—'}</b><small className="muted-line">{String(r.category||'').replaceAll('_',' ')}</small></td>
      <td><b>{r.work_name||'General'}</b>{r.work_item_description&&<small className="muted-line">{r.work_item_description}</small>}</td>
      <td><b>{r.description||'—'}</b><small className="muted-line">{r.document_number||''}</small></td>
      <td className={isOverdue?'danger-text':''}>{dateAR(r.due_date)}</td>
      <td>{money(r.amount)}</td><td>{money(r.paid_amount)}</td><td><b>{money(r.pending_amount)}</b></td>
      <td><Status tone={r.effective_status==='pagado'?'green':isOverdue?'red':r.effective_status==='parcial'?'blue':'yellow'}>{r.effective_status}</Status></td>
      <td><div className="row-actions">{Number(r.pending_amount)>0&&<button className="mini-button" onClick={()=>setPay(r)}>Pagar</button>}{Number(r.paid_amount||0)<=0&&<button className="mini-button danger-text" onClick={()=>remove(r)}>Eliminar</button>}</div></td>
     </tr>
    })}</tbody>
   </table></div>}
  </Card>

  {open&&<PayableCostModal suppliers={suppliers} works={works} close={()=>setOpen(false)} done={async()=>{setOpen(false);await load()}}/>}
  {pay&&<PayModal row={pay} accounts={accounts} close={()=>setPay(null)} done={async(result:any)=>{setPay(null);await load();if(result?.movement?.id&&result?.work_id)setUpload({movement_id:result.movement.id,work_id:result.work_id,title:`Comprobante pago ${pay.document_number||pay.description||''}`})}}/>}
  {upload&&<ReceiptUpload data={upload} close={()=>setUpload(null)} done={()=>setUpload(null)}/>}
 </div>
}

function PayableCostModal({suppliers,works,close,done}:any){
 const today=new Date().toISOString().slice(0,10);
 const [items,setItems]=useState<any[]>([]);
 const [saving,setSaving]=useState(false);
 const [f,setF]=useState<any>({issue_date:today,supplier_id:suppliers[0]?.id||'',work_id:'',work_item_id:'',category:'mano_obra',description:'',quantity:'1',unit:'',unit_price:'0',due_date:'',document_number:''});

 useEffect(()=>{
  if(!f.work_id){setItems([]);return}
  api.list<any>('work_items',`?limit=500&work_id=${f.work_id}`).then(x=>setItems(x.filter((i:any)=>i.status!=='cancelado'))).catch(()=>setItems([]));
 },[f.work_id]);

 const total=Number(f.quantity||0)*Number(f.unit_price||0);

 const save=async()=>{
  if(!f.supplier_id){alert('Seleccioná un proveedor / contratista.');return}
  if(!String(f.description||'').trim()){alert('Ingresá el concepto.');return}
  if(total<=0){alert('El importe debe ser mayor a cero.');return}
  setSaving(true);
  try{
   const detail=(Number(f.quantity||0)!==1||String(f.unit||'').trim())?`${Number(f.quantity||0)} ${String(f.unit||'').trim()} × ${money(f.unit_price)}`:null;
   await api.post('/api/finance-payables',{
    supplier_id:f.supplier_id,
    work_id:f.work_id||null,
    work_item_id:f.work_item_id||null,
    description:String(f.description).trim(),
    document_number:String(f.document_number||'').trim()||null,
    issue_date:f.issue_date||null,
    due_date:f.due_date||null,
    amount:total,
    category:f.category||'otros',
    notes:detail,
   });
   await done();
  }catch(e:any){alert(e.message||String(e))}finally{setSaving(false)}
 };

 return <div className="modal-backdrop" onMouseDown={e=>{if(e.target===e.currentTarget)close()}}><div className="modal finance-cost-modal">
  <div className="modal-head"><h2>Agregar costo</h2><button className="close-button" onClick={close}>×</button></div>
  <div className="form-grid">
   <label className="field"><span>Fecha</span><input type="date" value={f.issue_date} onChange={e=>setF({...f,issue_date:e.target.value})}/></label>
   <label className="field"><span>Proveedor / contratista</span><select value={f.supplier_id} onChange={e=>setF({...f,supplier_id:e.target.value})}><option value="">Seleccionar…</option>{suppliers.map((s:any)=><option key={s.id} value={s.id}>{s.name}</option>)}</select></label>

   <label className="field"><span>Obra</span><select value={f.work_id} onChange={e=>setF({...f,work_id:e.target.value,work_item_id:''})}><option value="">General / sin obra</option>{works.map((w:any)=><option key={w.id} value={w.id}>{w.name}</option>)}</select></label>
   <label className="field"><span>Ítem de obra</span><select disabled={!f.work_id} value={f.work_item_id} onChange={e=>setF({...f,work_item_id:e.target.value})}><option value="">Sin ítem específico</option>{items.map((i:any)=><option key={i.id} value={i.id}>{i.description}</option>)}</select></label>

   <label className="field"><span>Rubro</span><select value={f.category} onChange={e=>setF({...f,category:e.target.value})}>{RUBROS.map(([v,l])=><option key={v} value={v}>{l}</option>)}</select></label>
   <label className="field"><span>Concepto</span><input value={f.description} onChange={e=>setF({...f,description:e.target.value})}/></label>
   <label className="field"><span>Cantidad</span><input type="number" min="0" step="0.01" value={f.quantity} onChange={e=>setF({...f,quantity:e.target.value})}/></label>
   <label className="field"><span>Unidad</span><input value={f.unit} onChange={e=>setF({...f,unit:e.target.value})} placeholder="hora, unidad, servicio…"/></label>
   <label className="field"><span>Precio unitario</span><input type="number" min="0" step="0.01" value={f.unit_price} onChange={e=>setF({...f,unit_price:e.target.value})}/></label>
   <label className="field"><span>Vencimiento</span><input type="date" value={f.due_date} onChange={e=>setF({...f,due_date:e.target.value})}/></label>
   <label className="field"><span>Factura proveedor</span><input value={f.document_number} onChange={e=>setF({...f,document_number:e.target.value})}/></label>
   <div className="finance-cost-total"><span>Total</span><strong>{money(total)}</strong></div>
  </div>
  <div className="modal-actions"><button className="ghost-button" onClick={close}>Cancelar</button><button className="primary-button" disabled={saving} onClick={save}>{saving?'Guardando…':'Guardar costo'}</button></div>
 </div></div>
}

function PayModal({row,accounts,close,done}:any){
 const [saving,setSaving]=useState(false);
 const [f,setF]=useState<any>({account_id:accounts[0]?.id||'',amount:String(row.pending_amount||''),payment_date:new Date().toISOString().slice(0,10),notes:''});
 const save=async()=>{
  if(!f.account_id){alert('Seleccioná la cuenta desde donde se paga.');return}
  const amount=Number(f.amount||0);
  if(amount<=0||amount>Number(row.pending_amount)){alert('Revisá el monto del pago.');return}
  setSaving(true);
  try{
   const result=await api.post<any>(`/api/finance-payables/${row.id}/payments`,{account_id:f.account_id,amount,payment_date:f.payment_date,notes:f.notes||null});
   await done(result);
  }catch(e:any){alert(e.message||String(e))}finally{setSaving(false)}
 };
 return <div className="modal-backdrop"><div className="modal" style={{width:'min(650px,96vw)'}}>
  <div className="modal-head"><div><span className="eyebrow">REGISTRAR PAGO</span><h2>{row.supplier_name}</h2></div><button className="close-button" onClick={close}>×</button></div>
  <div className="modal-note">Saldo pendiente: <b>{money(row.pending_amount)}</b>. El pago se registra como egreso real y se descuenta de la cuenta seleccionada.</div>
  <div className="form-grid">
   <label className="field"><span>Cuenta *</span><select value={f.account_id} onChange={e=>setF({...f,account_id:e.target.value})}><option value="">Seleccionar…</option>{accounts.map((a:any)=><option key={a.id} value={a.id}>{a.name} · {a.currency}</option>)}</select></label>
   <label className="field"><span>Monto</span><input type="number" min="0.01" max={Number(row.pending_amount)} step="0.01" value={f.amount} onChange={e=>setF({...f,amount:e.target.value})}/></label>
   <label className="field"><span>Fecha</span><input type="date" value={f.payment_date} onChange={e=>setF({...f,payment_date:e.target.value})}/></label>
   <label className="field"><span>Notas</span><input value={f.notes} onChange={e=>setF({...f,notes:e.target.value})}/></label>
  </div>
  {!row.work_id&&<div className="modal-note" style={{marginTop:12}}>Este costo no está asociado a una obra, por lo que el pago se registrará normalmente pero no se podrá adjuntar el comprobante dentro de Documentación de obra desde este flujo.</div>}
  <div className="modal-actions"><button className="ghost-button" onClick={close}>Cancelar</button><button className="primary-button" disabled={saving} onClick={save}>{saving?'Registrando…':'Pagar'}</button></div>
 </div></div>
}

function ReceiptUpload({data,close,done}:any){
 const [file,setFile]=useState<File|null>(null);
 const [saving,setSaving]=useState(false);
 const upload=async()=>{
  if(!file)return;
  setSaving(true);
  try{
   const fd=new FormData();
   fd.append('work_id',data.work_id);
   fd.append('document_type','comprobante_pago');
   fd.append('title',data.title||'Comprobante de pago');
   fd.append('related_type','financial_movement');
   fd.append('related_id',data.movement_id);
   fd.append('file',file);
   await api.upload('/api/work-documents/upload',fd);
   done();
  }catch(e:any){alert(e.message||String(e))}finally{setSaving(false)}
 };
 return <div className="modal-backdrop"><div className="modal" style={{width:'min(620px,96vw)'}}>
  <div className="modal-head"><div><span className="eyebrow">PAGO REGISTRADO</span><h2>Subir comprobante</h2></div><button className="close-button" onClick={close}>×</button></div>
  <div className="modal-note">El dinero ya fue debitado de la cuenta. Ahora podés asociar el comprobante PDF a este pago.</div>
  <label className="field"><span>Comprobante PDF</span><input type="file" accept="application/pdf,.pdf" onChange={e=>setFile(e.target.files?.[0]||null)}/></label>
  <div className="modal-actions"><button className="ghost-button" onClick={close}>Omitir por ahora</button><button className="primary-button" disabled={!file||saving} onClick={upload}>{saving?'Subiendo…':'Subir comprobante'}</button></div>
 </div></div>
}
