from pathlib import Path

p = Path.cwd() / "front/src/components/Planning.tsx"
t = p.read_text(encoding="utf-8")

old = "onEdit={r=>{setEdit(r);setOpen(true)}}"
new = "onEdit={(r:any)=>{setEdit(r);setOpen(true)}}"

if old not in t:
    raise SystemExit("ERROR: no encontré el callback onEdit esperado")

t = t.replace(old, new, 1)
p.write_text(t, encoding="utf-8")
print("OK: tipo explícito agregado al callback onEdit de Planning.")
