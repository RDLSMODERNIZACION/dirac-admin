from pathlib import Path

p=Path.cwd()/'front/src/components/ResourceManager.tsx'
t=p.read_text(encoding='utf-8')

old="api.post<any>(`/api/works/${r.id}/generate-receivables`)"
new="api.post<any>(`/api/works/${r.id}/generate-receivables`,{})"

if old not in t:
    raise SystemExit("ERROR: llamada generate-receivables no encontrada")

t=t.replace(old,new,1)
p.write_text(t,encoding='utf-8')
print("OK: api.post corregido en ResourceManager.")
