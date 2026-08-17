'use client';

import { useEffect,useMemo,useState } from 'react';
import { api } from '@/src/lib/api';
import { Card,Empty,ErrorBox,Loading,SectionTitle,Status } from './ui';

const money=(v:any)=>`$ ${Number(v||0).toLocaleString('es-AR',{maximumFractionDigits:2})}`;
const dateAR=(v:any)=>v?new Date(`${String(v).slice(0,10)}T12:00:00`).toLocaleDateString('es-AR'):'—';

const RUBROS=[
 ['mano_obra','Mano de obra'],
 ['materiales','Materiales'],
 ['servicios','Servicios'],
 ['flota','Flota vehicular'],
 ['marketing','Marketing'],
 ['alquiler','Alquiler'],
 ['transporte','Transporte'],
 ['impuestos','Impuestos'],
 ['otros','Otros'],
];

export function FinancePayables(){
 const [rows,setRows]=useState<any[]|null>(null);
 const [suppliers,setSuppliers]=useState<any[]>([]);
 const [error,setError]=useState('');
 const [open,setOpen]=useState(false);
 const [query,setQuery]=useState('');

 const load=async()=>{
  try{
   const [p,s]=await Promise.all([
    api.list<any>('payables','?limit=500'),
    api.list<any>('suppliers','?limit=500')
   ]);
   setRows(p);
   setSuppliers(s.filter((x:any)=>x.is_active!==false));
   setError('');
  }catch(e:any){setError(e.message||String(e))}
 };
 useEffect(()=>{void load()},[]);

 const supplierMap=useMemo(()=>Object.fromEntries(suppliers.map((x:any)=>[x.id,x.name])),[suppliers]);

 const filtered=useMemo(()=>{
  if(!rows)return [];
  const q=query.trim().toLowerCase();
  return [...rows]
   .filter((r:any)=>!q||`${supplierMap[r.supplier_id]||''} ${r.description||''} ${r.document_number||''}`.toLowerCase().includes(q))
   .sort((a:any,b:any)=>{
    const ap=String(a.status||'')==='pagado';
    const bp=String(b.status||'')==='pagado';
    if(ap!==bp)return ap?1:-1;
    return String(a.due_date||'9999-12-31').localeCompare(String(b.due_date||'9999-12-31'));
   });
 },[rows,query,supplierMap]);

 if(error)return <ErrorBox message={error} onRetry={load}/>;
 if(!rows)return <Loading/>;

 const pending=rows.filter((x:any)=>String(x.status||'')!=='pagado'&&String(x.status||'')!=='anulado').reduce((a:number,x:any)=>a+Number(x.amount||0),0);
 const overdue=rows.filter((x:any)=>String(x.status||'')!=='pagado'&&x.due_date&&String(x.due_date).slice(0,10)<new Date().toISOString().slice(0,10)).reduce((a:number,x:any)=>a+Number(x.amount||0),0);

 const remove=async(r:any)=>{
  if(!confirm(`¿Eliminar la cuenta por pagar "${r.description||''}"?`))return;
  try{await api.remove('payables',r.id);await load()}catch(e:any){alert(e.message||String(e))}
 };

 return <div className="page-stack finance-payables-simple">
  <div className="kpi-grid three">
   <div className="card kpi"><span className="kpi-label">Pendiente</span><strong>{money(pending)}</strong><small>Cuentas todavía no pagadas</small></div>
   <div className="card kpi warn"><span className="kpi-label">Vencido</span><strong>{money(overdue)}</strong><small>Obligaciones fuera de término</small></div>
   <div className="card kpi"><span className="kpi-label">Registros</span><strong>{rows.length}</strong><small>Cuentas por pagar cargadas</small></div>
  </div>

  <Card>
   <SectionTitle
    title="Por pagar"
    subtitle="Obligaciones con proveedores y contratistas."
    action={<button className="primary-button" onClick={()=>setOpen(true)}>+ Nuevo</button>}
   />

   <div className="finance-payable-toolbar">
    <input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Buscar proveedor, concepto o factura…"/>
   </div>

   {filtered.length===0?<Empty text="Todavía no hay cuentas por pagar."/>:
   <div className="table-wrap">
    <table>
     <thead><tr><th>Proveedor</th><th>Rubro</th><th>Concepto</th><th>Fecha</th><th>Vencimiento</th><th>Factura</th><th>Monto</th><th>Estado</th><th></th></tr></thead>
     <tbody>{filtered.map((r:any)=>{
      const overdue=String(r.status||'')!=='pagado'&&r.due_date&&String(r.due_date).slice(0,10)<new Date().toISOString().slice(0,10);
      return <tr key={r.id}>
       <td><b>{supplierMap[r.supplier_id]||'—'}</b></td>
       <td>{String(r.category||'otros').replaceAll('_',' ')}</td>
       <td><b>{r.description||'—'}</b>{r.notes&&<small className="muted-line">{r.notes}</small>}</td>
       <td>{dateAR(r.issue_date)}</td>
       <td className={overdue?'danger-text':''}>{dateAR(r.due_date)}</td>
       <td>{r.document_number||'—'}</td>
       <td><b>{money(r.amount)}</b></td>
       <td><Status tone={String(r.status||'')==='pagado'?'green':overdue?'red':'yellow'}>{String(r.status||'pendiente')}</Status></td>
       <td><button className="mini-button danger-text" onClick={()=>remove(r)}>Eliminar</button></td>
      </tr>
     })}</tbody>
    </table>
   </div>}
  </Card>

  {open&&<PayableCostModal suppliers={suppliers} close={()=>setOpen(false)} done={async()=>{setOpen(false);await load()}}/>}
 </div>
}

function PayableCostModal({suppliers,close,done}:any){
 const today=new Date().toISOString().slice(0,10);
 const [saving,setSaving]=useState(false);
 const [f,setF]=useState<any>({
  issue_date:today,
  supplier_id:suppliers[0]?.id||'',
  category:'mano_obra',
  description:'',
  quantity:'1',
  unit:'',
  unit_price:'0',
  due_date:'',
  document_number:'',
 });

 const total=Number(f.quantity||0)*Number(f.unit_price||0);

 const save=async()=>{
  if(!f.supplier_id){alert('Seleccioná un proveedor / contratista.');return}
  if(!String(f.description||'').trim()){alert('Ingresá el concepto.');return}
  if(total<=0){alert('El importe debe ser mayor a cero.');return}

  setSaving(true);
  try{
   const detail=[
    Number(f.quantity||0)!==1||String(f.unit||'').trim()
      ? `${Number(f.quantity||0)} ${String(f.unit||'').trim()} × ${money(f.unit_price)}`
      : '',
   ].filter(Boolean).join(' · ');

   await api.create('payables',{
    supplier_id:f.supplier_id,
    description:String(f.description).trim(),
    document_number:String(f.document_number||'').trim()||null,
    issue_date:f.issue_date||null,
    due_date:f.due_date||null,
    amount:total,
    category:f.category||'otros',
    status:'pendiente',
    notes:detail||null,
   });

   await done();
  }catch(e:any){alert(e.message||String(e))}
  finally{setSaving(false)}
 };

 return <div className="modal-backdrop" onMouseDown={e=>{if(e.target===e.currentTarget)close()}}>
  <div className="modal finance-cost-modal">
   <div className="modal-head">
    <h2>Agregar costo</h2>
    <button className="close-button" onClick={close}>×</button>
   </div>

   <div className="form-grid">
    <label className="field"><span>Fecha</span><input type="date" value={f.issue_date} onChange={e=>setF({...f,issue_date:e.target.value})}/></label>

    <label className="field"><span>Proveedor / contratista</span>
     <select value={f.supplier_id} onChange={e=>setF({...f,supplier_id:e.target.value})}>
      <option value="">Seleccionar…</option>
      {suppliers.map((s:any)=><option key={s.id} value={s.id}>{s.name}</option>)}
     </select>
    </label>

    <label className="field"><span>Rubro</span>
     <select value={f.category} onChange={e=>setF({...f,category:e.target.value})}>
      {RUBROS.map(([v,l])=><option key={v} value={v}>{l}</option>)}
     </select>
    </label>

    <label className="field"><span>Concepto</span><input value={f.description} onChange={e=>setF({...f,description:e.target.value})}/></label>

    <label className="field"><span>Cantidad</span><input type="number" min="0" step="0.01" value={f.quantity} onChange={e=>setF({...f,quantity:e.target.value})}/></label>

    <label className="field"><span>Unidad</span><input value={f.unit} onChange={e=>setF({...f,unit:e.target.value})} placeholder="hora, unidad, servicio…"/></label>

    <label className="field"><span>Precio unitario</span><input type="number" min="0" step="0.01" value={f.unit_price} onChange={e=>setF({...f,unit_price:e.target.value})}/></label>

    <label className="field"><span>Vencimiento</span><input type="date" value={f.due_date} onChange={e=>setF({...f,due_date:e.target.value})}/></label>

    <label className="field"><span>Factura proveedor</span><input value={f.document_number} onChange={e=>setF({...f,document_number:e.target.value})}/></label>

    <div className="finance-cost-total">
     <span>Total</span>
     <strong>{money(total)}</strong>
    </div>
   </div>

   <div className="modal-actions">
    <button className="ghost-button" onClick={close}>Cancelar</button>
    <button className="primary-button" disabled={saving} onClick={save}>{saving?'Guardando…':'Guardar costo'}</button>
   </div>
  </div>
 </div>
}
