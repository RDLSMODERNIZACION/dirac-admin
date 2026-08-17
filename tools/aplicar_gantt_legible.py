from pathlib import Path
p=Path.cwd()/'front/src/components/Planning.tsx'
t=p.read_text(encoding='utf-8')
old='const DAY=86400000;'
new='const DAY=86400000;\nconst GANTT_WEEK_PX=128;'
if old in t and 'GANTT_WEEK_PX' not in t: t=t.replace(old,new,1)
old="   const [tasks,s,w]=await Promise.all([\n    api.get<any[]>(`/api/planning/tasks${workId?`?work_id=${workId}`:''}`),\n    api.get<any>(`/api/planning/summary${workId?`?work_id=${workId}`:''}`),\n    api.list<any>('works','?limit=500')\n   ]);\n   setRows(tasks);setSummary(s);setWorks(w);setError('');\n"
new="   const [tasks,s,w,wb]=await Promise.all([\n    api.get<any[]>(`/api/planning/tasks${workId?`?work_id=${workId}`:''}`),\n    api.get<any>(`/api/planning/summary${workId?`?work_id=${workId}`:''}`),\n    api.list<any>('works','?limit=500'),\n    api.get<any>('/api/works-board')\n   ]);\n   const boardMap=new Map((wb?.works||[]).map((x:any)=>[x.id,x]));\n   const enrichedWorks=(w||[]).map((x:any)=>{\n    const b:any=boardMap.get(x.id);\n    return {...x,progress_percent:b?.progress_percent??0,client_name:b?.client_name||x.client_name||'',is_finished:b?.is_finished??false};\n   });\n   setRows(tasks);setSummary(s);setWorks(enrichedWorks);setError('');\n"
if old not in t: raise SystemExit('ERROR: bloque load de Planning no encontrado')
t=t.replace(old,new,1)
old="  (works||[])\n   .filter((w:any)=>String(w.type||'obra')!=='servicio_mensual')\n   .forEach((w:any)=>{"
new="  (works||[])\n   .filter((w:any)=>String(w.type||'obra')!=='servicio_mensual')\n   .filter((w:any)=>Number(w.progress_percent||0)<99.999)\n   .forEach((w:any)=>{"
if old not in t: raise SystemExit('ERROR: filtro de obras del Gantt no encontrado')
t=t.replace(old,new,1)
old="  dated.forEach((r:any)=>{\n   const key=String(r.work_id||r.work_name||'obra');\n   if(!map.has(key)){\n    map.set(key,{\n     id:key,\n     name:r.work_name||'Obra',\n     client:r.client_name||'',\n     start_date:null,\n     end_date:null,\n     rows:[]\n    });\n   }\n   const g=map.get(key)!;\n   if(!g.client&&r.client_name)g.client=r.client_name;\n   g.rows.push(r);\n  });\n"
new="  dated.forEach((r:any)=>{\n   const key=String(r.work_id||r.work_name||'obra');\n   const knownWork=(works||[]).find((w:any)=>String(w.id)===String(r.work_id));\n   if(knownWork&&Number(knownWork.progress_percent||0)>=99.999)return;\n   if(!map.has(key)){\n    map.set(key,{\n     id:key,\n     name:r.work_name||'Obra',\n     client:r.client_name||'',\n     start_date:knownWork?.start_date||null,\n     end_date:knownWork?.end_date||null,\n     rows:[]\n    });\n   }\n   const g=map.get(key)!;\n   if(!g.client&&r.client_name)g.client=r.client_name;\n   g.rows.push(r);\n  });\n"
if old not in t: raise SystemExit('ERROR: agregado de tareas al Gantt no encontrado')
t=t.replace(old,new,1)
t=t.replace('minmax(82px,1fr)','${GANTT_WEEK_PX}px')
old='<div className="gantt-pro-table">'
new='<div className="gantt-pro-table" style={{\'--gantt-timeline-width\':`${weeks.length*GANTT_WEEK_PX}px`} as any}>'
if old not in t: raise SystemExit('ERROR: gantt-pro-table no encontrado')
t=t.replace(old,new,1)
old='<div className="gantt-left-head"><strong>Tarea</strong><span>ítem, responsable y dependencias</span></div>'
new='<div className="gantt-left-head"><strong>Obra / tarea</strong><span>plazo general y tareas de ejecución</span></div>'
if old in t: t=t.replace(old,new,1)
old='<div className="gantt-group-title">{g.name}<small>{g.client}</small></div>'
new='<div className="gantt-group-title"><div><span className="gantt-group-kicker">OBRA</span><b>{g.name}</b><small>{g.client}</small></div></div>'
if old not in t: raise SystemExit('ERROR: título de grupo no encontrado')
t=t.replace(old,new,1)
p.write_text(t,encoding='utf-8')

p=Path.cwd()/'front/app/globals.css'
css=p.read_text(encoding='utf-8')
if '/* GANTT LEGIBLE + JERARQUIA DE OBRAS */' not in css:
    css+='\n\n/* GANTT LEGIBLE + JERARQUIA DE OBRAS */\n.gantt-pro-shell{overflow-x:auto!important;overflow-y:hidden}\n.gantt-pro-table{width:max-content!important;min-width:100%!important}\n.gantt-pro-grid{grid-template-columns:450px var(--gantt-timeline-width)!important}\n.gantt-right-head,.gantt-row-track-wrap,.gantt-track{width:var(--gantt-timeline-width)!important;min-width:var(--gantt-timeline-width)!important}\n.gantt-months,.gantt-weeks,.gantt-row-track{width:var(--gantt-timeline-width)!important}\n.gantt-week{min-width:128px!important;width:128px!important}\n.gantt-group{border-top:2px solid #d7e0ea}\n.gantt-group-title{background:#eaf1fb!important;padding:14px 22px!important;min-height:64px;display:flex!important;align-items:center}\n.gantt-group-title>div{display:grid;gap:2px}\n.gantt-group-title b{font-size:15px;letter-spacing:.01em;color:#0f2747}\n.gantt-group-title small{font-size:11px;color:#62748b;font-weight:600}\n.gantt-group-kicker{font-size:10px;font-weight:900;letter-spacing:.12em;color:#356dcc}\n.gantt-work-span-row{background:#f4f7fb!important;border-bottom:1px solid #dfe7f0}\n.gantt-work-span-row .gantt-row-info{background:#f4f7fb!important;padding-left:28px!important}\n.gantt-work-span-row .gantt-task-title{font-size:14px;color:#334155}\n.gantt-group .gantt-row-pro:not(.gantt-work-span-row) .gantt-row-info{padding-left:46px!important;position:relative;background:#fff}\n.gantt-group .gantt-row-pro:not(.gantt-work-span-row) .gantt-row-info:before{content:"TAREA";position:absolute;left:20px;top:18px;font-size:8px;font-weight:900;letter-spacing:.08em;color:#94a3b8}\n.gantt-group .gantt-row-pro:not(.gantt-work-span-row){background:#fff}\n.gantt-work-span{z-index:3}\n'
p.write_text(css,encoding='utf-8')
print('OK: cronograma legible, obras 100% ocultas y jerarquía obra/plazo/tareas aplicada.')