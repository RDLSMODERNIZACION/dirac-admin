from pathlib import Path
ROOT=Path.cwd()

# works_board.py
p=ROOT/'backend/app/routers/works_board.py'
t=p.read_text(encoding='utf-8')
old='          COALESCE(costs.real_cost,0) AS real_cost,\n          COALESCE(overdue.overdue_amount,0) AS overdue_amount\n\n        FROM {}.works w\n'
new="          COALESCE(costs.real_cost,0) AS real_cost,\n          COALESCE(overdue.overdue_amount,0) AS overdue_amount,\n          COALESCE(admin.checklist,'{}'::jsonb) AS checklist\n\n        FROM {}.works w\n"
if old not in t: raise SystemExit('ERROR: SELECT works_board no encontrado')
t=t.replace(old,new,1)
needle='        LEFT JOIN LATERAL (\n          SELECT COALESCE(SUM(\n            GREATEST(0,r.amount-COALESCE(p.paid,0))\n          ),0) AS overdue_amount\n'
admin="        LEFT JOIN LATERAL (\n          SELECT COALESCE(\n            jsonb_object_agg(\n              wc.item_type,\n              jsonb_build_object('completed',wc.completed,'completed_date',wc.completed_date)\n            ) FILTER (WHERE wc.item_type IN ('presupuesto','contrato','certificacion','factura','cobro')),\n            '{}'::jsonb\n          ) AS checklist\n          FROM {}.work_checklist wc\n          WHERE wc.work_id=w.id\n        ) admin ON true\n\n"
idx=t.find(needle)
if idx<0: raise SystemExit('ERROR: overdue works_board no encontrado')
t=t[:idx]+admin+t[idx:]
old='""").format(S,S,S,S,S,S,S,S,S,S,S))'
new='""").format(S,S,S,S,S,S,S,S,S,S,S,S))'
if old not in t: raise SystemExit('ERROR: format works_board no encontrado')
t=t.replace(old,new,1)
p.write_text(t,encoding='utf-8')

# Jobs.tsx
p=ROOT/'front/src/components/Jobs.tsx'
t=p.read_text(encoding='utf-8')
t=t.replace("type Tab = 'all' | 'works' | 'services';","type Tab = 'admin' | 'works' | 'services';")
t=t.replace("const [tab,setTab]=useState<Tab>('all');","const [tab,setTab]=useState<Tab>('admin');")
old="  const [query,setQuery]=useState('');\n  const [selected,setSelected]=useState<{kind:'obra'|'servicio';id:string}|null>(null);\n"
new="  const [query,setQuery]=useState('');\n  const [adminRows,setAdminRows]=useState<any[]>([]);\n  const [selected,setSelected]=useState<{kind:'obra'|'servicio';id:string}|null>(null);\n"
if old not in t: raise SystemExit('ERROR: state Jobs')
t=t.replace(old,new,1)
old="      const [w,s,c]=await Promise.all([\n        api.list<Work>('works','?limit=500'),\n        api.list<Service>('services','?limit=500'),\n        api.list<Client>('clients','?limit=500'),\n      ]);\n      setWorks(w); setServices(s); setClients(c);\n"
new="      const [w,s,c,admin]=await Promise.all([\n        api.list<Work>('works','?limit=500'),\n        api.list<Service>('services','?limit=500'),\n        api.list<Client>('clients','?limit=500'),\n        api.get<any>('/api/works-board'),\n      ]);\n      setWorks(w); setServices(s); setClients(c); setAdminRows(admin.works||[]);\n"
if old not in t: raise SystemExit('ERROR: load Jobs')
t=t.replace(old,new,1)
start=t.find('  const filtered=useMemo(()=>{')
end=t.find("\n\n  if(selected?.kind==='obra')",start)
if start<0 or end<0: raise SystemExit('ERROR: filtered Jobs')
t=t[:start]+"  const filteredAdmin=useMemo(()=>{\n    const q=query.trim().toLowerCase();\n    return [...adminRows]\n      .filter((r:any)=>!q||`${r.name} ${r.client_name||''}`.toLowerCase().includes(q))\n      .sort((a:any,b:any)=>{\n        const ad=a.end_date?new Date(`${String(a.end_date).slice(0,10)}T12:00:00`).getTime():Number.MAX_SAFE_INTEGER;\n        const bd=b.end_date?new Date(`${String(b.end_date).slice(0,10)}T12:00:00`).getTime():Number.MAX_SAFE_INTEGER;\n        return ad-bd;\n      });\n  },[adminRows,query]);\n"+t[end:]
old="      <button className={tab==='all'?'active':''} onClick={()=>setTab('all')}>Todos</button>\n      <button className={tab==='works'?'active':''} onClick={()=>setTab('works')}>Obras</button>\n      <button className={tab==='services'?'active':''} onClick={()=>setTab('services')}>Servicios</button>"
new="      <button className={tab==='admin'?'active':''} onClick={()=>setTab('admin')}>Administración</button>\n      <button className={tab==='works'?'active':''} onClick={()=>setTab('works')}>Obras</button>\n      <button className={tab==='services'?'active':''} onClick={()=>setTab('services')}>Servicios</button>"
if old not in t: raise SystemExit('ERROR: tabs Jobs')
t=t.replace(old,new,1)
start=t.find("    {tab==='all'&&(")
end=t.find("\n    )}\n  </div>;",start)
if start<0 or end<0: raise SystemExit('ERROR: vista Todos Jobs')
end=end+len("\n    )}")
t=t[:start]+'    {tab===\'admin\'&&(\n      error?<ErrorBox message={error} onRetry={load}/>:loading?<Loading/>:<Card>\n        <div className="table-toolbar">\n          <input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Buscar obra o cliente…"/>\n          <span className="record-count">{filteredAdmin.length} obras</span>\n        </div>\n        {filteredAdmin.length===0?<Empty text="Todavía no hay obras."/>:<div className="table-wrap"><table className="admin-works-table">\n          <thead><tr><th>Obra</th><th>Cliente</th><th>Fecha fin</th><th>Presupuesto</th><th>Contrato</th><th>Certificación</th><th>Factura</th><th>Cobro</th><th>Avance adm.</th></tr></thead>\n          <tbody>{filteredAdmin.map((r:any)=>{\n            const checklist=r.checklist||{};\n            const defs=[[\'presupuesto\',\'Presupuesto\'],[\'contrato\',\'Contrato\'],[\'certificacion\',\'Certificación\'],[\'factura\',\'Factura\'],[\'cobro\',\'Cobro\']] as [string,string][];\n            const done=defs.filter(([k])=>!!checklist[k]?.completed).length;\n            const progress=Math.round(done/defs.length*100);\n            return <tr key={r.id} className="clickable-row" onClick={()=>setSelected({kind:\'obra\',id:r.id})}>\n              <td><b>{r.name}</b></td>\n              <td>{r.client_name||\'—\'}</td>\n              <td>{r.end_date?new Date(`${String(r.end_date).slice(0,10)}T12:00:00`).toLocaleDateString(\'es-AR\'):\'—\'}</td>\n              {defs.map(([k])=><td key={k}><AdminCheck row={checklist[k]}/></td>)}\n              <td><div className="admin-progress-cell"><b>{progress}%</b><span><i style={{width:`${progress}%`}}/></span></div></td>\n            </tr>\n          })}</tbody>\n        </table></div>}\n      </Card>\n    )}'+t[end:]
anchor='\nexport function Jobs(){'
if 'function AdminCheck(' not in t:
    t=t.replace(anchor,'\n'+'function AdminCheck({row}:{row:any}){\n if(!row?.completed)return <span className="admin-check pending">Pendiente</span>;\n const d=row.completed_date?new Date(`${String(row.completed_date).slice(0,10)}T12:00:00`).toLocaleDateString(\'es-AR\'):\'\';\n return <span className="admin-check done">OK<small>{d}</small></span>;\n}\n\n'+'export function Jobs(){',1)
p.write_text(t,encoding='utf-8')

# CSS
p=ROOT/'front/app/globals.css'
t=p.read_text(encoding='utf-8')
if '/* TRABAJOS ADMINISTRACION CHECKLIST */' not in t:
    t+='\n/* TRABAJOS ADMINISTRACION CHECKLIST */\n.admin-works-table th{white-space:nowrap}\n.admin-check{display:inline-flex;flex-direction:column;align-items:flex-start;gap:2px;font-size:12px;font-weight:800}\n.admin-check.done{color:#15803d}\n.admin-check.done small{font-size:10px;font-weight:500;color:#64748b}\n.admin-check.pending{color:#94a3b8;font-weight:700}\n.admin-progress-cell{display:grid;gap:6px;min-width:90px}\n.admin-progress-cell span{height:6px;border-radius:999px;background:#e7edf5;overflow:hidden;display:block}\n.admin-progress-cell span i{height:100%;display:block;background:currentColor;border-radius:999px}\n'
p.write_text(t,encoding='utf-8')
print('OK: Administración de obras aplicada.')