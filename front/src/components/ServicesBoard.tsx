'use client';

import { useEffect, useMemo, useState } from 'react';
import { api } from '@/src/lib/api';
import { ServiceDetail } from './ServiceDetail';
import { ErrorBox, Loading, Status } from './ui';

const moneyFull=(v:any)=>`$ ${Math.round(Number(v||0)).toLocaleString('es-AR')}`;
const dateAR=(v:any)=>v?new Date(`${String(v).slice(0,10)}T12:00:00`).toLocaleDateString('es-AR'):'—';

function Risk({level,reasons}:{level:string;reasons?:string[]}){
 const tone=level==='alto'?'red':level==='medio'?'yellow':'green';
 const label=level==='alto'?'Alto':level==='medio'?'Medio':'Bajo';
 return <div className="works-risk-cell" title={(reasons||[]).join(' · ')}>
   <Status tone={tone as any}>{label}</Status>
   {!!reasons?.length&&<small>{reasons[0]}</small>}
 </div>
}

export function ServicesBoard({onNew}:{onNew?:()=>void}){
 const [data,setData]=useState<any|null>(null);
 const [error,setError]=useState('');
 const [query,setQuery]=useState('');
 const [sort,setSort]=useState<'risk'|'end'|'pending'>('risk');
 const [selected,setSelected]=useState<string|null>(null);
 const [editing,setEditing]=useState<any|null>(null);
 const [editForm,setEditForm]=useState<any>({});
 const [savingEdit,setSavingEdit]=useState(false);
 const [menuOpen,setMenuOpen]=useState<string|null>(null);

 const load=async()=>{
   setError('');
   try{setData(await api.get<any>('/api/services-board'))}
   catch(e:any){setError(e.message||String(e))}
 };
 useEffect(()=>{void load()},[]);

 const rows=useMemo(()=>{
   if(!data)return [];
   const q=query.trim().toLowerCase();
   let x=(data.services||[]).filter((r:any)=>!q||`${r.name} ${r.client_name}`.toLowerCase().includes(q));
   const riskRank:any={alto:0,medio:1,bajo:2};
   x=[...x].sort((a:any,b:any)=>{
     const aFinished=['finalizado','cancelado'].includes(a.effective_status);
     const bFinished=['finalizado','cancelado'].includes(b.effective_status);
     if(aFinished!==bFinished)return aFinished?1:-1;
     if(sort==='risk'){
       const d=(riskRank[a.risk_level]??9)-(riskRank[b.risk_level]??9);
       if(d)return d;
       return Number(b.pending_collection||0)-Number(a.pending_collection||0);
     }
     if(sort==='pending')return Number(b.pending_collection||0)-Number(a.pending_collection||0);
     const ad=a.end_date?new Date(a.end_date).getTime():Number.MAX_SAFE_INTEGER;
     const bd=b.end_date?new Date(b.end_date).getTime():Number.MAX_SAFE_INTEGER;
     return ad-bd;
   });
   return x;
 },[data,query,sort]);

 const openEdit=(r:any)=>{
   setEditing(r);
   setEditForm({
     name:r.name||'',
     billing_amount:String(r.billing_amount??''),
     start_date:r.start_date?String(r.start_date).slice(0,10):'',
     duration_months:String(r.duration_months??''),
     billing_day:r.billing_day==null?'':String(r.billing_day),
   });
 };

 const removeService=async(r:any)=>{
   setMenuOpen(null);
   const ok=confirm(`¿Eliminar el servicio "${r.name}"? Esta acción eliminará sus períodos y facturas pendientes si todavía no tiene cobros.`);
   if(!ok)return;
   try{
     await api.remove('services-board',r.id);
     await load();
   }catch(err:any){
     alert(err?.message||String(err));
   }
 };

 const saveEdit=async(e:any)=>{
   e.preventDefault();
   if(!editing)return;
   setSavingEdit(true);
   try{
     await api.update('services',editing.id,{
       name:String(editForm.name||'').trim(),
       billing_amount:Number(editForm.billing_amount||0),
       start_date:editForm.start_date||null,
       duration_months:editForm.duration_months===''?null:Number(editForm.duration_months),
       billing_day:editForm.billing_day===''?null:Number(editForm.billing_day),
     });
     await api.get<any>(`/api/services/${editing.id}/detail`);
     setEditing(null);
     await load();
   }catch(err:any){
     alert(err?.message||String(err));
   }finally{
     setSavingEdit(false);
   }
 };

 if(selected)return <ServiceDetail serviceId={selected} onBack={()=>{setSelected(null);void load()}}/>;
 if(error)return <ErrorBox message={error} onRetry={load}/>;
 if(!data)return <Loading/>;

 const s=data.summary||{};

 return <div className="works-board">
   <div className="works-kpis">
     <div className="works-kpi blue"><span>Servicios activos</span><strong>{s.active_services}</strong><small>De {s.total_services} servicios totales</small></div>
     <div className="works-kpi green"><span>Facturación mensual vigente</span><strong>{moneyFull(s.monthly_recurring)}</strong><small>Servicios mensuales activos</small></div>
     <div className="works-kpi amber"><span>Pendiente de cobro</span><strong>{moneyFull(s.pending_collection)}</strong><small>Facturado aún no ingresado a caja</small></div>
     <div className="works-kpi red"><span>Servicios en riesgo alto</span><strong>{s.high_risk_services}</strong><small>Requieren atención</small></div>
   </div>

   <section className="works-control-card">
      <div className="works-control-head">
        <div><span className="works-eyebrow">CONTROL DE SERVICIOS</span><h2>Cuadro de control de servicios</h2></div>
        <div className="works-board-tools">
          <input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Buscar servicio o cliente…"/>
          <label><span>Ordenar por</span><select value={sort} onChange={e=>setSort(e.target.value as any)}><option value="risk">Riesgo</option><option value="end">Fecha fin</option><option value="pending">Pendiente de cobro</option></select></label>
          {onNew&&<button className="primary-button" onClick={onNew}>+ Nuevo servicio</button>}
        </div>
      </div>

      <div className="table-wrap works-board-table-wrap">
       <table className="works-board-table services-board-table">
        <thead><tr>
          <th>Servicio</th><th>Cliente</th><th>Vigencia</th><th>Monto mensual</th>
          <th>Períodos</th><th>Facturado</th><th>Cobrado</th><th>Pendiente</th><th className="service-menu-head"></th>
        </tr></thead>
        <tbody>{rows.map((r:any)=>{
          const progress=Math.max(0,Math.min(100,Number(r.billing_progress_percent||0)));
          const visuallyFinished=['finalizado','cancelado'].includes(r.effective_status);
          return <tr key={r.id} className={`${visuallyFinished?'finished-row':''} clickable-row`} onClick={()=>setSelected(r.id)}>
            <td>
              <div style={{display:'flex',alignItems:'center',gap:8,flexWrap:'wrap'}}>
                <b>{r.name}</b>
              </div>
              {Number(r.due_pending_periods)>0&&<small className="work-row-note">{r.due_pending_periods} período{Number(r.due_pending_periods)===1?'':'s'} sin facturar</small>}
              {Number(r.overdue_amount)>0&&<small className="work-row-note danger-note">Vencido: {moneyFull(r.overdue_amount)}</small>}
            </td>
            <td>{r.client_name||'—'}</td>
            <td><span>{dateAR(r.start_date)}</span><small>→ {dateAR(r.end_date)}</small><small><Status tone={r.effective_status==='activo'?'green':r.effective_status==='pendiente_cierre'?'yellow':r.effective_status==='cancelado'?'red':'blue'}>{r.effective_status==='pendiente_cierre'?'Pendiente de cierre':r.effective_status}</Status></small></td>
            <td><b>{moneyFull(r.billing_amount)}</b></td>
            <td><div className="works-progress"><div><b>{r.billed_periods}/{r.total_periods}</b><span><i style={{width:`${progress}%`}}/></span></div></div></td>
            <td>{moneyFull(r.invoiced_total)}</td>
            <td>{moneyFull(r.collected_total)}</td>
            <td className={Number(r.pending_collection)>0?'pending-money':''}><b>{moneyFull(r.pending_collection)}</b></td>
            <td className="service-menu-cell" onClick={e=>e.stopPropagation()}>
              <div className="service-row-menu">
                <button
                  className="service-row-menu-button"
                  aria-label="Opciones"
                  onClick={()=>setMenuOpen(menuOpen===r.id?null:r.id)}
                >⋯</button>
                {menuOpen===r.id&&<div className="service-row-menu-popover">
                  <button onClick={()=>{setMenuOpen(null);openEdit(r)}}>Editar</button>
                  <button className="danger-text" onClick={()=>removeService(r)}>Eliminar</button>
                </div>}
              </div>
            </td>
          </tr>
        })}</tbody>
       </table>
      </div>
      <div className="works-control-footer"><span>Mostrando {rows.length} servicios</span><small>Solo los servicios realmente cerrados se muestran atenuados y al final.</small></div>
   </section>

   {editing&&<div className="modal-backdrop" onMouseDown={e=>{if(e.target===e.currentTarget)setEditing(null)}}>
     <div className="modal">
       <div className="modal-head">
         <div><span className="eyebrow">EDITAR SERVICIO</span><h2>{editing.name}</h2></div>
         <button className="close-button" onClick={()=>setEditing(null)}>×</button>
       </div>
       <form onSubmit={saveEdit}>
         <div className="form-grid">
           <label className="field full"><span>Nombre</span><input required value={editForm.name||''} onChange={e=>setEditForm({...editForm,name:e.target.value})}/></label>
           <label className="field"><span>Monto mensual</span><input type="number" min="0" step="0.01" required value={editForm.billing_amount||''} onChange={e=>setEditForm({...editForm,billing_amount:e.target.value})}/></label>
           <label className="field"><span>Fecha de inicio</span><input type="date" value={editForm.start_date||''} onChange={e=>setEditForm({...editForm,start_date:e.target.value})}/></label>
           <label className="field"><span>Duración (meses)</span><input type="number" min="1" step="1" value={editForm.duration_months||''} onChange={e=>setEditForm({...editForm,duration_months:e.target.value})}/></label>
           <label className="field"><span>Día de facturación/cobro</span><input type="number" min="1" max="31" value={editForm.billing_day||''} onChange={e=>setEditForm({...editForm,billing_day:e.target.value})}/></label>
         </div>
         <div className="modal-note" style={{marginTop:12}}>
           Los cambios de monto y fechas actualizan únicamente los períodos que todavía no fueron facturados.
         </div>
         <div className="modal-actions">
           <button type="button" className="ghost-button" onClick={()=>setEditing(null)}>Cancelar</button>
           <button className="primary-button" disabled={savingEdit}>{savingEdit?'Guardando…':'Guardar cambios'}</button>
         </div>
       </form>
     </div>
   </div>}
 </div>
}
