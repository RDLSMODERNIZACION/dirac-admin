'use client';

import { useEffect, useMemo, useState } from 'react';
import { api } from '@/src/lib/api';
import { Card, Empty, ErrorBox, Loading, SectionTitle, Status } from './ui';

const fmtDate=(v:any)=>v?new Date(`${String(v).slice(0,10)}T12:00:00`).toLocaleDateString('es-AR'):'—';
const iso=(d:Date)=>d.toISOString().slice(0,10);
const DAY=86400000;

function parseDate(v:any){
  if(!v) return null;
  const s=String(v).slice(0,10);
  const d=new Date(`${s}T12:00:00`);
  return isNaN(d.getTime())?null:d;
}
function addDays(d:Date,n:number){ return new Date(d.getTime()+n*DAY); }
function diffDays(a:Date,b:Date){ return Math.round((a.getTime()-b.getTime())/DAY); }
function startOfWeek(d:Date){
  const x=new Date(d.getTime());
  const day=(x.getDay()+6)%7;
  x.setDate(x.getDate()-day);
  x.setHours(12,0,0,0);
  return x;
}
function endOfWeek(d:Date){ return addDays(startOfWeek(d),6); }
function startOfMonth(d:Date){ return new Date(d.getFullYear(),d.getMonth(),1,12); }
function endOfMonth(d:Date){ return new Date(d.getFullYear(),d.getMonth()+1,0,12); }
function monthLabel(d:Date){ return d.toLocaleDateString('es-AR',{month:'long',year:'numeric'}); }
function shortDate(d:Date){ return d.toLocaleDateString('es-AR',{day:'2-digit',month:'2-digit'}); }

function TaskStatus({status,overdue}:{status:string;overdue?:boolean}){
 if(overdue)return <Status tone="red">Vencida</Status>;
 if(status==='completada')return <Status tone="green">Completada</Status>;
 if(status==='en_ejecucion')return <Status tone="blue">En ejecución</Status>;
 if(status==='pausada')return <Status tone="yellow">Pausada</Status>;
 return <Status tone="gray">Pendiente</Status>;
}

export function Planning({workId}:{workId?:string}={}){
 const [tab,setTab]=useState<'tasks'|'gantt'>('gantt');
 const [rows,setRows]=useState<any[]|null>(null);
 const [summary,setSummary]=useState<any|null>(null);
 const [works,setWorks]=useState<any[]>([]);
 const [query,setQuery]=useState('');
 const [filter,setFilter]=useState('abiertas');
 const [open,setOpen]=useState(false);
 const [edit,setEdit]=useState<any|null>(null);
 const [error,setError]=useState('');

 const load=async()=>{
  try{
   const [tasks,s,w]=await Promise.all([
    api.get<any[]>(`/api/planning/tasks${workId?`?work_id=${workId}`:''}`),
    api.get<any>('/api/planning/summary'),
    api.list<any>('works','?limit=500')
   ]);
   setRows(tasks);setSummary(s);setWorks(w);setError('');
  }catch(e:any){setError(e.message||String(e))}
 };
 useEffect(()=>{void load()},[workId]);

 const filtered=useMemo(()=>{
  if(!rows)return [];
  const q=query.trim().toLowerCase();
  return rows.filter(r=>{
   if(q&&!`${r.title} ${r.work_name} ${r.item_description||''} ${r.responsible||''}`.toLowerCase().includes(q))return false;
   if(filter==='vencidas')return !!r.is_overdue;
   if(filter==='pendientes')return r.status==='pendiente'&&!r.is_overdue;
   if(filter==='ejecucion')return r.status==='en_ejecucion'&&!r.is_overdue;
   if(filter==='completadas')return r.status==='completada';
   if(filter==='abiertas')return r.status!=='completada';
   return true;
  });
 },[rows,query,filter]);

 if(error)return <ErrorBox message={error} onRetry={load}/>;
 if(!rows||!summary)return <Loading/>;

 return <div className="page-stack planning-page">
  {!workId&&<SectionTitle title="Planificación" subtitle="Tareas, responsables y cronograma de ejecución de todas las obras."/>}

  <div className="planning-kpis">
   <div><span>Pendientes</span><strong>{summary.pending||0}</strong></div>
   <div><span>En ejecución</span><strong>{summary.in_progress||0}</strong></div>
   <div className={Number(summary.overdue)>0?'danger':''}><span>Vencidas</span><strong>{summary.overdue||0}</strong></div>
   <div><span>Próximos 7 días</span><strong>{summary.next_7_days||0}</strong></div>
  </div>

  <div className="tabs standalone">
   <button className={tab==='gantt'?'active':''} onClick={()=>setTab('gantt')}>Cronograma</button>
   <button className={tab==='tasks'?'active':''} onClick={()=>setTab('tasks')}>Tareas</button>
  </div>

  <Card>
   <div className="planning-toolbar">
    <input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Buscar tarea, obra, ítem o responsable…"/>
    <select value={filter} onChange={e=>setFilter(e.target.value)}>
     <option value="abiertas">Abiertas</option>
     <option value="todas">Todas</option>
     <option value="vencidas">Vencidas</option>
     <option value="pendientes">Pendientes</option>
     <option value="ejecucion">En ejecución</option>
     <option value="completadas">Completadas</option>
    </select>
    <button className="primary-button" onClick={()=>{setEdit(null);setOpen(true)}}>+ Nueva tarea</button>
   </div>

   {tab==='tasks'&&(
    filtered.length===0?<Empty text="No hay tareas para mostrar."/>:<div className="table-wrap"><table className="planning-table">
      <thead><tr><th>Tarea</th>{!workId&&<th>Obra</th>}<th>Ítem</th><th>Responsable</th><th>Inicio</th><th>Fin</th><th>Prioridad</th><th>Estado</th><th>Avance</th><th></th></tr></thead>
      <tbody>{filtered.map(r=><tr key={r.id}>
        <td><b>{r.title}</b>{r.description&&<small>{r.description}</small>}</td>
        {!workId&&<td>{r.work_name}</td>}
        <td>{r.item_description||'General de obra'}</td>
        <td>{r.responsible||'—'}</td>
        <td>{fmtDate(r.start_date)}</td>
        <td className={r.is_overdue?'danger-text':''}>{fmtDate(r.end_date)}</td>
        <td><span className={`priority ${r.priority}`}>{r.priority}</span></td>
        <td><TaskStatus status={r.status} overdue={r.is_overdue}/></td>
        <td><b>{Math.round(Number(r.progress_percent||0))}%</b></td>
        <td><div className="row-actions"><button className="mini-button" onClick={()=>{setEdit(r);setOpen(true)}}>Editar</button><button className="mini-button danger-text" onClick={async()=>{if(confirm(`¿Eliminar la tarea "${r.title}"?`)){try{await api.remove('planning/tasks',r.id);await load()}catch(e:any){alert(e.message)}}}}>Eliminar</button></div></td>
      </tr>)}</tbody>
    </table></div>
   )}

   {tab==='gantt'&&<GanttBoard rows={filtered} />}
  </Card>

  {open&&<TaskModal
    initial={edit}
    works={works}
    fixedWorkId={workId}
    close={()=>{setOpen(false);setEdit(null)}}
    done={async()=>{setOpen(false);setEdit(null);await load()}}
  />}
 </div>
}

function GanttBoard({rows}:{rows:any[]}){
 const dated=rows.filter(r=>parseDate(r.start_date)&&parseDate(r.end_date));
 const groups=useMemo(()=>{
   const map=new Map<string,{name:string;client:string;rows:any[]}>();
   dated.forEach(r=>{
     const key=r.work_id||r.work_name||'obra';
     if(!map.has(key)) map.set(key,{name:r.work_name||'Obra',client:r.client_name||'',rows:[]});
     map.get(key)!.rows.push(r);
   });
   const list=Array.from(map.values());
   list.forEach(g=>g.rows.sort((a,b)=>(parseDate(a.start_date)?.getTime()||0)-(parseDate(b.start_date)?.getTime()||0)));
   return list.sort((a,b)=>{
     const ad=parseDate(a.rows[0]?.start_date)?.getTime()||0;
     const bd=parseDate(b.rows[0]?.start_date)?.getTime()||0;
     return ad-bd;
   });
 },[dated]);

 if(dated.length===0)return <Empty text="Cargá fechas de inicio y fin para visualizar el cronograma."/>;

 const starts=dated.map(r=>parseDate(r.start_date)!.getTime());
 const ends=dated.map(r=>parseDate(r.end_date)!.getTime());
 const today=new Date(); today.setHours(12,0,0,0);
 const minDate=new Date(Math.min(...starts, today.getTime()));
 const maxDate=new Date(Math.max(...ends, today.getTime()));
 const timelineStart=startOfWeek(startOfMonth(minDate));
 const timelineEnd=endOfWeek(endOfMonth(maxDate));
 const weeks:Date[]=[];
 for(let d=new Date(timelineStart); d<=timelineEnd; d=addDays(d,7)) weeks.push(new Date(d));
 const totalDays=diffDays(timelineEnd,timelineStart)+1;
 const todayLeft=Math.min(100,Math.max(0,(diffDays(today,timelineStart)/totalDays)*100));

 const monthGroups:{label:string;span:number}[]=[];
 weeks.forEach(w=>{
   const label=monthLabel(w);
   const last=monthGroups[monthGroups.length-1];
   if(last&&last.label===label) last.span += 1;
   else monthGroups.push({label,span:1});
 });

 return <div className="gantt-pro-wrap">
   <div className="gantt-pro-legend">
     <span><i className="dot blue"></i> En ejecución</span>
     <span><i className="dot green"></i> Completada</span>
     <span><i className="dot yellow"></i> Pendiente / pausada</span>
     <span><i className="dot red"></i> Vencida</span>
   </div>

   <div className="gantt-pro-shell">
     <div className="gantt-pro-table">
       <div className="gantt-pro-head gantt-pro-grid">
         <div className="gantt-left-head">
           <strong>Tarea</strong>
           <span>Obra, responsable y fechas</span>
         </div>
         <div className="gantt-right-head">
           <div className="gantt-months" style={{gridTemplateColumns:`repeat(${weeks.length}, minmax(72px, 1fr))`}}>
             {monthGroups.map((m,i)=><div key={i} className="gantt-month" style={{gridColumn:`span ${m.span}`}}>{m.label}</div>)}
           </div>
           <div className="gantt-weeks" style={{gridTemplateColumns:`repeat(${weeks.length}, minmax(72px, 1fr))`}}>
             {weeks.map((w,i)=><div key={i} className="gantt-week"><b>{shortDate(w)}</b><span>{shortDate(addDays(w,6))}</span></div>)}
           </div>
         </div>
       </div>

       {groups.map((g,gi)=><div key={gi} className="gantt-group">
         <div className="gantt-group-title">{g.name}<small>{g.client}</small></div>
         {g.rows.map((r:any)=>{
           const sd=parseDate(r.start_date)!; const ed=parseDate(r.end_date)!;
           const left=(diffDays(sd,timelineStart)/totalDays)*100;
           const width=Math.max(1.5,((diffDays(ed,sd)+1)/totalDays)*100);
           const progress=Math.max(0,Math.min(100,Number(r.progress_percent||0)));
           const tone=r.is_overdue?'overdue':(r.status==='completada'?'done':(r.status==='en_ejecucion'?'active':'pending'));
           return <div key={r.id} className="gantt-row-pro gantt-pro-grid">
             <div className="gantt-row-info">
               <div className="gantt-task-title">{r.title}</div>
               <div className="gantt-task-meta">
                 <span>{r.item_description||'General de obra'}</span>
                 <span>{r.responsible||'Sin responsable'}</span>
                 <span>{fmtDate(r.start_date)} → {fmtDate(r.end_date)}</span>
               </div>
             </div>
             <div className="gantt-row-track-wrap">
               <div className="gantt-row-track" style={{gridTemplateColumns:`repeat(${weeks.length}, minmax(72px, 1fr))`}}>
                 {weeks.map((_:Date,i:number)=><div key={i} className="gantt-cell"/>) }
                 <div className="gantt-today-line" style={{left:`${todayLeft}%`}} />
                 <div className={`gantt-bar-pro ${tone}`} style={{left:`${left}%`,width:`${width}%`}}>
                   <div className="gantt-bar-fill" style={{width:`${progress}%`}} />
                   <span className="gantt-bar-label">{progress}%</span>
                 </div>
               </div>
             </div>
           </div>
         })}
       </div>)}
     </div>
   </div>
 </div>
}

function TaskModal({initial,works,fixedWorkId,close,done}:any){
 const [items,setItems]=useState<any[]>([]);
 const [saving,setSaving]=useState(false);
 const [f,setF]=useState<any>({
  work_id:fixedWorkId||initial?.work_id||works[0]?.id||'',
  work_item_id:initial?.work_item_id||'',
  title:initial?.title||'',
  description:initial?.description||'',
  responsible:initial?.responsible||'',
  start_date:initial?.start_date?String(initial.start_date).slice(0,10):iso(new Date()),
  end_date:initial?.end_date?String(initial.end_date).slice(0,10):iso(new Date()),
  status:initial?.status||'pendiente',
  priority:initial?.priority||'media',
  progress_percent:String(initial?.progress_percent??0),
  notes:initial?.notes||''
 });

 useEffect(()=>{
  if(!f.work_id){setItems([]);return}
  api.list<any>('work_items',`?limit=500&work_id=${f.work_id}`).then(setItems).catch(()=>setItems([]));
 },[f.work_id]);

 const save=async()=>{
  if(!f.work_id||!String(f.title).trim())return;
  setSaving(true);
  try{
   const payload={...f,work_item_id:f.work_item_id||null,progress_percent:Number(f.progress_percent||0)};
   if(initial)await api.update('planning/tasks',initial.id,payload);
   else await api.create('planning/tasks',payload);
   await done();
  }catch(e:any){alert(e.message||String(e))}
  finally{setSaving(false)}
 };

 return <div className="modal-backdrop"><div className="modal">
  <div className="modal-head"><div><span className="eyebrow">{initial?'EDITAR':'NUEVA'}</span><h2>{initial?'Editar tarea':'Nueva tarea'}</h2></div><button className="close-button" onClick={close}>×</button></div>
  <div className="form-grid">
   <label className="field"><span>Obra *</span><select disabled={!!fixedWorkId} value={f.work_id} onChange={e=>setF({...f,work_id:e.target.value,work_item_id:''})}><option value="">Seleccionar…</option>{works.map((w:any)=><option key={w.id} value={w.id}>{w.name}</option>)}</select></label>
   <label className="field"><span>Ítem asociado</span><select value={f.work_item_id} onChange={e=>setF({...f,work_item_id:e.target.value})}><option value="">General de obra</option>{items.map((x:any)=><option key={x.id} value={x.id}>{x.description}</option>)}</select></label>
   <label className="field full"><span>Tarea *</span><input value={f.title} onChange={e=>setF({...f,title:e.target.value})}/></label>
   <label className="field full"><span>Descripción</span><textarea rows={2} value={f.description} onChange={e=>setF({...f,description:e.target.value})}/></label>
   <label className="field"><span>Responsable</span><input value={f.responsible} onChange={e=>setF({...f,responsible:e.target.value})}/></label>
   <label className="field"><span>Prioridad</span><select value={f.priority} onChange={e=>setF({...f,priority:e.target.value})}><option value="baja">Baja</option><option value="media">Media</option><option value="alta">Alta</option><option value="critica">Crítica</option></select></label>
   <label className="field"><span>Inicio</span><input type="date" value={f.start_date} onChange={e=>setF({...f,start_date:e.target.value})}/></label>
   <label className="field"><span>Fin</span><input type="date" value={f.end_date} onChange={e=>setF({...f,end_date:e.target.value})}/></label>
   <label className="field"><span>Estado</span><select value={f.status} onChange={e=>setF({...f,status:e.target.value,progress_percent:e.target.value==='completada'?'100':f.progress_percent})}><option value="pendiente">Pendiente</option><option value="en_ejecucion">En ejecución</option><option value="pausada">Pausada</option><option value="completada">Completada</option></select></label>
   <label className="field"><span>Avance %</span><input type="number" min="0" max="100" step="1" value={f.progress_percent} onChange={e=>setF({...f,progress_percent:e.target.value})}/></label>
   <label className="field full"><span>Notas</span><textarea rows={2} value={f.notes} onChange={e=>setF({...f,notes:e.target.value})}/></label>
  </div>
  <div className="modal-actions"><button className="ghost-button" onClick={close}>Cancelar</button><button className="primary-button" disabled={saving||!f.work_id||!String(f.title).trim()} onClick={save}>{saving?'Guardando…':'Guardar tarea'}</button></div>
 </div></div>
}
