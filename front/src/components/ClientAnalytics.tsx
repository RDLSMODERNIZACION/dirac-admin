'use client';

import { useEffect,useMemo,useState } from 'react';
import { api } from '@/src/lib/api';
import { Card, Empty, ErrorBox, Loading, SectionTitle, Status } from './ui';

const money=(v:any)=>`$ ${Math.round(Number(v||0)).toLocaleString('es-AR')}`;
const dateAR=(v:any)=>v?new Date(`${String(v).slice(0,10)}T12:00:00`).toLocaleDateString('es-AR'):'—';
const pct=(v:any)=>`${Number(v||0).toFixed(1)}%`;

function Risk({level,reasons}:{level:string;reasons?:string[]}){
 const tone=level==='alto'?'red':level==='medio'?'yellow':'green';
 return <div className="client-risk"><Status tone={tone as any}>{level==='alto'?'Alto':level==='medio'?'Medio':'Bajo'}</Status>{reasons?.[0]&&<small>{reasons[0]}</small>}</div>
}

export function ClientAnalytics(){
 const [data,setData]=useState<any|null>(null);
 const [query,setQuery]=useState('');
 const [sort,setSort]=useState<'risk'|'billing'|'pending'|'overdue'>('risk');
 const [selected,setSelected]=useState<any|null>(null);
 const [editing,setEditing]=useState<any|null>(null);
 const [creating,setCreating]=useState(false);
 const [menuOpen,setMenuOpen]=useState<string|null>(null);
 const [error,setError]=useState('');

 const load=async()=>{try{setData(await api.get<any>('/api/client-insights'));setError('')}catch(e:any){setError(e.message||String(e))}};
 useEffect(()=>{void load()},[]);

 const rows=useMemo(()=>{
  if(!data)return [];
  const q=query.trim().toLowerCase();
  const rank:any={alto:0,medio:1,bajo:2};
  return [...data.clients].filter((r:any)=>!q||`${r.name} ${r.tax_id||''} ${r.contact_name||''}`.toLowerCase().includes(q)).sort((a:any,b:any)=>{
   if(sort==='billing')return Number(b.invoiced)-Number(a.invoiced);
   if(sort==='pending')return Number(b.pending)-Number(a.pending);
   if(sort==='overdue')return Number(b.overdue)-Number(a.overdue);
   const d=(rank[a.risk_level]??9)-(rank[b.risk_level]??9);return d||Number(b.overdue)-Number(a.overdue);
  });
 },[data,query,sort]);

 if(error)return <ErrorBox message={error} onRetry={load}/>;
 if(!data)return <Loading/>;
 const s=data.summary;
 const topClients=[...data.clients].sort((a:any,b:any)=>Number(b.invoiced)-Number(a.invoiced)).slice(0,5);
 const maxBilling=Math.max(1,...topClients.map((x:any)=>Number(x.invoiced||0)));

 const remove=async(r:any)=>{
  setMenuOpen(null);
  if(!confirm(`¿Eliminar el cliente "${r.name}"?`))return;
  try{await api.remove('clients',r.id);await load()}catch(e:any){alert(e.message||String(e))}
 };

 return <div className="page-stack clients-exec">
  <SectionTitle title="Clientes" subtitle="Cartera comercial, facturación, cobranza, concentración y riesgo." action={<button className="primary-button" onClick={()=>setCreating(true)}>+ Nuevo cliente</button>}/>

  <div className="client-kpis">
   <Metric label="Clientes activos" value={String(s.active_clients)} sub={`de ${s.total_clients} totales`}/>
   <Metric label="Facturación acumulada" value={money(s.invoiced)} sub={`Cobrado ${money(s.collected)}`} tone="blue"/>
   <Metric label="Pendiente de cobro" value={money(s.pending)} sub="facturado no cobrado" tone="amber"/>
   <Metric label="Vencido" value={money(s.overdue)} sub={`${s.high_risk_clients} clientes en riesgo alto`} tone="red"/>
  </div>

  <div className="client-kpis secondary">
   <Metric label="Ticket promedio" value={money(s.avg_ticket)} sub="por cliente con facturación"/>
   <Metric label="Concentración Top 3" value={pct(s.top3_concentration)} sub="de la facturación total" tone={Number(s.top3_concentration)>=70?'red':'amber'}/>
   <Metric label="Días promedio de cobro" value={`${Math.round(Number(s.avg_collection_days||0))} días`} sub="desde emisión a último cobro"/>
   <Metric label="Clientes riesgo alto" value={String(s.high_risk_clients)} sub="requieren seguimiento" tone={Number(s.high_risk_clients)>0?'red':undefined}/>
  </div>

  <div className="client-chart-grid">
   <Card>
    <SectionTitle title="Facturación por cliente" subtitle="Participación de los principales clientes."/>
    <div className="client-bars">{topClients.length?topClients.map((x:any)=><div key={x.id} className="client-bar-row">
      <div><b>{x.name}</b><small>{pct(x.share_percent)} del total</small></div>
      <div className="client-bar-track"><i style={{width:`${Number(x.invoiced)/maxBilling*100}%`}}/></div>
      <strong>{money(x.invoiced)}</strong>
    </div>):<Empty text="Todavía no hay facturación."/ >}</div>
   </Card>

   <Card>
    <SectionTitle title="Cartera de cobranza" subtitle="Cuánto ya ingresó y cuánto sigue expuesto."/>
    <div className="collection-big">
     <div><span>Cobrado</span><strong>{money(s.collected)}</strong></div>
     <div><span>Pendiente</span><strong>{money(s.pending)}</strong></div>
     <div className="danger"><span>Vencido</span><strong>{money(s.overdue)}</strong></div>
    </div>
    <div className="collection-stack">
     <i style={{width:`${Number(s.invoiced)>0?Number(s.collected)/Number(s.invoiced)*100:0}%`}}/>
    </div>
    <small className="muted-line">El tramo restante representa facturación todavía no cobrada.</small>
   </Card>
  </div>

  <Card>
   <div className="client-toolbar">
    <input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Buscar cliente, CUIT o contacto…"/>
    <label><span>Ordenar por</span><select value={sort} onChange={e=>setSort(e.target.value as any)}><option value="risk">Riesgo</option><option value="billing">Facturación</option><option value="pending">Pendiente</option><option value="overdue">Vencido</option></select></label>
   </div>
   <div className="table-wrap"><table className="client-exec-table">
    <thead><tr><th>Cliente</th><th>Facturado</th><th>Cobrado</th><th>Pendiente</th><th>Vencido</th><th>Obras</th><th>Servicios</th><th>Última actividad</th><th>Riesgo</th><th></th></tr></thead>
    <tbody>{rows.map((r:any)=><tr key={r.id} className="clickable-row" onClick={()=>setSelected(r)}>
     <td><b>{r.name}</b><small>{r.contact_name||r.tax_id||'Sin datos de contacto'}</small></td>
     <td>{money(r.invoiced)}</td><td>{money(r.collected)}</td>
     <td className={Number(r.pending)>0?'pending-money':''}><b>{money(r.pending)}</b></td>
     <td className={Number(r.overdue)>0?'danger-text':''}><b>{money(r.overdue)}</b>{Number(r.max_overdue_days)>0&&<small>{r.max_overdue_days} días máx.</small>}</td>
     <td>{r.active_works}</td><td>{r.active_services}</td><td>{dateAR(r.last_activity)}</td><td><Risk level={r.risk_level} reasons={r.risk_reasons}/></td>
     <td className="client-menu-cell" onClick={e=>e.stopPropagation()}><div className="client-menu"><button onClick={()=>setMenuOpen(menuOpen===r.id?null:r.id)}>⋯</button>{menuOpen===r.id&&<div className="client-menu-pop"><button onClick={()=>{setMenuOpen(null);setEditing(r)}}>Editar</button><button className="danger-text" onClick={()=>remove(r)}>Eliminar</button></div>}</div></td>
    </tr>)}</tbody>
   </table></div>
  </Card>

  {selected&&<ClientDrawer client={selected} close={()=>setSelected(null)}/>}
  {(creating||editing)&&<ClientModal initial={editing} close={()=>{setCreating(false);setEditing(null)}} done={async()=>{setCreating(false);setEditing(null);await load()}}/>}
 </div>
}

function Metric({label,value,sub,tone}:{label:string;value:string;sub:string;tone?:string}){
 return <div className={`client-metric ${tone||''}`}><span>{label}</span><strong>{value}</strong><small>{sub}</small></div>
}

function ClientDrawer({client,close}:{client:any;close:()=>void}){
 const [d,setD]=useState<any|null>(null);const [tab,setTab]=useState<'summary'|'works'|'services'|'billing'|'payments'>('summary');const [error,setError]=useState('');
 useEffect(()=>{api.get<any>(`/api/client-insights/${client.id}`).then(setD).catch((e:any)=>setError(e.message))},[client.id]);
 return <div className="client-drawer-bg" onMouseDown={e=>{if(e.target===e.currentTarget)close()}}><aside className="client-drawer">
  <div className="client-drawer-head"><div><span className="eyebrow">CLIENTE</span><h2>{client.name}</h2><p>{client.tax_id||'Sin CUIT'} · {client.contact_name||'Sin contacto'}</p></div><button className="close-button" onClick={close}>×</button></div>
  {error?<ErrorBox message={error}/>:!d?<Loading/>:<>
   <div className="client-drawer-kpis"><Mini l="Facturado" v={money(client.invoiced)}/><Mini l="Cobrado" v={money(client.collected)}/><Mini l="Pendiente" v={money(client.pending)}/><Mini l="Vencido" v={money(client.overdue)} danger={Number(client.overdue)>0}/></div>
   <div className="client-drawer-tabs">{[['summary','Resumen'],['works','Obras'],['services','Servicios'],['billing','Facturación'],['payments','Cobros']].map(([id,l])=><button key={id} className={tab===id?'active':''} onClick={()=>setTab(id as any)}>{l}</button>)}</div>
   {tab==='summary'&&<div className="drawer-summary">
    <div className="drawer-grid"><Mini l="Riesgo" v={client.risk_level}/><Mini l="Participación" v={pct(client.share_percent)}/><Mini l="Días prom. cobro" v={`${Math.round(Number(client.avg_collection_days||0))} días`}/><Mini l="Última actividad" v={dateAR(client.last_activity)}/></div>
    <section><h4>Contacto</h4><p>{client.contact_name||'—'}<br/>{client.email||'—'}<br/>{client.phone||'—'}</p></section>
    {!!client.risk_reasons?.length&&<section><h4>Motivos de riesgo</h4><div className="risk-reasons">{client.risk_reasons.map((x:string)=><span key={x}>{x}</span>)}</div></section>}
   </div>}
   {tab==='works'&&<SimpleList rows={d.works} cols={[['name','Obra'],['status','Estado'],['contract_amount','Contrato']]}/>}
   {tab==='services'&&<SimpleList rows={d.services} cols={[['name','Servicio'],['status','Estado'],['billing_amount','Monto']]}/>}
   {tab==='billing'&&<SimpleList rows={d.receivables} cols={[['document_number','Documento'],['issue_date','Emisión'],['amount','Monto'],['pending','Pendiente']]}/>}
   {tab==='payments'&&<SimpleList rows={d.payments} cols={[['movement_date','Fecha'],['description','Concepto'],['amount','Monto']]}/>}
  </>}
 </aside></div>
}
function Mini({l,v,danger}:{l:string;v:any;danger?:boolean}){return <div className={danger?'danger':''}><span>{l}</span><b>{v??'—'}</b></div>}
function SimpleList({rows,cols}:{rows:any[];cols:[string,string][]}){return rows?.length?<div className="table-wrap"><table><thead><tr>{cols.map(c=><th key={c[0]}>{c[1]}</th>)}</tr></thead><tbody>{rows.map((r:any,i:number)=><tr key={r.id||i}>{cols.map(([k])=><td key={k}>{k.includes('amount')||k==='pending'?money(r[k]):k.includes('date')?dateAR(r[k]):r[k]||'—'}</td>)}</tr>)}</tbody></table></div>:<Empty text="Sin registros."/>}

function ClientModal({initial,close,done}:any){
 const [saving,setSaving]=useState(false);const [f,setF]=useState<any>({name:initial?.name||'',tax_id:initial?.tax_id||'',contact_name:initial?.contact_name||'',email:initial?.email||'',phone:initial?.phone||'',address:initial?.address||'',notes:initial?.notes||'',is_active:initial?.is_active!==false});
 const save=async()=>{if(!f.name.trim())return;setSaving(true);try{if(initial)await api.update('clients',initial.id,f);else await api.create('clients',f);await done()}catch(e:any){alert(e.message||String(e))}finally{setSaving(false)}};
 return <div className="modal-backdrop"><div className="modal"><div className="modal-head"><div><span className="eyebrow">{initial?'EDITAR':'NUEVO'}</span><h2>{initial?'Editar cliente':'Nuevo cliente'}</h2></div><button className="close-button" onClick={close}>×</button></div><div className="form-grid">
  <label className="field full"><span>Razón social / nombre *</span><input value={f.name} onChange={e=>setF({...f,name:e.target.value})}/></label>
  <label className="field"><span>CUIT</span><input value={f.tax_id} onChange={e=>setF({...f,tax_id:e.target.value})}/></label><label className="field"><span>Contacto</span><input value={f.contact_name} onChange={e=>setF({...f,contact_name:e.target.value})}/></label>
  <label className="field"><span>Email</span><input value={f.email} onChange={e=>setF({...f,email:e.target.value})}/></label><label className="field"><span>Teléfono</span><input value={f.phone} onChange={e=>setF({...f,phone:e.target.value})}/></label>
  <label className="field full"><span>Dirección</span><input value={f.address} onChange={e=>setF({...f,address:e.target.value})}/></label><label className="field full"><span>Notas</span><textarea rows={3} value={f.notes} onChange={e=>setF({...f,notes:e.target.value})}/></label>
  <label className="field"><span>Activo</span><input type="checkbox" checked={f.is_active} onChange={e=>setF({...f,is_active:e.target.checked})}/></label>
 </div><div className="modal-actions"><button className="ghost-button" onClick={close}>Cancelar</button><button className="primary-button" disabled={saving||!f.name.trim()} onClick={save}>{saving?'Guardando…':'Guardar'}</button></div></div></div>
}
