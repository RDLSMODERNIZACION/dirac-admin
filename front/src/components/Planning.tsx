'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { api } from '@/src/lib/api';
import { Card, Empty, ErrorBox, Loading, SectionTitle, Status } from './ui';

const DAY=86400000;
const GANTT_WEEK_PX=128;
const fmtDate=(v:any)=>v?new Date(`${String(v).slice(0,10)}T12:00:00`).toLocaleDateString('es-AR'):'—';
const iso=(d:Date)=>{const x=new Date(d);x.setHours(12,0,0,0);return x.toISOString().slice(0,10)};
const parseDate=(v:any)=>v?new Date(`${String(v).slice(0,10)}T12:00:00`):null;
const addDays=(d:Date,n:number)=>new Date(d.getTime()+n*DAY);
const diffDays=(a:Date,b:Date)=>Math.round((a.getTime()-b.getTime())/DAY);
const startOfWeek=(d:Date)=>{const x=new Date(d);const day=(x.getDay()+6)%7;x.setDate(x.getDate()-day);x.setHours(12,0,0,0);return x};
const endOfWeek=(d:Date)=>addDays(startOfWeek(d),6);
const startOfMonth=(d:Date)=>new Date(d.getFullYear(),d.getMonth(),1,12);
const endOfMonth=(d:Date)=>new Date(d.getFullYear(),d.getMonth()+1,0,12);
const monthLabel=(d:Date)=>d.toLocaleDateString('es-AR',{month:'long',year:'numeric'});
const shortDate=(d:Date)=>d.toLocaleDateString('es-AR',{day:'2-digit',month:'2-digit'});

function TaskStatus({status,overdue}:{status:string;overdue?:boolean}){
 if(overdue)return <Status tone="red">Vencida</Status>;
 if(status==='completada')return <Status tone="green">Completada</Status>;
 if(status==='en_ejecucion')return <Status tone="blue">En ejecución</Status>;
 if(status==='pausada')return <Status tone="yellow">Pausada</Status>;
 return <Status tone="gray">Pendiente</Status>;
}

function payloadFromTask(r:any,overrides:any={}){
 return {
  work_id:r.work_id,
  work_item_id:r.work_item_id||null,
  title:r.title,
  description:r.description||null,
  responsible:r.responsible||null,
  start_date:r.start_date?String(r.start_date).slice(0,10):null,
  end_date:r.end_date?String(r.end_date).slice(0,10):null,
  status:r.status||'pendiente',
  priority:r.priority||'media',
  progress_percent:Number(r.progress_percent||0),
  notes:r.notes||null,
  task_type:r.task_type||'tarea',
  predecessor_ids:(r.predecessors||[]).map((x:any)=>x.id),
  ...overrides,
 };
}

export function Planning({workId}:{workId?:string}={}){
 const [view,setView]=useState<'gantt'|'calendar'|'tasks'>('gantt');
 const [rows,setRows]=useState<any[]|null>(null);
 const [summary,setSummary]=useState<any|null>(null);
 const [works,setWorks]=useState<any[]>([]);
 const [query,setQuery]=useState('');
 const [filter,setFilter]=useState('abiertas');
 const [responsible,setResponsible]=useState('');
 const [open,setOpen]=useState(false);
 const [edit,setEdit]=useState<any|null>(null);
 const [selected,setSelected]=useState<any|null>(null);
 const [error,setError]=useState('');

 const load=async()=>{
  try{
   const [tasks,s,w,wb]=await Promise.all([
    api.get<any[]>(`/api/planning/tasks${workId?`?work_id=${workId}`:''}`),
    api.get<any>(`/api/planning/summary${workId?`?work_id=${workId}`:''}`),
    api.list<any>('works','?limit=500'),
    api.get<any>('/api/works-board')
   ]);
   const boardMap=new Map((wb?.works||[]).map((x:any)=>[x.id,x]));
   const enrichedWorks=(w||[]).map((x:any)=>{
    const b:any=boardMap.get(x.id);
    return {...x,progress_percent:b?.progress_percent??0,client_name:b?.client_name||x.client_name||'',is_finished:b?.is_finished??false};
   });
   setRows(tasks);setSummary(s);setWorks(enrichedWorks);setError('');
   setSelected((prev:any)=>prev?tasks.find((x:any)=>x.id===prev.id)||null:null);
  }catch(e:any){setError(e.message||String(e))}
 };
 useEffect(()=>{void load()},[workId]);

 const responsibles=useMemo(()=>Array.from(new Set((rows||[]).map(r=>String(r.responsible||'').trim()).filter(Boolean))).sort(),[rows]);

 const filtered=useMemo(()=>{
  if(!rows)return [];
  const q=query.trim().toLowerCase();
  return rows.filter(r=>{
   if(q&&!`${r.title} ${r.work_name} ${r.item_description||''} ${r.responsible||''}`.toLowerCase().includes(q))return false;
   if(responsible&&r.responsible!==responsible)return false;
   if(filter==='vencidas')return !!r.is_overdue;
   if(filter==='pendientes')return r.status==='pendiente'&&!r.is_overdue;
   if(filter==='ejecucion')return r.status==='en_ejecucion'&&!r.is_overdue;
   if(filter==='completadas')return r.status==='completada';
   if(filter==='abiertas')return r.status!=='completada';
   return true;
  });
 },[rows,query,filter,responsible]);

 const remove=async(r:any)=>{
  if(!confirm(`¿Eliminar la tarea "${r.title}"?`))return;
  try{await api.remove('planning/tasks',r.id);setSelected(null);await load()}catch(e:any){alert(e.message||String(e))}
 };
 const duplicate=async(r:any)=>{
  try{await api.post(`/api/planning/tasks/${r.id}/duplicate`,{});await load()}catch(e:any){alert(e.message||String(e))}
 };
 const complete=async(r:any)=>{
  try{await api.update('planning/tasks',r.id,payloadFromTask(r,{status:'completada',progress_percent:100}));await load()}catch(e:any){alert(e.message||String(e))}
 };

 if(error)return <ErrorBox message={error} onRetry={load}/>;
 if(!rows||!summary)return <Loading/>;

 return <div className="page-stack planning-page">
  {!workId&&<SectionTitle title="Planificación" subtitle="Tareas, dependencias, responsables y cronograma de ejecución de todas las obras."/>}

  <div className="planning-kpis">
   <div><span>Pendientes</span><strong>{summary.pending||0}</strong><small>tareas abiertas</small></div>
   <div><span>En ejecución</span><strong>{summary.in_progress||0}</strong><small>trabajo activo</small></div>
   <div className={Number(summary.overdue)>0?'danger':''}><span>Vencidas</span><strong>{summary.overdue||0}</strong><small>requieren atención</small></div>
   <div><span>Próximos 7 días</span><strong>{summary.next_7_days||0}</strong><small>vencen pronto</small></div>
  </div>

  <Card>
   <div className="planning-toolbar pro">
    <input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Buscar tarea, obra, ítem o responsable…"/>
    <select value={filter} onChange={e=>setFilter(e.target.value)}>
     <option value="abiertas">Abiertas</option><option value="todas">Todas</option><option value="vencidas">Vencidas</option>
     <option value="pendientes">Pendientes</option><option value="ejecucion">En ejecución</option><option value="completadas">Completadas</option>
    </select>
    <select value={responsible} onChange={e=>setResponsible(e.target.value)}><option value="">Todos los responsables</option>{responsibles.map(x=><option key={x} value={x}>{x}</option>)}</select>
    <div className="planning-view-switch">
     <button className={view==='gantt'?'active':''} onClick={()=>setView('gantt')}>Cronograma</button>
     <button className={view==='calendar'?'active':''} onClick={()=>setView('calendar')}>Calendario</button>
     <button className={view==='tasks'?'active':''} onClick={()=>setView('tasks')}>Tareas</button>
    </div>
    <button className="primary-button" onClick={()=>{setEdit(null);setOpen(true)}}>+ Nueva tarea</button>
   </div>

   {view==='gantt'&&<GanttBoard rows={filtered} works={works} selected={selected} onSelect={setSelected} reload={load}/>}
   {view==='calendar'&&<CalendarView rows={filtered} onSelect={setSelected}/>}
   {view==='tasks'&&<TaskTable rows={filtered} workId={workId} onSelect={setSelected} onEdit={r=>{setEdit(r);setOpen(true)}} onDelete={remove}/>}
  </Card>

  {selected&&<TaskDrawer task={selected} close={()=>setSelected(null)} edit={()=>{setEdit(selected);setOpen(true)}} remove={()=>remove(selected)} duplicate={()=>duplicate(selected)} complete={()=>complete(selected)}/>}
  {open&&<TaskModal initial={edit} rows={rows} works={works} fixedWorkId={workId} close={()=>{setOpen(false);setEdit(null)}} done={async()=>{setOpen(false);setEdit(null);await load()}}/>}
 </div>
}

function TaskTable({rows,workId,onSelect,onEdit,onDelete}:any){
 if(!rows.length)return <Empty text="No hay tareas para mostrar."/>;
 return <div className="table-wrap"><table className="planning-table">
  <thead><tr><th>Tarea</th>{!workId&&<th>Obra</th>}<th>Ítem</th><th>Responsable</th><th>Inicio</th><th>Fin</th><th>Prioridad</th><th>Estado</th><th>Avance</th><th></th></tr></thead>
  <tbody>{rows.map((r:any)=><tr key={r.id} className="clickable-row" onClick={()=>onSelect(r)}>
   <td><b>{r.task_type==='hito'?'◆ ':''}{r.title}</b>{r.description&&<small>{r.description}</small>}</td>
   {!workId&&<td>{r.work_name}</td>}<td>{r.item_description||'General de obra'}</td><td>{r.responsible||'—'}</td>
   <td>{fmtDate(r.start_date)}</td><td className={r.is_overdue?'danger-text':''}>{fmtDate(r.end_date)}</td>
   <td><span className={`priority ${r.priority}`}>{r.priority}</span></td><td><TaskStatus status={r.status} overdue={r.is_overdue}/></td>
   <td><b>{Math.round(Number(r.progress_percent||0))}%</b></td>
   <td onClick={e=>e.stopPropagation()}><div className="row-actions"><button className="mini-button" onClick={()=>onEdit(r)}>Editar</button><button className="mini-button danger-text" onClick={()=>onDelete(r)}>Eliminar</button></div></td>
  </tr>)}</tbody>
 </table></div>
}

function GanttBoard({rows,works,selected,onSelect,reload}:any){
 const dated=rows.filter((r:any)=>parseDate(r.start_date)&&parseDate(r.end_date));
 const trackRef=useRef<HTMLDivElement|null>(null);
 const [drag,setDrag]=useState<any|null>(null);
 const [cascade,setCascade]=useState(true);

 const groups=useMemo(()=>{
  const map=new Map<string,{id:string;name:string;client:string;start_date:any;end_date:any;progress_percent:number;rows:any[]}>();

  // Primero incorporamos TODAS las obras, aunque todavía no tengan tareas.
  (works||[])
   .filter((w:any)=>String(w.type||'obra')!=='servicio_mensual')
   .filter((w:any)=>Number(w.progress_percent||0)<99.999)
   .forEach((w:any)=>{
    map.set(String(w.id),{
     id:String(w.id),
     name:w.name||'Obra',
     client:w.client_name||'',
     start_date:w.start_date||null,
     end_date:w.end_date||null,
     progress_percent:Number(w.progress_percent||0),
     rows:[]
    });
   });

  // Después agregamos las tareas con fecha dentro de su obra.
  dated.forEach((r:any)=>{
   const key=String(r.work_id||r.work_name||'obra');
   const knownWork=(works||[]).find((w:any)=>String(w.id)===String(r.work_id));
   if(knownWork&&Number(knownWork.progress_percent||0)>=99.999)return;
   if(!map.has(key)){
    map.set(key,{
     id:key,
     name:r.work_name||'Obra',
     client:r.client_name||'',
     start_date:knownWork?.start_date||null,
     end_date:knownWork?.end_date||null,
     progress_percent:Number(knownWork?.progress_percent||0),
     rows:[]
    });
   }
   const g=map.get(key)!;
   if(!g.client&&r.client_name)g.client=r.client_name;
   g.rows.push(r);
  });

  const list=Array.from(map.values());
  list.forEach(g=>g.rows.sort((a:any,b:any)=>(parseDate(a.start_date)?.getTime()||0)-(parseDate(b.start_date)?.getTime()||0)));
  list.sort((a:any,b:any)=>{
   const ad=parseDate(a.start_date)?.getTime()??Number.MAX_SAFE_INTEGER;
   const bd=parseDate(b.start_date)?.getTime()??Number.MAX_SAFE_INTEGER;
   return ad-bd||a.name.localeCompare(b.name,'es');
  });
  return list;
 },[dated,works]);

 const datedWorks=groups.filter((g:any)=>parseDate(g.start_date)&&parseDate(g.end_date));
 if(!dated.length&&!datedWorks.length)return <Empty text="Cargá fechas de inicio y fin en las obras o en sus tareas para visualizar el cronograma."/>;

 const today=new Date();today.setHours(12,0,0,0);
 const workStarts=datedWorks.map((g:any)=>parseDate(g.start_date)!.getTime());
 const workEnds=datedWorks.map((g:any)=>parseDate(g.end_date)!.getTime());
 const starts=[...dated.map((r:any)=>parseDate(r.start_date)!.getTime()),...workStarts];
 const ends=[...dated.map((r:any)=>parseDate(r.end_date)!.getTime()),...workEnds];
 const minDate=new Date(Math.min(...starts,today.getTime()));
 const maxDate=new Date(Math.max(...ends,today.getTime()));
 const timelineStart=startOfWeek(startOfMonth(minDate));
 const timelineEnd=endOfWeek(endOfMonth(maxDate));
 const weeks:Date[]=[];for(let d=new Date(timelineStart);d<=timelineEnd;d=addDays(d,7))weeks.push(new Date(d));
 const totalDays=diffDays(timelineEnd,timelineStart)+1;
 const todayLeft=Math.min(100,Math.max(0,diffDays(today,timelineStart)/totalDays*100));
 const todayX=450+(todayLeft/100)*(weeks.length*GANTT_WEEK_PX);

 const months:{label:string;span:number}[]=[];
 weeks.forEach(w=>{const l=monthLabel(w);const last=months[months.length-1];if(last&&last.label===l)last.span++;else months.push({label:l,span:1})});

 const moveTask=async(r:any,delta:number)=>{
  if(!delta)return;
  const s=parseDate(r.start_date)!;const e=parseDate(r.end_date)!;
  try{
   await api.post(`/api/planning/tasks/${r.id}/move`,{start_date:iso(addDays(s,delta)),end_date:iso(addDays(e,delta)),cascade});
   await reload();
  }catch(err:any){alert(err.message||String(err))}
 };

 return <div className="gantt-pro-wrap">
  <div className="gantt-pro-topline">
   <div className="gantt-pro-legend"><span><i className="dot blue"/> En ejecución</span><span><i className="dot green"/> Completada</span><span><i className="dot yellow"/> Pendiente / pausada</span><span><i className="dot red"/> Vencida</span><span><i className="diamond"/> Hito</span></div>
   <label className="cascade-toggle"><input type="checkbox" checked={cascade} onChange={e=>setCascade(e.target.checked)}/> Reprogramar sucesoras al mover</label>
  </div>
  <div className="gantt-pro-shell">
   <div className="gantt-pro-table gantt-global-today-host" style={{'--gantt-timeline-width':`${weeks.length*GANTT_WEEK_PX}px`} as any}>
    {today>=timelineStart&&today<=timelineEnd&&<div className="gantt-today-global" style={{left:`${todayX}px`}}><span>Hoy</span></div>}
    <div className="gantt-pro-head gantt-pro-grid">
     <div className="gantt-left-head"><strong>Obra / tarea</strong><span>plazo general y tareas de ejecución</span></div>
     <div className="gantt-right-head">
      <div className="gantt-months" style={{gridTemplateColumns:`repeat(${weeks.length},${GANTT_WEEK_PX}px)`}}>{months.map((m,i)=><div className="gantt-month" key={i} style={{gridColumn:`span ${m.span}`}}>{m.label}</div>)}</div>
      <div className="gantt-weeks" style={{gridTemplateColumns:`repeat(${weeks.length},${GANTT_WEEK_PX}px)`}}>{weeks.map((w,i)=><div className="gantt-week" key={i}><b>{shortDate(w)} – {shortDate(addDays(w,6))}</b><span>Semana {Math.ceil(diffDays(w,new Date(w.getFullYear(),0,1,12))/7)+1}</span></div>)}</div>
     </div>
    </div>

    {groups.map((g,gi)=><div className="gantt-group" key={gi}>
     {parseDate(g.start_date)&&parseDate(g.end_date)?(()=>{
      const ws=parseDate(g.start_date)!;const we=parseDate(g.end_date)!;
      const workLeft=diffDays(ws,timelineStart)/totalDays*100;
      const workWidth=Math.max(1.3,(diffDays(we,ws)+1)/totalDays*100);
      const workProgress=Math.max(0,Math.min(100,Number(g.progress_percent||0)));
      return <div className="gantt-work-main-row gantt-pro-grid">
       <div className="gantt-work-main-info">
        <span className="gantt-group-kicker">OBRA</span>
        <b>{g.name}</b>
        <small>{g.client}</small>
        <div className="gantt-work-main-meta"><span>{fmtDate(g.start_date)} → {fmtDate(g.end_date)}</span><strong>{Math.round(workProgress)}% ejecutado</strong></div>
       </div>
       <div className="gantt-work-main-track">
        <div className="gantt-work-main-bar" style={{left:`${workLeft}%`,width:`${workWidth}%`}}>
         <div className="gantt-work-main-fill" style={{width:`${workProgress}%`}}/>
         <div className="gantt-work-main-label"><span>{fmtDate(g.start_date)}</span><b>{Math.round(workProgress)}%</b><span>{fmtDate(g.end_date)}</span></div>
        </div>
       </div>
      </div>
     })():<div className="gantt-work-main-row gantt-pro-grid">
      <div className="gantt-work-main-info">
       <span className="gantt-group-kicker">OBRA</span><b>{g.name}</b><small>{g.client}</small>
       <div className="gantt-work-main-meta"><span>Sin fecha de inicio / fin</span><strong>{Math.round(Number(g.progress_percent||0))}% ejecutado</strong></div>
      </div>
      <div className="gantt-work-main-track gantt-work-no-dates"><span>Cargá Inicio y Fin en Obras</span></div>
     </div>}
     {g.rows.map((r:any)=>{
      const sd=parseDate(r.start_date)!;const ed=parseDate(r.end_date)!;
      const left=diffDays(sd,timelineStart)/totalDays*100;
      const width=Math.max(1.3,(diffDays(ed,sd)+1)/totalDays*100);
      const progress=Math.max(0,Math.min(100,Number(r.progress_percent||0)));
      const tone=r.is_overdue?'overdue':r.status==='completada'?'done':r.status==='en_ejecucion'?'active':'pending';
      const isMilestone=r.task_type==='hito';
      return <div className={`gantt-row-pro gantt-pro-grid ${selected?.id===r.id?'selected':''}`} key={r.id}>
       <div className="gantt-row-info" onClick={()=>onSelect(r)}>
        <div className="gantt-task-title">{isMilestone?'◆ ':''}{r.title}</div>
        <div className="gantt-task-meta"><span>{r.item_description||'General de obra'}</span><span>{r.responsible||'Sin responsable'}</span><span>{fmtDate(r.start_date)} → {fmtDate(r.end_date)}</span></div>
        {!!r.predecessors?.length&&<div className="dependency-mini">↳ Depende de: {r.predecessors.map((x:any)=>x.title).join(', ')}</div>}
       </div>
       <div className="gantt-row-track-wrap">
        <div className="gantt-row-track" ref={trackRef} style={{gridTemplateColumns:`repeat(${weeks.length},${GANTT_WEEK_PX}px)`}}>
         {weeks.map((_:Date,i:number)=><div className="gantt-cell" key={i}/>)}
         
         {isMilestone?
          <button className={`gantt-milestone ${tone}`} style={{left:`${left}%`}} title={r.title} onClick={()=>onSelect(r)}>◆</button>
          :<div className={`gantt-bar-pro ${tone} ${selected?.id===r.id?'selected':''}`} style={{left:`${left}%`,width:`${width}%`}}
             onClick={()=>onSelect(r)}
             onPointerDown={e=>{e.currentTarget.setPointerCapture(e.pointerId);setDrag({id:r.id,startX:e.clientX,row:r})}}
             onPointerUp={async e=>{if(!drag||drag.id!==r.id)return;const rect=e.currentTarget.parentElement?.getBoundingClientRect();const dx=e.clientX-drag.startX;setDrag(null);if(rect&&Math.abs(dx)>5){const delta=Math.round(dx/rect.width*totalDays);await moveTask(r,delta)}else onSelect(r)}}>
            <div className="gantt-bar-fill" style={{width:`${progress}%`}}/><span className="gantt-bar-label">{progress}%</span>
           </div>}
        </div>
       </div>
      </div>
     })}
    </div>)}
   </div>
  </div>
 </div>
}

function CalendarView({rows,onSelect}:any){
 const dated=rows.filter((r:any)=>r.start_date);
 const today=new Date();today.setHours(12,0,0,0);
 const [monthOffset,setMonthOffset]=useState(0);
 const focus=new Date(today.getFullYear(),today.getMonth()+monthOffset,1,12);
 const first=startOfWeek(startOfMonth(focus));
 const days=Array.from({length:42},(_,i)=>addDays(first,i));

 return <div className="calendar-pro">
  <div className="calendar-head"><button className="ghost-button" onClick={()=>setMonthOffset(x=>x-1)}>←</button><h3>{monthLabel(focus)}</h3><button className="ghost-button" onClick={()=>setMonthOffset(x=>x+1)}>→</button></div>
  <div className="calendar-weekdays">{['Lun','Mar','Mié','Jue','Vie','Sáb','Dom'].map(x=><b key={x}>{x}</b>)}</div>
  <div className="calendar-grid">{days.map(d=>{
   const events=dated.filter((r:any)=>String(r.start_date).slice(0,10)===iso(d));
   const outside=d.getMonth()!==focus.getMonth();
   return <div className={`calendar-day ${outside?'outside':''} ${iso(d)===iso(today)?'today':''}`} key={iso(d)}><span className="calendar-number">{d.getDate()}</span>{events.slice(0,4).map((r:any)=><button key={r.id} className={`calendar-event ${r.is_overdue?'overdue':r.status}`} onClick={()=>onSelect(r)}>{r.task_type==='hito'?'◆ ':''}{r.title}</button>)}{events.length>4&&<small>+{events.length-4} más</small>}</div>
  })}</div>
 </div>
}

function TaskDrawer({task,close,edit,remove,duplicate,complete}:any){
 return <div className="task-drawer-backdrop" onMouseDown={e=>{if(e.target===e.currentTarget)close()}}>
  <aside className="task-drawer">
   <div className="task-drawer-head"><div><span className="eyebrow">{task.task_type==='hito'?'HITO':'TAREA'}</span><h2>{task.title}</h2><p>{task.work_name}</p></div><button className="close-button" onClick={close}>×</button></div>
   <div className="drawer-actions"><button className="primary-button" onClick={edit}>Editar</button>{task.status!=='completada'&&<button className="ghost-button" onClick={complete}>Completar</button>}<button className="ghost-button" onClick={duplicate}>Duplicar</button><button className="ghost-button danger-text" onClick={remove}>Eliminar</button></div>
   <div className="drawer-status"><TaskStatus status={task.status} overdue={task.is_overdue}/><span className={`priority ${task.priority}`}>{task.priority}</span><b>{Math.round(Number(task.progress_percent||0))}%</b></div>
   <div className="drawer-grid"><Info l="Ítem" v={task.item_description||'General de obra'}/><Info l="Responsable" v={task.responsible||'Sin responsable'}/><Info l="Inicio" v={fmtDate(task.start_date)}/><Info l="Fin" v={fmtDate(task.end_date)}/></div>
   {task.description&&<section><h4>Descripción</h4><p>{task.description}</p></section>}
   <section><h4>Antecesoras</h4>{task.predecessors?.length?<div className="dependency-list">{task.predecessors.map((x:any)=><div key={x.id}><b>← {x.title}</b><span>{fmtDate(x.end_date)}</span></div>)}</div>:<p className="muted">No depende de otra tarea.</p>}</section>
   <section><h4>Sucesoras</h4>{task.successors?.length?<div className="dependency-list">{task.successors.map((x:any)=><div key={x.id}><b>→ {x.title}</b><span>{fmtDate(x.start_date)}</span></div>)}</div>:<p className="muted">No tiene tareas sucesoras.</p>}</section>
   {task.notes&&<section><h4>Notas</h4><p>{task.notes}</p></section>}
  </aside>
 </div>
}

function Info({l,v}:{l:string;v:any}){return <div><span>{l}</span><b>{v||'—'}</b></div>}

function TaskModal({initial,rows,works,fixedWorkId,close,done}:any){
 const [items,setItems]=useState<any[]>([]);
 const [saving,setSaving]=useState(false);
 const [f,setF]=useState<any>({
  work_id:fixedWorkId||initial?.work_id||works[0]?.id||'',
  work_item_id:initial?.work_item_id||'',
  title:initial?.title||'',description:initial?.description||'',responsible:initial?.responsible||'',
  start_date:initial?.start_date?String(initial.start_date).slice(0,10):iso(new Date()),
  end_date:initial?.end_date?String(initial.end_date).slice(0,10):iso(new Date()),
  status:initial?.status||'pendiente',priority:initial?.priority||'media',
  progress_percent:String(initial?.progress_percent??0),notes:initial?.notes||'',
  task_type:initial?.task_type||'tarea',
  predecessor_ids:(initial?.predecessors||[]).map((x:any)=>x.id)
 });

 useEffect(()=>{if(!f.work_id){setItems([]);return}api.list<any>('work_items',`?limit=500&work_id=${f.work_id}`).then(setItems).catch(()=>setItems([]))},[f.work_id]);
 const candidates=(rows||[]).filter((x:any)=>x.work_id===f.work_id&&x.id!==initial?.id);
 const isOneDayTask=f.task_type==='tarea'&&!!f.start_date&&!!f.end_date&&f.start_date===f.end_date;

 const togglePred=(id:string)=>setF({...f,predecessor_ids:f.predecessor_ids.includes(id)?f.predecessor_ids.filter((x:string)=>x!==id):[...f.predecessor_ids,id]});
 const save=async()=>{
  if(!f.work_id||!String(f.title).trim())return;
  setSaving(true);
  try{
   const payload={...f,work_item_id:f.work_item_id||null,progress_percent:Number(f.progress_percent||0),end_date:f.task_type==='hito'?f.start_date:f.end_date};
   if(initial)await api.update('planning/tasks',initial.id,payload);else await api.create('planning/tasks',payload);
   await done();
  }catch(e:any){alert(e.message||String(e))}finally{setSaving(false)}
 };

 return <div className="modal-backdrop"><div className="modal planning-modal">
  <div className="modal-head"><div><span className="eyebrow">{initial?'EDITAR':'NUEVA'}</span><h2>{initial?'Editar tarea':'Nueva tarea / hito'}</h2></div><button className="close-button" onClick={close}>×</button></div>
  <div className="form-grid">
   <label className="field"><span>Obra *</span><select disabled={!!fixedWorkId} value={f.work_id} onChange={e=>setF({...f,work_id:e.target.value,work_item_id:'',predecessor_ids:[]})}><option value="">Seleccionar…</option>{works.map((w:any)=><option key={w.id} value={w.id}>{w.name}</option>)}</select></label>
   <label className="field"><span>Tipo</span><select value={f.task_type} onChange={e=>setF({...f,task_type:e.target.value,end_date:e.target.value==='hito'?f.start_date:f.end_date})}><option value="tarea">Tarea</option><option value="hito">Hito puntual</option></select></label>
   <label className="field"><span>Ítem asociado</span><select value={f.work_item_id} onChange={e=>setF({...f,work_item_id:e.target.value})}><option value="">General de obra</option>{items.map((x:any)=><option key={x.id} value={x.id}>{x.description}</option>)}</select></label>
   <label className="field"><span>Responsable</span><input value={f.responsible} onChange={e=>setF({...f,responsible:e.target.value})}/></label>
   <label className="field full"><span>Tarea *</span><input value={f.title} onChange={e=>setF({...f,title:e.target.value})}/></label>
   <label className="field full"><span>Descripción</span><textarea rows={2} value={f.description} onChange={e=>setF({...f,description:e.target.value})}/></label>
   <label className="field"><span>Inicio</span><input type="date" value={f.start_date} onChange={e=>setF({...f,start_date:e.target.value,end_date:f.task_type==='hito'?e.target.value:f.end_date})}/></label>
   <label className="field"><span>Fin</span><input type="date" disabled={f.task_type==='hito'} value={f.task_type==='hito'?f.start_date:f.end_date} onChange={e=>setF({...f,end_date:e.target.value})}/></label>
   {isOneDayTask&&<div className="field full one-day-hint"><div><b>Actividad puntual de un día</b><span>Como Inicio y Fin son la misma fecha, conviene mostrarla como un hito ◆ en el cronograma.</span></div><button type="button" className="mini-button" onClick={()=>setF({...f,task_type:'hito',end_date:f.start_date})}>Convertir en hito</button></div>}
   <label className="field"><span>Estado</span><select value={f.status} onChange={e=>setF({...f,status:e.target.value,progress_percent:e.target.value==='completada'?'100':f.progress_percent})}><option value="pendiente">Pendiente</option><option value="en_ejecucion">En ejecución</option><option value="pausada">Pausada</option><option value="completada">Completada</option></select></label>
   <label className="field"><span>Prioridad</span><select value={f.priority} onChange={e=>setF({...f,priority:e.target.value})}><option value="baja">Baja</option><option value="media">Media</option><option value="alta">Alta</option><option value="critica">Crítica</option></select></label>
   <label className="field"><span>Avance %</span><input type="number" min="0" max="100" value={f.progress_percent} onChange={e=>setF({...f,progress_percent:e.target.value})}/></label>
   <div className="field"></div>
   <div className="field full"><span>Antecesoras (Fin → Inicio)</span><div className="predecessor-picker">{candidates.length?candidates.map((x:any)=><label key={x.id} className={f.predecessor_ids.includes(x.id)?'checked':''}><input type="checkbox" checked={f.predecessor_ids.includes(x.id)} onChange={()=>togglePred(x.id)}/><span><b>{x.title}</b><small>{fmtDate(x.start_date)} → {fmtDate(x.end_date)}</small></span></label>):<div className="muted">No hay otras tareas en esta obra todavía.</div>}</div></div>
   <label className="field full"><span>Notas</span><textarea rows={2} value={f.notes} onChange={e=>setF({...f,notes:e.target.value})}/></label>
  </div>
  <div className="modal-note">Las sucesoras se calculan automáticamente. Los hitos se muestran como ◆ en una fecha puntual; las tareas normales se muestran como barras. Si movés una barra en el Gantt y dejás activado “Reprogramar sucesoras”, las tareas dependientes se desplazan la misma cantidad de días.</div>
  <div className="modal-actions"><button className="ghost-button" onClick={close}>Cancelar</button><button className="primary-button" disabled={saving||!f.work_id||!String(f.title).trim()} onClick={save}>{saving?'Guardando…':'Guardar'}</button></div>
 </div></div>
}
