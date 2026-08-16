from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# BACKEND
p = ROOT / 'backend/app/routers/work_detail.py'
t = p.read_text(encoding='utf-8')

old = '        docs = _rows(cur, "SELECT * FROM {}.work_documents WHERE work_id=%s ORDER BY document_date DESC, created_at DESC", [work_id])\n        recv = _rows(cur, "SELECT * FROM {}.receivables WHERE work_id=%s ORDER BY due_date DESC NULLS LAST, created_at DESC", [work_id])'
new = '        docs = _rows(cur, "SELECT * FROM {}.work_documents WHERE work_id=%s ORDER BY document_date DESC, created_at DESC", [work_id])\n        checklist = _rows(cur, "SELECT * FROM {}.work_checklist WHERE work_id=%s ORDER BY created_at", [work_id])\n        recv = _rows(cur, "SELECT * FROM {}.receivables WHERE work_id=%s ORDER BY due_date DESC NULLS LAST, created_at DESC", [work_id])'
if old not in t:
    raise SystemExit('ERROR: no encontré docs/recv en work_detail.py')
t = t.replace(old, new, 1)

old = '        "documents": docs,\n        "receivables": recv,'
new = '        "documents": docs,\n        "checklist": checklist,\n        "receivables": recv,'
if old not in t:
    raise SystemExit('ERROR: no encontré documents en response de work_detail.py')
t = t.replace(old, new, 1)

if 'class WorkChecklistUpdate(BaseModel):' not in t:
    anchor = '\n\nclass CostCreate(BaseModel):'
    block = '''\n\nCHECKLIST_TYPES = {\n    "presupuesto": "Presupuesto presentado",\n    "nota": "Nota presentada",\n    "memoria_descriptiva": "Memoria descriptiva",\n    "contrato": "Contrato",\n    "certificacion": "Certificación",\n    "factura": "Factura",\n    "cobro": "Cobro",\n}\n\n\nclass WorkChecklistUpdate(BaseModel):\n    completed: bool = True\n    completed_date: date | None = None\n    notes: str | None = None\n\n\n@router.put("/{work_id}/checklist/{item_type}")\ndef update_work_checklist(work_id: UUID, item_type: str, body: WorkChecklistUpdate):\n    if item_type not in CHECKLIST_TYPES:\n        raise HTTPException(400, "Tipo de checklist inválido")\n\n    completed_date = body.completed_date\n    if body.completed and completed_date is None:\n        completed_date = date.today()\n    if not body.completed:\n        completed_date = None\n\n    with db_cursor() as cur:\n        cur.execute(sql.SQL("SELECT id FROM {}.works WHERE id=%s").format(S), [work_id])\n        if not cur.fetchone():\n            raise HTTPException(404, "Obra no encontrada")\n\n        cur.execute(sql.SQL("""\n            INSERT INTO {}.work_checklist\n              (work_id,item_type,completed,completed_date,notes)\n            VALUES (%s,%s,%s,%s,%s)\n            ON CONFLICT (work_id,item_type)\n            DO UPDATE SET\n              completed=EXCLUDED.completed,\n              completed_date=EXCLUDED.completed_date,\n              notes=EXCLUDED.notes,\n              updated_at=now()\n            RETURNING *\n        """).format(S), [work_id, item_type, body.completed, completed_date, body.notes])\n        return cur.fetchone()\n'''
    idx = t.find(anchor)
    if idx == -1:
        raise SystemExit('ERROR: no encontré CostCreate en work_detail.py')
    t = t[:idx] + block + t[idx:]

p.write_text(t, encoding='utf-8')

# FRONT
p = ROOT / 'front/src/components/WorkDetail.tsx'
t = p.read_text(encoding='utf-8')
start = t.find('function Summary({d,reload}')
end = t.find('\nfunction Info(', start)
if start == -1 or end == -1:
    raise SystemExit('ERROR: no encontré Summary en WorkDetail.tsx')

summary = r'''function Summary({d,reload}:{d:any;reload:()=>void}){
 const w=d.work,m=d.metrics;
 const budget=Number(w.estimated_cost||0), real=Number(m.real_cost||0);
 const change=async(field:string,value:any)=>{try{await api.update('works',w.id,{[field]:value});reload()}catch(e:any){alert(e.message)}};
 const defs=[
  ['presupuesto','Presupuesto presentado'],
  ['nota','Nota presentada'],
  ['memoria_descriptiva','Memoria descriptiva'],
  ['contrato','Contrato'],
  ['certificacion','Certificación'],
  ['factura','Factura'],
  ['cobro','Cobro'],
 ] as [string,string][];
 const cmap=Object.fromEntries((d.checklist||[]).map((x:any)=>[x.item_type,x]));
 const save=async(key:string,completed:boolean,completedDate?:string)=>{
  try{
   await fetch(`${(process.env.NEXT_PUBLIC_API_URL||'https://dirac-admin.onrender.com').replace(/\/$/,'')}/api/works/${w.id}/checklist/${key}`,{
    method:'PUT',
    headers:{'Content-Type':'application/json',...(process.env.NEXT_PUBLIC_API_KEY?{'X-API-Key':process.env.NEXT_PUBLIC_API_KEY}:{})},
    body:JSON.stringify({completed,completed_date:completed?(completedDate||new Date().toISOString().slice(0,10)):null})
   }).then(async r=>{if(!r.ok){const b=await r.json().catch(()=>({}));throw new Error(b.detail||`Error ${r.status}`)}});
   await reload();
  }catch(e:any){alert(e.message||String(e))}
 };
 const doneCount=defs.filter(([k])=>!!cmap[k]?.completed).length;
 return <div className="two-col">
  <Card><SectionTitle title="Estado y números de la obra"/><div className="detail-grid"><Info l="Inicio" v={dateAR(w.start_date)}/><Info l="Fin" v={dateAR(w.end_date)}/><Info l="Costo estimado" v={money(w.estimated_cost)}/><Info l="Costo real" v={money(real)}/><Info l="Monto ejecutado" v={money(m.executed_amount)}/><Info l="Disponible a facturar" v={money(m.available_to_invoice)}/><Info l="Facturado acumulado" v={money(m.invoiced)}/><Info l="Pendiente de cobro" v={money(m.pending_collection)}/></div><label className="field" style={{marginTop:16}}><span>Estado de ejecución</span><select value={w.execution_status||'pendiente'} onChange={e=>change('execution_status',e.target.value)}><option value="pendiente">Pendiente</option><option value="en_ejecucion">En ejecución</option><option value="pausada">Pausada</option><option value="finalizada">Finalizada</option></select></label></Card>
  <Card>
   <SectionTitle title="Checklist administrativo" subtitle="Control de hitos y fecha de registro de la obra."/>
   <div style={{borderTop:'1px solid #e3e8ef'}}>{defs.map(([key,label])=>{const row=cmap[key]||{};const checked=!!row.completed;const dateValue=row.completed_date?String(row.completed_date).slice(0,10):'';return <div key={key} style={{display:'grid',gridTemplateColumns:'32px minmax(170px,1fr) 150px',alignItems:'center',gap:12,padding:'12px 4px',borderBottom:'1px solid #e3e8ef'}}><input type="checkbox" checked={checked} style={{width:19,height:19}} onChange={e=>save(key,e.target.checked,dateValue)}/><div><strong style={{fontSize:14}}>{label}</strong><div style={{fontSize:12,color:checked?'#15803d':'#718096',marginTop:2}}>{checked?'Registrado':'Pendiente'}</div></div><input type="date" value={dateValue} disabled={!checked} onChange={e=>save(key,true,e.target.value)} style={{minWidth:0}}/></div>})}</div>
   <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',gap:12,marginTop:14}}><span style={{color:'#718096',fontSize:13}}>Avance administrativo</span><strong>{Math.round(doneCount/defs.length*100)}%</strong></div>
  </Card>
 </div>
}'''

t = t[:start] + summary + t[end:]
p.write_text(t, encoding='utf-8')
print('OK: checklist administrativo de obra aplicado.')
