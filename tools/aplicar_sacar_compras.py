from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Sidebar
p = ROOT / "front/src/components/Sidebar.tsx"
t = p.read_text(encoding="utf-8")
line = " {id:'purchases',label:'Compras',icon:'▤'},\n"
if line not in t:
    raise SystemExit("ERROR: no encontré Compras en Sidebar.tsx")
t = t.replace(line, "", 1)
p.write_text(t, encoding="utf-8")

# page.tsx
p = ROOT / "front/app/page.tsx"
t = p.read_text(encoding="utf-8")

t = t.replace(
    "import { Accounts, Clients, Finance, Purchases, Reports, Services, Stock, Suppliers, Works } from '@/src/components/Modules';",
    "import { Accounts, Clients, Finance, Reports, Services, Stock, Suppliers, Works } from '@/src/components/Modules';"
)

t = t.replace(
    "export type Section='dashboard'|'accounts'|'jobs'|'planning'|'services'|'works'|'clients'|'suppliers'|'stock'|'purchases'|'finance'|'reports';",
    "export type Section='dashboard'|'accounts'|'jobs'|'planning'|'services'|'works'|'clients'|'suppliers'|'stock'|'finance'|'reports';"
)

t = t.replace("{section==='purchases'&&<Purchases/>}", "")
t = t.replace("stock:'Stock de materiales',purchases:'Compras',finance:", "stock:'Stock de materiales',finance:")

p.write_text(t, encoding="utf-8")

print("OK: Compras eliminado del sidebar y navegación principal.")
