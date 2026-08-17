from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

# main.py
p=ROOT/"backend/app/main.py"
t=p.read_text(encoding="utf-8")
if "from .routers.planning import router as planning_router" not in t:
    t=t.replace("from .routers.financial_movements import router as financial_movements_router\n",
                "from .routers.financial_movements import router as financial_movements_router\nfrom .routers.planning import router as planning_router\n")
if "app.include_router(planning_router)" not in t:
    t=t.replace("app.include_router(financial_movements_router)\n",
                "app.include_router(financial_movements_router)\napp.include_router(planning_router)\n")
p.write_text(t,encoding="utf-8")

# Sidebar
p=ROOT/"front/src/components/Sidebar.tsx"
t=p.read_text(encoding="utf-8")
if "{id:'planning'" not in t:
    t=t.replace(" {id:'jobs',label:'Trabajos',icon:'▣'},\n",
                " {id:'jobs',label:'Trabajos',icon:'▣'},\n {id:'planning',label:'Planificación',icon:'◷'},\n")
p.write_text(t,encoding="utf-8")

# page.tsx
p=ROOT/"front/app/page.tsx"
t=p.read_text(encoding="utf-8")
if "import { Planning }" not in t:
    t=t.replace("import { Jobs } from '@/src/components/Jobs';\n",
                "import { Jobs } from '@/src/components/Jobs';\nimport { Planning } from '@/src/components/Planning';\n")
t=t.replace(
    "export type Section='dashboard'|'accounts'|'jobs'|'services'|'works'|'clients'|'suppliers'|'stock'|'purchases'|'finance'|'reports';",
    "export type Section='dashboard'|'accounts'|'jobs'|'planning'|'services'|'works'|'clients'|'suppliers'|'stock'|'purchases'|'finance'|'reports';"
)
if "{section==='planning'&&<Planning/>}" not in t:
    t=t.replace("{section==='jobs'&&<Jobs/>}", "{section==='jobs'&&<Jobs/>}{section==='planning'&&<Planning/>}")
t=t.replace("jobs:'Trabajos',services:", "jobs:'Trabajos',planning:'Planificación',services:")
p.write_text(t,encoding="utf-8")

# WorkDetail
p=ROOT/"front/src/components/WorkDetail.tsx"
t=p.read_text(encoding="utf-8")
if "import { WorkPlanning } from './WorkPlanning';" not in t:
    t=t.replace("import { Card, Empty, ErrorBox, Kpi, Loading, SectionTitle, Status } from './ui';\n",
                "import { Card, Empty, ErrorBox, Kpi, Loading, SectionTitle, Status } from './ui';\nimport { WorkPlanning } from './WorkPlanning';\n")
t=t.replace(
    "type Tab='summary'|'items'|'invoices'|'collections'|'costs'|'suppliers'|'documents';",
    "type Tab='summary'|'items'|'planning'|'invoices'|'collections'|'costs'|'suppliers'|'documents';"
)
t=t.replace(
    "['summary','Resumen'],['items','Ítems'],['invoices','Facturación']",
    "['summary','Resumen'],['items','Ítems'],['planning','Cronograma'],['invoices','Facturación']"
)
if "{tab==='planning'&&<WorkPlanning workId={workId}/>} " not in t:
    t=t.replace(
        "{tab==='items'&&<Items workId={workId} rows={d.items} reload={load}/>} ",
        "{tab==='items'&&<Items workId={workId} rows={d.items} reload={load}/>} {tab==='planning'&&<WorkPlanning workId={workId}/>} "
    )
p.write_text(t,encoding="utf-8")

# CSS
p=ROOT/"front/app/globals.css"
t=p.read_text(encoding="utf-8")
css=(ROOT/"PLANNING_CSS.txt").read_text(encoding="utf-8")
if "/* ===== PLANIFICACION ===== */" not in t:
    t=t.rstrip()+"\n\n"+css+"\n"
p.write_text(t,encoding="utf-8")

print("OK: módulo Planificación aplicado.")
