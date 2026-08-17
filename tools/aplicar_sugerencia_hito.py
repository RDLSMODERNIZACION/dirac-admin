from pathlib import Path
ROOT=Path.cwd()
p=ROOT/'front/src/components/Planning.tsx'
t=p.read_text(encoding='utf-8')
old=' const candidates=(rows||[]).filter((x:any)=>x.work_id===f.work_id&&x.id!==initial?.id);\n\n const togglePred=(id:string)=>setF({...f,predecessor_ids:f.predecessor_ids.includes(id)?f.predecessor_ids.filter((x:string)=>x!==id):[...f.predecessor_ids,id]});\n'
new=" const candidates=(rows||[]).filter((x:any)=>x.work_id===f.work_id&&x.id!==initial?.id);\n const isOneDayTask=f.task_type==='tarea'&&!!f.start_date&&!!f.end_date&&f.start_date===f.end_date;\n\n const togglePred=(id:string)=>setF({...f,predecessor_ids:f.predecessor_ids.includes(id)?f.predecessor_ids.filter((x:string)=>x!==id):[...f.predecessor_ids,id]});\n"
if old not in t: raise SystemExit('ERROR: bloque candidates no encontrado')
t=t.replace(old,new,1)
old='   <label className="field"><span>Inicio</span><input type="date" value={f.start_date} onChange={e=>setF({...f,start_date:e.target.value,end_date:f.task_type===\'hito\'?e.target.value:f.end_date})}/></label>\n   <label className="field"><span>Fin</span><input type="date" disabled={f.task_type===\'hito\'} value={f.task_type===\'hito\'?f.start_date:f.end_date} onChange={e=>setF({...f,end_date:e.target.value})}/></label>\n   <label className="field"><span>Estado</span>'
new='   <label className="field"><span>Inicio</span><input type="date" value={f.start_date} onChange={e=>setF({...f,start_date:e.target.value,end_date:f.task_type===\'hito\'?e.target.value:f.end_date})}/></label>\n   <label className="field"><span>Fin</span><input type="date" disabled={f.task_type===\'hito\'} value={f.task_type===\'hito\'?f.start_date:f.end_date} onChange={e=>setF({...f,end_date:e.target.value})}/></label>\n   {isOneDayTask&&<div className="field full one-day-hint"><div><b>Actividad puntual de un día</b><span>Como Inicio y Fin son la misma fecha, conviene mostrarla como un hito ◆ en el cronograma.</span></div><button type="button" className="mini-button" onClick={()=>setF({...f,task_type:\'hito\',end_date:f.start_date})}>Convertir en hito</button></div>}\n   <label className="field"><span>Estado</span>'
if old not in t: raise SystemExit('ERROR: bloque fechas del modal no encontrado')
t=t.replace(old,new,1)
old='  <div className="modal-note">Las sucesoras se calculan automáticamente. Si movés una barra en el Gantt y dejás activado “Reprogramar sucesoras”, las tareas dependientes se desplazan la misma cantidad de días.</div>'
new='  <div className="modal-note">Las sucesoras se calculan automáticamente. Los hitos se muestran como ◆ en una fecha puntual; las tareas normales se muestran como barras. Si movés una barra en el Gantt y dejás activado “Reprogramar sucesoras”, las tareas dependientes se desplazan la misma cantidad de días.</div>'
if old in t: t=t.replace(old,new,1)
p.write_text(t,encoding='utf-8')

p=ROOT/'front/app/globals.css'
css=p.read_text(encoding='utf-8')
if '/* SUGERENCIA HITO UN DIA */' not in css:
    css += '\n/* SUGERENCIA HITO UN DIA */\n.one-day-hint{display:flex!important;align-items:center;justify-content:space-between;gap:16px;padding:12px 14px;border:1px solid #d9c7ff;border-radius:10px;background:#f8f5ff}.one-day-hint>div{display:grid;gap:3px}.one-day-hint b{color:#6336c6;font-size:13px}.one-day-hint span{font-size:12px;color:#64748b}.one-day-hint .mini-button{white-space:nowrap}\n'
p.write_text(css,encoding='utf-8')
print('OK: tareas de un día ahora sugieren convertirse en hito.')