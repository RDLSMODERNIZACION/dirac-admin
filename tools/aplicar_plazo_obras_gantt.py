from pathlib import Path
p=Path.cwd()/'front/src/components/Planning.tsx'
t=p.read_text(encoding='utf-8')
old="{view==='gantt'&&<GanttBoard rows={filtered} selected={selected} onSelect={setSelected} reload={load}/>"
new="{view==='gantt'&&<GanttBoard rows={filtered} works={works} selected={selected} onSelect={setSelected} reload={load}/>"
if old not in t: raise SystemExit('ERROR reemplazo 1')
t=t.replace(old,new,1)
old='function GanttBoard({rows,selected,onSelect,reload}:any){'
new='function GanttBoard({rows,works,selected,onSelect,reload}:any){'
if old not in t: raise SystemExit('ERROR reemplazo 2')
t=t.replace(old,new,1)
old=" const groups=useMemo(()=>{\n  const map=new Map<string,{name:string;client:string;rows:any[]}>();\n  dated.forEach((r:any)=>{\n   const key=r.work_id||r.work_name||'obra';\n   if(!map.has(key))map.set(key,{name:r.work_name||'Obra',client:r.client_name||'',rows:[]});\n   map.get(key)!.rows.push(r);\n  });\n  const list=Array.from(map.values());\n  list.forEach(g=>g.rows.sort((a:any,b:any)=>(parseDate(a.start_date)?.getTime()||0)-(parseDate(b.start_date)?.getTime()||0)));\n  return list;\n },[dated]);\n"
new=" const groups=useMemo(()=>{\n  const workMap=new Map((works||[]).map((w:any)=>[w.id,w]));\n  const map=new Map<string,{id:string;name:string;client:string;start_date:any;end_date:any;rows:any[]}>();\n  dated.forEach((r:any)=>{\n   const key=r.work_id||r.work_name||'obra';\n   const w=workMap.get(r.work_id);\n   if(!map.has(key))map.set(key,{id:String(r.work_id||key),name:r.work_name||w?.name||'Obra',client:r.client_name||'',start_date:w?.start_date||null,end_date:w?.end_date||null,rows:[]});\n   map.get(key)!.rows.push(r);\n  });\n  const list=Array.from(map.values());\n  list.forEach(g=>g.rows.sort((a:any,b:any)=>(parseDate(a.start_date)?.getTime()||0)-(parseDate(b.start_date)?.getTime()||0)));\n  return list;\n },[dated,works]);\n"
if old not in t: raise SystemExit('ERROR reemplazo 3')
t=t.replace(old,new,1)
old=' const starts=dated.map((r:any)=>parseDate(r.start_date)!.getTime());\n const ends=dated.map((r:any)=>parseDate(r.end_date)!.getTime());\n const minDate=new Date(Math.min(...starts,today.getTime()));\n const maxDate=new Date(Math.max(...ends,today.getTime()));\n'
new=' const workStarts=groups.map((g:any)=>parseDate(g.start_date)?.getTime()).filter((x:any)=>Number.isFinite(x));\n const workEnds=groups.map((g:any)=>parseDate(g.end_date)?.getTime()).filter((x:any)=>Number.isFinite(x));\n const starts=[...dated.map((r:any)=>parseDate(r.start_date)!.getTime()),...workStarts];\n const ends=[...dated.map((r:any)=>parseDate(r.end_date)!.getTime()),...workEnds];\n const minDate=new Date(Math.min(...starts,today.getTime()));\n const maxDate=new Date(Math.max(...ends,today.getTime()));\n'
if old not in t: raise SystemExit('ERROR reemplazo 4')
t=t.replace(old,new,1)
old='    {groups.map((g,gi)=><div className="gantt-group" key={gi}>\n     <div className="gantt-group-title">{g.name}<small>{g.client}</small></div>\n     {g.rows.map((r:any)=>{'
new='    {groups.map((g,gi)=><div className="gantt-group" key={gi}>\n     <div className="gantt-group-title">{g.name}<small>{g.client}</small></div>\n     {parseDate(g.start_date)&&parseDate(g.end_date)&&(()=>{\n      const ws=parseDate(g.start_date)!;const we=parseDate(g.end_date)!;\n      const workLeft=diffDays(ws,timelineStart)/totalDays*100;\n      const workWidth=Math.max(1.3,(diffDays(we,ws)+1)/totalDays*100);\n      return <div className="gantt-row-pro gantt-pro-grid gantt-work-span-row">\n       <div className="gantt-row-info"><div className="gantt-task-title">Plazo de obra</div><div className="gantt-task-meta"><span>{fmtDate(g.start_date)} → {fmtDate(g.end_date)}</span></div></div>\n       <div className="gantt-track gantt-work-track"><div className="gantt-work-span" style={{left:`${workLeft}%`,width:`${workWidth}%`}}><span>{fmtDate(g.start_date)}</span><b>{g.name}</b><span>{fmtDate(g.end_date)}</span></div>{today>=timelineStart&&today<=timelineEnd&&<div className="gantt-today-line" style={{left:`${todayLeft}%`}}><span>Hoy</span></div>}</div>\n      </div>\n     })()}\n     {g.rows.map((r:any)=>{'
if old not in t: raise SystemExit('ERROR reemplazo 5')
t=t.replace(old,new,1)
p.write_text(t,encoding='utf-8')
p=Path.cwd()/'front/app/globals.css'
css=p.read_text(encoding='utf-8')
if '/* GANTT PLAZO DE OBRAS */' not in css:
    css+='\n\n/* GANTT PLAZO DE OBRAS */\n.gantt-work-span-row{background:#f8fafc}\n.gantt-work-span-row .gantt-row-info{background:#f8fafc}\n.gantt-work-track{position:relative;min-height:58px}\n.gantt-work-span{position:absolute;top:14px;height:30px;border:2px solid #64748b;border-radius:8px;background:rgba(100,116,139,.10);display:flex;align-items:center;justify-content:space-between;gap:10px;padding:0 10px;overflow:hidden;white-space:nowrap;color:#334155;font-size:11px;font-weight:700}\n.gantt-work-span b{font-size:11px;overflow:hidden;text-overflow:ellipsis}\n.gantt-work-span span{font-size:10px;font-weight:600}\n'
p.write_text(css,encoding='utf-8')
print('OK: plazos de obra agregados al cronograma.')