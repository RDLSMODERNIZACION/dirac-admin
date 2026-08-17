'use client';

import { useEffect, useMemo, useState } from 'react';
import { api } from '@/src/lib/api';
import { WorkDetail } from './WorkDetail';
import { ErrorBox, Loading, Status } from './ui';
import { NewWorkModal } from './NewJobModals';

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

export function WorksBoard(){
 const [data,setData]=useState<any|null>(null);
 const [error,setError]=useState('');
 const [query,setQuery]=useState('');
 const [sort,setSort]=useState<'risk'|'end'|'pending'>('end');
 const [selected,setSelected]=useState<string|null>(null);
 const [menuOpen,setMenuOpen]=useState<string|null>(null);
 const [editing,setEditing]=useState<any|null>(null);
 const [editForm,setEditForm]=useState<any>({});
 const [savingEdit,setSavingEdit]=useState(false);
 const [creating,setCreating]=useState(false);

 const load=async()=>{
   setError('');
   try{setData(await api.get<any>('/api/works-board'))}
   catch(e:any){setError(e.message||String(e))}
 };
 useEffect(()=>{void load()},[]);

 const rows=useMemo(()=>{
   if(!data)return [];
   const q=query.trim().toLowerCase();
   let x=(data.works||[]).filter((r:any)=>!q||`${r.name} ${r.client_name}`.toLowerCase().includes(q));
   const riskRank:any={alto:0,medio:1,bajo:2};
   x=[...x].sort((a:any,b:any)=>{
     if(a.is_finished!==b.is_finished)return a.is_finished?1:-1;
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
   setMenuOpen(null);
   setEditing(r);
   setEditForm({
     name:r.name||'',
     start_date:r.start_date?String(r.start_date).slice(0,10):'',
     end_date:r.end_date?String(r.end_date).slice(0,10):'',
     contract_amount:String(r.contract_amount??''),
   });
 };

 const saveEdit=async(e:any)=>{
   e.preventDefault();
   if(!editing)return;
   setSavingEdit(true);
   try{
     await api.update('works',editing.id,{
       name:String(editForm.name||'').trim(),
       start_date:editForm.start_date||null,
       end_date:editForm.end_date||null,
       contract_amount:Number(editForm.contract_amount||0),
     });
     setEditing(null);
     await load();
   }catch(err:any){alert(err?.message||String(err))}
   finally{setSavingEdit(false)}
 };

 const removeWork=async(r:any)=>{
   setMenuOpen(null);
   if(!confirm(`¿Eliminar la obra "${r.name}"?`))return;
   try{
     await api.remove('works',r.id);
     await load();
   }catch(err:any){alert(err?.message||String(err))}
 };

 if(selected)return <WorkDetail workId={selected} onBack={()=>{setSelected(null);void load()}}/>;
 if(error)return <ErrorBox message={error} onRetry={load}/>;
 if(!data)return <Loading/>;

 const s=data.summary||{};

 return <div className="works-board">
   <div className="works-kpis">
     <div className="works-kpi blue"><span>Obras activas</span><strong>{s.active_works}</strong><small>De {s.total_works} obras totales</small></div>
     <div className="works-kpi green"><span>Ejecutado total</span><strong>{moneyFull(s.executed_total)}</strong><small>Valor ejecutado de obras activas</small></div>
     <div className="works-kpi amber"><span>Pendiente de cobro</span><strong>{moneyFull(s.pending_collection)}</strong><small>Facturado aún no ingresado a caja</small></div>
     <div className="works-kpi red"><span>Obras en riesgo alto</span><strong>{s.high_risk_works}</strong><small>Requieren atención</small></div>
   </div>

   <div className="works-board-layout">
    <section className="works-control-card">
      <div className="works-control-head">
        <div><span className="works-eyebrow">CONTROL DE PROYECTOS</span><h2>Cuadro de control de obras</h2></div>
        <div className="works-board-tools">
          <input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Buscar obra o cliente…"/>
          <label><span>Ordenar por</span><select value={sort} onChange={e=>setSort(e.target.value as any)}><option value="risk">Riesgo</option><option value="end">Fecha fin</option><option value="pending">Pendiente de cobro</option></select></label>
          <button className="primary-button" onClick={()=>setCreating(true)}>+ Nueva obra</button>
        </div>
      </div>

      <div className="table-wrap works-board-table-wrap">
       <table className="works-board-table">
        <thead><tr>
          <th>Obra</th><th>Cliente</th><th>Fechas</th><th>Avance</th>
          <th>Ejecutado</th><th>Facturado</th><th>Cobrado</th><th>Pendiente de cobro</th><th>Riesgo</th><th className="work-menu-head"></th>
        </tr></thead>
        <tbody>{rows.map((r:any)=>{
          const progress=Math.max(0,Math.min(100,Number(r.progress_percent||0)));
          return <tr key={r.id} className={`${r.is_finished?'finished-row':''} clickable-row`} onClick={()=>setSelected(r.id)}>
            <td><b>{r.name}</b>{Number(r.executed_unbilled)>0&&<small className="work-row-note">Ejecutado sin facturar: {moneyFull(r.executed_unbilled)}</small>}{Number(r.advanced_invoicing)>0&&<small className="work-row-note positive-note">Facturación anticipada: {moneyFull(r.advanced_invoicing)}</small>}</td>
            <td>{r.client_name}</td>
            <td><span>{dateAR(r.start_date)}</span><small>→ {dateAR(r.end_date)}</small></td>
            <td><div className="works-progress"><div><b>{progress.toFixed(0)}%</b><span><i style={{width:`${progress}%`}}/></span></div></div></td>
            <td><b>{moneyFull(r.executed_amount)}</b></td>
            <td>{moneyFull(r.invoiced_total)}</td>
            <td>{moneyFull(r.collected)}</td>
            <td className={Number(r.pending_collection)>0?'pending-money':''}><b>{moneyFull(r.pending_collection)}</b>{Number(r.overdue_amount)>0&&<small>Vencido: {moneyFull(r.overdue_amount)}</small>}</td>
            <td><Risk level={r.risk_level} reasons={r.risk_reasons}/></td>
            <td className="work-menu-cell" onClick={e=>e.stopPropagation()}>
              <div className="work-row-menu">
                <button className="work-row-menu-button" aria-label="Opciones" onClick={()=>setMenuOpen(menuOpen===r.id?null:r.id)}>⋯</button>
                {menuOpen===r.id&&<div className="work-row-menu-popover">
                  <button onClick={()=>{setMenuOpen(null);openEdit(r)}}>Editar</button>
                  <button className="danger-text" onClick={()=>removeWork(r)}>Eliminar</button>
                </div>}
              </div>
            </td>
          </tr>
        })}</tbody>
       </table>
      </div>
      <div className="works-control-footer"><span>Mostrando {rows.length} obras</span><small>Las finalizadas se muestran al final.</small></div>
    </section>

   </div>
   {creating&&<NewWorkModal close={()=>setCreating(false)} done={async()=>{setCreating(false);await load()}}/>}
   {editing&&<div className="modal-backdrop" onMouseDown={e=>{if(e.target===e.currentTarget)setEditing(null)}}>
     <div className="modal">
       <div className="modal-head"><div><span className="eyebrow">EDITAR OBRA</span><h2>{editing.name}</h2></div><button className="close-button" onClick={()=>setEditing(null)}>×</button></div>
       <form onSubmit={saveEdit}>
         <div className="form-grid">
           <label className="field full"><span>Nombre</span><input required value={editForm.name||''} onChange={e=>setEditForm({...editForm,name:e.target.value})}/></label>
           <label className="field"><span>Inicio</span><input type="date" value={editForm.start_date||''} onChange={e=>setEditForm({...editForm,start_date:e.target.value})}/></label>
           <label className="field"><span>Fin estimado</span><input type="date" value={editForm.end_date||''} onChange={e=>setEditForm({...editForm,end_date:e.target.value})}/></label>
           <label className="field"><span>Valor contrato IVA incluido</span><input type="number" min="0" step="0.01" value={editForm.contract_amount||''} onChange={e=>setEditForm({...editForm,contract_amount:e.target.value})}/></label>
         </div>
         <div className="modal-actions"><button type="button" className="ghost-button" onClick={()=>setEditing(null)}>Cancelar</button><button className="primary-button" disabled={savingEdit}>{savingEdit?'Guardando…':'Guardar cambios'}</button></div>
       </form>
     </div>
   </div>}

 </div>
}
