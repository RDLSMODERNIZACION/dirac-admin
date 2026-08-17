from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# 1) OBRAS: selector arranca en Fecha fin
p = ROOT / "front/src/components/WorksBoard.tsx"
t = p.read_text(encoding="utf-8")
old = "const [sort,setSort]=useState<'risk'|'end'|'pending'>('risk');"
new = "const [sort,setSort]=useState<'risk'|'end'|'pending'>('end');"
if old not in t:
    raise SystemExit("ERROR: no encontré sort inicial en WorksBoard.tsx")
t = t.replace(old, new, 1)
p.write_text(t, encoding="utf-8")

# 2) SERVICIOS: selector arranca en Fecha fin
p = ROOT / "front/src/components/ServicesBoard.tsx"
t = p.read_text(encoding="utf-8")
old = "const [sort,setSort]=useState<'risk'|'end'|'pending'>('risk');"
new = "const [sort,setSort]=useState<'risk'|'end'|'pending'>('end');"
if old not in t:
    raise SystemExit("ERROR: no encontré sort inicial en ServicesBoard.tsx")
t = t.replace(old, new, 1)
p.write_text(t, encoding="utf-8")

# 3) TRABAJOS > TODOS: ordenar también por fecha fin ascendente
p = ROOT / "front/src/components/Jobs.tsx"
t = p.read_text(encoding="utf-8")

t = t.replace(
    "type Work = { id:string; name:string; client_id:string; status:string; contract_amount:number; type?:string };",
    "type Work = { id:string; name:string; client_id:string; status:string; contract_amount:number; type?:string; end_date?:string|null };"
)
t = t.replace(
    "type Service = { id:string; name:string; client_id:string; status:string; contract_amount:number; service_type?:string };",
    "type Service = { id:string; name:string; client_id:string; status:string; contract_amount:number; service_type?:string; end_date?:string|null };"
)
t = t.replace(
    "  subtype:string;\n};",
    "  subtype:string;\n  end_date?:string|null;\n};"
)

old_rows = """  const rows=useMemo<Unified[]>(()=>[
    ...works.map(w=>({id:w.id,kind:'obra' as const,name:w.name,client_id:w.client_id,status:w.status,value:Number(w.contract_amount||0),subtype:w.type||'obra'})),
    ...services.map(s=>({id:s.id,kind:'servicio' as const,name:s.name,client_id:s.client_id,status:s.status,value:Number(s.contract_amount||0),subtype:s.service_type||'servicio'})),
  ],[works,services]);
"""
new_rows = """  const rows=useMemo<Unified[]>(()=>[
    ...works.map(w=>({id:w.id,kind:'obra' as const,name:w.name,client_id:w.client_id,status:w.status,value:Number(w.contract_amount||0),subtype:w.type||'obra',end_date:w.end_date||null})),
    ...services.map(s=>({id:s.id,kind:'servicio' as const,name:s.name,client_id:s.client_id,status:s.status,value:Number(s.contract_amount||0),subtype:s.service_type||'servicio',end_date:s.end_date||null})),
  ],[works,services]);
"""
if old_rows not in t:
    raise SystemExit("ERROR: no encontré armado de rows en Jobs.tsx")
t = t.replace(old_rows, new_rows, 1)

old_filtered = """  const filtered=useMemo(()=>{
    const q=query.trim().toLowerCase();
    return !q?rows:rows.filter(r=>`${r.name} ${clientMap[r.client_id]||''} ${r.kind} ${r.status}`.toLowerCase().includes(q));
  },[rows,query,clientMap]);
"""
new_filtered = """  const filtered=useMemo(()=>{
    const q=query.trim().toLowerCase();
    const base=!q?rows:rows.filter(r=>`${r.name} ${clientMap[r.client_id]||''} ${r.kind} ${r.status}`.toLowerCase().includes(q));
    return [...base].sort((a,b)=>{
      const ad=a.end_date?new Date(`${String(a.end_date).slice(0,10)}T12:00:00`).getTime():Number.MAX_SAFE_INTEGER;
      const bd=b.end_date?new Date(`${String(b.end_date).slice(0,10)}T12:00:00`).getTime():Number.MAX_SAFE_INTEGER;
      return ad-bd;
    });
  },[rows,query,clientMap]);
"""
if old_filtered not in t:
    raise SystemExit("ERROR: no encontré filtered en Jobs.tsx")
t = t.replace(old_filtered, new_filtered, 1)

# Mostrar fecha fin en "Todos" para que el criterio sea visible
t = t.replace(
    "<thead><tr><th>Trabajo</th><th>Cliente</th><th>Tipo</th><th>Modalidad</th><th>Estado</th><th>Valor</th></tr></thead>",
    "<thead><tr><th>Trabajo</th><th>Cliente</th><th>Tipo</th><th>Modalidad</th><th>Fecha fin</th><th>Estado</th><th>Valor</th></tr></thead>"
)
t = t.replace(
    "<td>{r.subtype}</td>\n            <td><Status tone={r.status==='activo'?'green':r.status==='cancelado'?'red':'blue'}>{r.status}</Status></td>",
    "<td>{r.subtype}</td>\n            <td>{r.end_date?new Date(`${String(r.end_date).slice(0,10)}T12:00:00`).toLocaleDateString('es-AR'):'—'}</td>\n            <td><Status tone={r.status==='activo'?'green':r.status==='cancelado'?'red':'blue'}>{r.status}</Status></td>"
)

p.write_text(t, encoding="utf-8")

print("OK: Trabajos, Obras y Servicios ordenan por Fecha fin de forma predeterminada.")
