from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
TARGET=Path.cwd()

for rel in ["backend/app/routers/supplier_insights.py","front/src/components/SupplierAnalytics.tsx"]:
    src=ROOT/rel
    dst=TARGET/rel
    dst.parent.mkdir(parents=True,exist_ok=True)
    dst.write_text(src.read_text(encoding="utf-8"),encoding="utf-8")

# backend/main.py
p=TARGET/"backend/app/main.py"
t=p.read_text(encoding="utf-8")
if "from .routers.supplier_insights import router as supplier_insights_router" not in t:
    anchor="from .routers.client_insights import router as client_insights_router\n"
    if anchor not in t:
        anchor="from .routers.financial_movements import router as financial_movements_router\n"
    t=t.replace(anchor,anchor+"from .routers.supplier_insights import router as supplier_insights_router\n",1)
if "app.include_router(supplier_insights_router)" not in t:
    anchor="app.include_router(client_insights_router)\n"
    if anchor not in t:
        anchor="app.include_router(financial_movements_router)\n"
    t=t.replace(anchor,anchor+"app.include_router(supplier_insights_router)\n",1)
p.write_text(t,encoding="utf-8")

# Modules.tsx
p=TARGET/"front/src/components/Modules.tsx"
t=p.read_text(encoding="utf-8")
if "import { SupplierAnalytics } from './SupplierAnalytics';" not in t:
    anchor="import { ClientAnalytics } from './ClientAnalytics';\n"
    if anchor in t:
        t=t.replace(anchor,anchor+"import { SupplierAnalytics } from './SupplierAnalytics';\n",1)
    else:
        t=t.replace("import { WorkDetail } from './WorkDetail';\n","import { WorkDetail } from './WorkDetail';\nimport { SupplierAnalytics } from './SupplierAnalytics';\n",1)

old="export function Suppliers(){const [tab,setTab]=useState<'suppliers'|'supplier_rates'|'supplier_services'>('suppliers');return <div className=\"page-stack\"><SectionTitle title=\"Proveedores y contratistas\" subtitle=\"Cuenta base, tarifas y horas/servicios acumulados.\"/><Tabs tabs={[['suppliers','Proveedores'],['supplier_rates','Tarifas'],['supplier_services','Horas y servicios']]} value={tab} set={setTab}/><ResourceManager hideTitle spec={specs[tab]}/></div>}"
if old not in t:
    raise SystemExit("ERROR: no encontré el componente Suppliers actual en Modules.tsx")
t=t.replace(old,"export function Suppliers(){return <SupplierAnalytics/>}",1)
p.write_text(t,encoding="utf-8")

# CSS
p=TARGET/"front/app/globals.css"
t=p.read_text(encoding="utf-8")
marker="/* ===== PROVEEDORES EJECUTIVO AGRUPADO ===== */"
if marker in t:
    t=t[:t.index(marker)].rstrip()
block=(ROOT/"SUPPLIERS_EXEC_CSS.txt").read_text(encoding="utf-8")
p.write_text(t+"\n\n"+block+"\n",encoding="utf-8")

print("OK: Proveedores Ejecutivo agrupado aplicado.")
