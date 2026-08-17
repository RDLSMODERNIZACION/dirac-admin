from pathlib import Path

p = Path.cwd() / 'front/src/components/Jobs.tsx'
t = p.read_text(encoding='utf-8')
old = "      <button className={tab==='admin'?'active':''} onClick={()=>setTab('admin')}>Administración</button>"
new = "      <button className={tab==='admin'?'active':''} onClick={()=>{setTab('admin');void load()}}>Administración</button>"
if old not in t:
    raise SystemExit('ERROR: botón Administración no encontrado')
t = t.replace(old, new, 1)
p.write_text(t, encoding='utf-8')
print('OK: Administración ahora refresca los datos al entrar.')