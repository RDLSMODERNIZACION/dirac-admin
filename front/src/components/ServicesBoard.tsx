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
     const aFinished=a.effective_status!=='activo';
     const bFinished=b.effective_status!=='activo';
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
          <th>Períodos</th><th>Facturado</th><th>Cobrado</th><th>Pendiente</th><th>Próximo período</th>
        </tr></thead>
        <tbody>{rows.map((r:any)=>{
          const progress=Math.max(0,Math.min(100,Number(r.billing_progress_percent||0)));
          return <tr key={r.id} className={`${r.effective_status!=='activo'?'finished-row':''} clickable-row`} onClick={()=>setSelected(r.id)}>
            <td><b>{r.name}</b>
              {Number(r.pending_periods)>0&&<small className="work-row-note">{r.pending_periods} período{Number(r.pending_periods)===1?'':'s'} sin facturar</small>}
              {Number(r.overdue_amount)>0&&<small className="work-row-note danger-note">Vencido: {moneyFull(r.overdue_amount)}</small>}
            </td>
            <td>{r.client_name||'—'}</td>
            <td><span>{dateAR(r.start_date)}</span><small>→ {dateAR(r.end_date)}</small><small><Status tone={r.effective_status==='activo'?'green':r.effective_status==='cancelado'?'red':'blue'}>{r.effective_status}</Status></small></td>
            <td><b>{moneyFull(r.billing_amount)}</b></td>
            <td><div className="works-progress"><div><b>{r.billed_periods}/{r.total_periods}</b><span><i style={{width:`${progress}%`}}/></span></div></div></td>
            <td>{moneyFull(r.invoiced_total)}</td>
            <td>{moneyFull(r.collected_total)}</td>
            <td className={Number(r.pending_collection)>0?'pending-money':''}><b>{moneyFull(r.pending_collection)}</b></td>
            <td>{r.next_period_number?<><b>Mes {r.next_period_number}</b><small>{dateAR(r.next_period_start)}</small></>:<span>—</span>}</td>

          </tr>
        })}</tbody>
       </table>
      </div>
      <div className="works-control-footer"><span>Mostrando {rows.length} servicios</span><small>Los finalizados y cancelados se muestran al final.</small></div>
   </section>
 </div>
}
