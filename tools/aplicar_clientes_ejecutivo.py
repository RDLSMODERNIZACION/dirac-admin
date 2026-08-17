from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
TARGET=Path.cwd()

# Copy new files
for rel in ["backend/app/routers/client_insights.py","front/src/components/ClientAnalytics.tsx"]:
    src=ROOT/rel;dst=TARGET/rel
    dst.parent.mkdir(parents=True,exist_ok=True)
    dst.write_text(src.read_text(encoding="utf-8"),encoding="utf-8")

# backend main.py
p=TARGET/"backend/app/main.py"
t=p.read_text(encoding="utf-8")
if "from .routers.client_insights import router as client_insights_router" not in t:
    t=t.replace("from .routers.financial_movements import router as financial_movements_router\n",
                "from .routers.financial_movements import router as financial_movements_router\nfrom .routers.client_insights import router as client_insights_router\n")
if "app.include_router(client_insights_router)" not in t:
    t=t.replace("app.include_router(financial_movements_router)\n",
                "app.include_router(financial_movements_router)\napp.include_router(client_insights_router)\n")
p.write_text(t,encoding="utf-8")

# Modules.tsx
p=TARGET/"front/src/components/Modules.tsx"
t=p.read_text(encoding="utf-8")
if "import { ClientAnalytics } from './ClientAnalytics';" not in t:
    t=t.replace("import { WorkDetail } from './WorkDetail';\n",
                "import { WorkDetail } from './WorkDetail';\nimport { ClientAnalytics } from './ClientAnalytics';\n")
old='export const Clients=()=> <ResourceManager spec={specs.clients} subtitle="Cartera de clientes y datos de contacto."/>;'
if old in t:
    t=t.replace(old,"export const Clients=()=> <ClientAnalytics/>;",1)
elif "export const Clients=()=> <ClientAnalytics/>;" not in t:
    raise SystemExit("ERROR: no encontré el componente Clients esperado en Modules.tsx")
p.write_text(t,encoding="utf-8")

# CSS
p=TARGET/"front/app/globals.css"
t=p.read_text(encoding="utf-8")
marker="/* ===== CLIENTES EJECUTIVO ===== */"
if marker in t:t=t[:t.index(marker)].rstrip()
block=(ROOT/"CLIENTS_EXEC_CSS.txt").read_text(encoding="utf-8")
p.write_text(t+"\n\n"+block+"\n",encoding="utf-8")

print("OK: Clientes convertido en panel ejecutivo.")
