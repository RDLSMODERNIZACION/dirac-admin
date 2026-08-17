from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

p=ROOT/'front/src/components/WorksBoard.tsx'
t=p.read_text(encoding='utf-8')
for old,new in [
("import { ErrorBox, Loading, Status } from './ui';\n","import { ErrorBox, Loading, Status } from './ui';\nimport { NewWorkModal } from './NewJobModals';\n"),
(' const [selected,setSelected]=useState<string|null>(null);\n',' const [selected,setSelected]=useState<string|null>(null);\n const [creating,setCreating]=useState(false);\n'),
('          <label><span>Ordenar por</span><select value={sort} onChange={e=>setSort(e.target.value as any)}><option value="risk">Riesgo</option><option value="end">Fecha fin</option><option value="pending">Pendiente de cobro</option></select></label>\n        </div>','          <label><span>Ordenar por</span><select value={sort} onChange={e=>setSort(e.target.value as any)}><option value="risk">Riesgo</option><option value="end">Fecha fin</option><option value="pending">Pendiente de cobro</option></select></label>\n          <button className="primary-button" onClick={()=>setCreating(true)}>+ Nueva obra</button>\n        </div>'),
('   </div>\n </div>\n}','   </div>\n   {creating&&<NewWorkModal close={()=>setCreating(false)} done={async()=>{setCreating(false);await load()}}/>}\n </div>\n}'),
]:
    if old not in t: raise SystemExit('ERROR: bloque esperado no encontrado en WorksBoard.tsx')
    t=t.replace(old,new,1)
p.write_text(t,encoding='utf-8')

p=ROOT/'front/src/components/ServicesBoard.tsx'
t=p.read_text(encoding='utf-8')
if "import { ErrorBox, Loading, Status } from './ui';\nimport { NewServiceModal } from './NewJobModals';\n" not in t:
    if "import { ErrorBox, Loading, Status } from './ui';\n" not in t: raise SystemExit('ERROR: import ui no encontrado en ServicesBoard.tsx')
    t=t.replace("import { ErrorBox, Loading, Status } from './ui';\n","import { ErrorBox, Loading, Status } from './ui';\nimport { NewServiceModal } from './NewJobModals';\n",1)
if ' const [savingEdit,setSavingEdit]=useState(false);\n const [creating,setCreating]=useState(false);\n' not in t:
    if ' const [savingEdit,setSavingEdit]=useState(false);\n' not in t: raise SystemExit('ERROR: estado savingEdit no encontrado')
    t=t.replace(' const [savingEdit,setSavingEdit]=useState(false);\n',' const [savingEdit,setSavingEdit]=useState(false);\n const [creating,setCreating]=useState(false);\n',1)
if '          <button className="primary-button" onClick={()=>setCreating(true)}>+ Nuevo servicio</button>\n        </div>' not in t:
    if '          {onNew&&<button className="primary-button" onClick={onNew}>+ Nuevo servicio</button>}\n        </div>' not in t: raise SystemExit('ERROR: toolbar servicios no encontrado')
    t=t.replace('          {onNew&&<button className="primary-button" onClick={onNew}>+ Nuevo servicio</button>}\n        </div>','          <button className="primary-button" onClick={()=>setCreating(true)}>+ Nuevo servicio</button>\n        </div>',1)
if '   {creating&&<NewServiceModal close={()=>setCreating(false)} done={async()=>{setCreating(false);await load()}}/>}\n\n   {editing&&<div className="modal-backdrop" ' not in t:
    if '   {editing&&<div className="modal-backdrop" ' not in t: raise SystemExit('ERROR: modal edición servicios no encontrado')
    t=t.replace('   {editing&&<div className="modal-backdrop" ','   {creating&&<NewServiceModal close={()=>setCreating(false)} done={async()=>{setCreating(false);await load()}}/>}\n\n   {editing&&<div className="modal-backdrop" ',1)
p.write_text(t,encoding='utf-8')

print('OK: alta de obra y servicio restaurada.')
