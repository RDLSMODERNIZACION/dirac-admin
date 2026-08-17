'use client';

import { useEffect,useMemo,useState } from 'react';
import { api } from '@/src/lib/api';
import { Card,Empty,ErrorBox,Loading,SectionTitle,Status } from './ui';

const money=(v:any)=>`$ ${Math.round(Number(v||0)).toLocaleString('es-AR')}`;
const dateAR=(v:any)=>v?new Date(`${String(v).slice(0,10)}T12:00:00`).toLocaleDateString('es-AR'):'—';

const groups:any={
 flota_vehicular:'Flota vehicular',
 marketing:'Marketing',
 contratistas:'Contratistas',
};

function Risk({level,reason}:{level:string;reason?:string}){
 const tone=level==='alto'?'red':level==='medio'?'yellow':'green';
 return <div className="supplier-risk"><Status tone={tone as any}>{level==='alto'?'Alto':level==='medio'?'Medio':'Bajo'}</Status>{reason&&<small>{reason}</small>}</div>
}

export function SupplierAnalytics(){
 const [data,setData]=useState<any|null>(null);
 const [group,setGroup]=useState('todos');
 const [query,setQuery]=useState('');
 const [selected,setSelected]=useState<any|null>(null);
 const [edit,setEdit]=useState<any|null>(null);
 const [creating,setCreating]=useState(false);
 const [error,setError]=useState('');

 const load=async()=>{try{setData(await api.get<any>('/api/supplier-insights'));setError('')}catch(e:any){setError(e.message||String(e))}};
 useEffect(()=>{void load()},[]);

 const filtered=useMemo(()=>{
  if(!data)return [];
  const q=query.trim().toLowerCase();
  return data.suppliers.filter((r:any)=>{
   if(group!=='todos'&&r.supplier_group!==group)return false;
   return !q||`${r.name} ${r.contact_name||''} ${r.tax_id||''}`.toLowerCase().includes(q);
  });
 },[data,group,query]);

 const grouped=useMemo(()=>{
  const out:any={flota_vehicular:[],marketing:[],contratistas:[]};
  filtered.forEach((r:any)=>(out[r.supplier_group]||out.contratistas).push(r));
  return out;
 },[filtered]);

 if(error)return <ErrorBox message={error} onRetry={load}/>;
 if(!data)return <Loading/>;

 const s=data.summary;

 return <div className="page-stack supplier-exec">
  <SectionTitle title="Proveedores y contratistas" subtitle="Cartera de proveedores agrupada, obligaciones y pagos." action={<button className="primary-button" onClick={()=>setCreating(true)}>+ Nuevo</button>}/>

  <Card>
   <div className="supplier-summary-table">
    <SummaryCell label="Activos" value={s.active}/>
    <SummaryCell label="Flota vehicular" value={s.flota_vehicular}/>
    <SummaryCell label="Marketing" value={s.marketing}/>
    <SummaryCell label="Contratistas" value={s.contratistas}/>
    <SummaryCell label="Pendiente" value={money(s.pending)} warn={Number(s.pending)>0}/>
    <SummaryCell label="Vencido" value={money(s.overdue)} danger={Number(s.overdue)>0}/>
    <SummaryCell label="Pagado este mes" value={money(s.paid_this_month)}/>
   </div>
  </Card>

  <Card>
   <div className="supplier-toolbar">
    <div className="supplier-group-tabs">
     {[['todos','Todos'],['flota_vehicular','Flota vehicular'],['marketing','Marketing'],['contratistas','Contratistas']].map(([id,l])=><button key={id} className={group===id?'active':''} onClick={()=>setGroup(id)}>{l}</button>)}
    </div>
    <input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Buscar proveedor, contacto o CUIT…"/>
   </div>

   {filtered.length===0?<Empty text="No hay proveedores en este grupo."/>:
    group==='todos'
      ?<div className="supplier-groups">{(['flota_vehicular','marketing','contratistas'] as string[]).map(g=>grouped[g].length?<SupplierGroup key={g} name={groups[g]} rows={grouped[g]} onSelect={setSelected}/>:null)}</div>
      :<SupplierTable rows={filtered} onSelect={setSelected}/>
   }
  </Card>

  {selected&&<SupplierDrawer supplier={selected} close={()=>setSelected(null)} edit={()=>{setEdit(selected);setSelected(null)}} reload={async()=>{await load();setSelected(null)}}/>}
  {(creating||edit)&&<SupplierModal initial={edit} close={()=>{setCreating(false);setEdit(null)}} done={async()=>{setCreating(false);setEdit(null);await load()}}/>}
 </div>
}

function SummaryCell({label,value,warn,danger}:any){return <div className={`${warn?'warn ':''}${danger?'danger':''}`}><span>{label}</span><b>{value}</b></div>}

function SupplierGroup({name,rows,onSelect}:any){
 return <section className="supplier-group-block">
  <div className="supplier-group-head"><h3>{name}</h3><span>{rows.length} {rows.length===1?'registro':'registros'}</span></div>
  <SupplierTable rows={rows} onSelect={onSelect}/>
 </section>
}

function SupplierTable({rows,onSelect}:any){
 return <div className="table-wrap"><table className="supplier-exec-table">
  <thead><tr><th>Proveedor</th><th>Grupo</th><th>Pendiente</th><th>Vencido</th><th>Último pago</th><th>Estado</th><th>Riesgo</th></tr></thead>
  <tbody>{rows.map((r:any)=><tr key={r.id} className="clickable-row" onClick={()=>onSelect(r)}>
   <td><b>{r.name}</b><small>{r.contact_name||r.tax_id||'Sin datos de contacto'}</small></td>
   <td><span className={`supplier-group-pill ${r.supplier_group}`}>{groups[r.supplier_group]||'Contratistas'}</span></td>
   <td className={Number(r.pending)>0?'pending-money':''}><b>{money(r.pending)}</b></td>
   <td className={Number(r.overdue)>0?'danger-text':''}><b>{money(r.overdue)}</b>{Number(r.max_overdue_days)>0&&<small>{r.max_overdue_days} días</small>}</td>
   <td>{dateAR(r.last_payment_date)}</td>
   <td><Status tone={r.is_active!==false?'green':'gray'}>{r.is_active!==false?'Activo':'Inactivo'}</Status></td>
   <td><Risk level={r.risk_level} reason={r.risk_reason}/></td>
  </tr>)}</tbody>
 </table></div>
}

function SupplierDrawer({supplier,close,edit,reload}:any){
 const [d,setD]=useState<any|null>(null);
 const [tab,setTab]=useState<'summary'|'payables'|'payments'|'documents'>('summary');
 const [docOpen,setDocOpen]=useState(false);
 const [error,setError]=useState('');

 const load=async()=>{try{setD(await api.get<any>(`/api/supplier-insights/${supplier.id}`));setError('')}catch(e:any){setError(e.message||String(e))}};
 useEffect(()=>{void load()},[supplier.id]);

 const remove=async()=>{
  if(!confirm(`¿Eliminar "${supplier.name}"?`))return;
  try{await api.remove('supplier-insights',supplier.id);await reload()}catch(e:any){alert(e.message||String(e))}
 };

 return <div className="supplier-drawer-bg" onMouseDown={e=>{if(e.target===e.currentTarget)close()}}>
  <aside className="supplier-drawer">
   <div className="supplier-drawer-head">
    <div><span className="eyebrow">{groups[supplier.supplier_group]||'PROVEEDOR'}</span><h2>{supplier.name}</h2><p>{supplier.contact_name||'Sin contacto'} · {supplier.tax_id||'Sin CUIT'}</p></div>
    <button className="close-button" onClick={close}>×</button>
   </div>
   <div className="supplier-drawer-actions"><button className="primary-button" onClick={edit}>Editar</button><button className="ghost-button danger-text" onClick={remove}>Eliminar</button></div>

   {error?<ErrorBox message={error}/>:!d?<Loading/>:<>
    <div className="supplier-drawer-kpis">
     <Mini l="Pendiente" v={money(supplier.pending)}/>
     <Mini l="Vencido" v={money(supplier.overdue)} danger={Number(supplier.overdue)>0}/>
     <Mini l="Pagado histórico" v={money(supplier.paid_total)}/>
     <Mini l="Último pago" v={dateAR(supplier.last_payment_date)}/>
    </div>

    <div className="supplier-drawer-tabs">
     {[['summary','Resumen'],['payables','Cuentas por pagar'],['payments','Pagos'],['documents','Documentación']].map(([id,l])=><button key={id} className={tab===id?'active':''} onClick={()=>setTab(id as any)}>{l}</button>)}
    </div>

    {tab==='summary'&&<div className="supplier-summary-detail">
     <div className="supplier-detail-grid">
      <Mini l="Grupo" v={groups[supplier.supplier_group]}/>
      <Mini l="Estado" v={supplier.is_active!==false?'Activo':'Inactivo'}/>
      <Mini l="Riesgo" v={supplier.risk_level}/>
      <Mini l="Pagado este mes" v={money(supplier.paid_this_month)}/>
     </div>
     <section><h4>Contacto</h4><p>{supplier.contact_name||'—'}<br/>{supplier.email||'—'}<br/>{supplier.phone||'—'}<br/>{supplier.address||'—'}</p></section>
     {supplier.notes&&<section><h4>Notas</h4><p>{supplier.notes}</p></section>}
    </div>}

    {tab==='payables'&&<SimpleTable rows={d.payables} cols={[['document_number','Documento'],['description','Concepto'],['due_date','Vence'],['amount','Total'],['paid','Pagado'],['pending','Saldo']]}/>}
    {tab==='payments'&&<SimpleTable rows={d.payments} cols={[['movement_date','Fecha'],['description','Concepto'],['document_number','Documento'],['amount','Monto']]}/>}
    {tab==='documents'&&<div>
      <div className="supplier-doc-head"><h4>Documentación</h4><button className="primary-button" onClick={()=>setDocOpen(true)}>+ Documento</button></div>
      {d.documents?.length?<div className="supplier-doc-list">{d.documents.map((x:any)=><div key={x.id}><div><b>{x.title}</b><span>{x.document_type} · {dateAR(x.document_date)}</span>{x.notes&&<small>{x.notes}</small>}</div><div className="row-actions">{x.url&&<button className="mini-button" onClick={()=>window.open(x.url,'_blank')}>Abrir</button>}<button className="mini-button danger-text" onClick={async()=>{if(confirm('¿Eliminar documento?')){try{await api.remove('supplier-insights/documents',x.id);await load()}catch(e:any){alert(e.message)}}}}>Eliminar</button></div></div>)}</div>:<Empty text="Todavía no hay documentación registrada."/>}
      {docOpen&&<DocumentModal supplierId={supplier.id} close={()=>setDocOpen(false)} done={async()=>{setDocOpen(false);await load()}}/>}
    </div>}
   </>}
  </aside>
 </div>
}

function Mini({l,v,danger}:any){return <div className={danger?'danger':''}><span>{l}</span><b>{v??'—'}</b></div>}

function SimpleTable({rows,cols}:any){
 if(!rows?.length)return <Empty text="Sin registros."/>;
 return <div className="table-wrap"><table><thead><tr>{cols.map((c:any)=><th key={c[0]}>{c[1]}</th>)}</tr></thead><tbody>{rows.map((r:any,i:number)=><tr key={r.id||i}>{cols.map(([k]:any)=><td key={k}>{['amount','paid','pending'].includes(k)?money(r[k]):k.includes('date')?dateAR(r[k]):r[k]||'—'}</td>)}</tr>)}</tbody></table></div>
}

function SupplierModal({initial,close,done}:any){
 const [saving,setSaving]=useState(false);
 const [f,setF]=useState<any>({
  name:initial?.name||'',supplier_group:initial?.supplier_group||'contratistas',
  tax_id:initial?.tax_id||'',type:initial?.type||'proveedor',
  contact_name:initial?.contact_name||'',email:initial?.email||'',phone:initial?.phone||'',
  address:initial?.address||'',notes:initial?.notes||'',is_active:initial?.is_active!==false
 });

 const save=async()=>{
  if(!String(f.name).trim())return;
  setSaving(true);
  try{
   if(initial)await api.update('supplier-insights',initial.id,f);
   else await api.post('/api/supplier-insights',f);
   await done();
  }catch(e:any){alert(e.message||String(e))}finally{setSaving(false)}
 };

 return <div className="modal-backdrop"><div className="modal">
  <div className="modal-head"><div><span className="eyebrow">{initial?'EDITAR':'NUEVO'}</span><h2>{initial?'Editar proveedor':'Nuevo proveedor'}</h2></div><button className="close-button" onClick={close}>×</button></div>
  <div className="form-grid">
   <label className="field full"><span>Nombre / razón social *</span><input value={f.name} onChange={e=>setF({...f,name:e.target.value})}/></label>
   <label className="field"><span>Grupo *</span><select value={f.supplier_group} onChange={e=>setF({...f,supplier_group:e.target.value})}><option value="flota_vehicular">Flota vehicular</option><option value="marketing">Marketing</option><option value="contratistas">Contratistas</option></select></label>
   <label className="field"><span>Tipo</span><select value={f.type} onChange={e=>setF({...f,type:e.target.value})}><option value="proveedor">Proveedor</option><option value="contratista">Contratista</option><option value="ambos">Ambos</option></select></label>
   <label className="field"><span>CUIT</span><input value={f.tax_id} onChange={e=>setF({...f,tax_id:e.target.value})}/></label>
   <label className="field"><span>Contacto</span><input value={f.contact_name} onChange={e=>setF({...f,contact_name:e.target.value})}/></label>
   <label className="field"><span>Email</span><input value={f.email} onChange={e=>setF({...f,email:e.target.value})}/></label>
   <label className="field"><span>Teléfono</span><input value={f.phone} onChange={e=>setF({...f,phone:e.target.value})}/></label>
   <label className="field full"><span>Dirección</span><input value={f.address} onChange={e=>setF({...f,address:e.target.value})}/></label>
   <label className="field full"><span>Notas</span><textarea rows={3} value={f.notes} onChange={e=>setF({...f,notes:e.target.value})}/></label>
   <label className="field"><span>Activo</span><input type="checkbox" checked={f.is_active} onChange={e=>setF({...f,is_active:e.target.checked})}/></label>
  </div>
  <div className="modal-actions"><button className="ghost-button" onClick={close}>Cancelar</button><button className="primary-button" disabled={saving||!String(f.name).trim()} onClick={save}>{saving?'Guardando…':'Guardar'}</button></div>
 </div></div>
}

function DocumentModal({supplierId,close,done}:any){
 const [saving,setSaving]=useState(false);
 const [f,setF]=useState<any>({document_type:'factura',title:'',document_date:'',url:'',notes:''});
 const save=async()=>{if(!f.title.trim())return;setSaving(true);try{await api.post(`/api/supplier-insights/${supplierId}/documents`,{...f,document_date:f.document_date||null,url:f.url||null});await done()}catch(e:any){alert(e.message||String(e))}finally{setSaving(false)}};
 return <div className="modal-backdrop"><div className="modal" style={{width:'min(650px,96vw)'}}>
  <div className="modal-head"><div><span className="eyebrow">DOCUMENTACIÓN</span><h2>Registrar documento</h2></div><button className="close-button" onClick={close}>×</button></div>
  <div className="form-grid">
   <label className="field"><span>Tipo</span><select value={f.document_type} onChange={e=>setF({...f,document_type:e.target.value})}><option value="factura">Factura</option><option value="presupuesto">Presupuesto</option><option value="contrato">Contrato / acuerdo</option><option value="fiscal">Fiscal</option><option value="otro">Otro</option></select></label>
   <label className="field"><span>Fecha</span><input type="date" value={f.document_date} onChange={e=>setF({...f,document_date:e.target.value})}/></label>
   <label className="field full"><span>Título *</span><input value={f.title} onChange={e=>setF({...f,title:e.target.value})}/></label>
   <label className="field full"><span>URL / enlace</span><input value={f.url} onChange={e=>setF({...f,url:e.target.value})} placeholder="https://..."/></label>
   <label className="field full"><span>Notas</span><textarea rows={2} value={f.notes} onChange={e=>setF({...f,notes:e.target.value})}/></label>
  </div>
  <div className="modal-actions"><button className="ghost-button" onClick={close}>Cancelar</button><button className="primary-button" disabled={saving||!f.title.trim()} onClick={save}>{saving?'Guardando…':'Guardar'}</button></div>
 </div></div>
}
