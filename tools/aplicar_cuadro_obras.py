from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

# main.py
p=ROOT/"backend/app/main.py"
t=p.read_text(encoding="utf-8")
imp="from .routers.works_board import router as works_board_router\n"
if imp not in t:
    anchor="from .routers.works import router as works_router\n"
    if anchor not in t: raise SystemExit("No encontré works_router en main.py")
    t=t.replace(anchor,anchor+imp)
inc="app.include_router(works_board_router)\n"
if inc not in t:
    anchor="app.include_router(works_router)\n"
    if anchor not in t: raise SystemExit("No encontré include works_router")
    t=t.replace(anchor,anchor+inc)
p.write_text(t,encoding="utf-8")

# Jobs.tsx
p=ROOT/"front/src/components/Jobs.tsx"
t=p.read_text(encoding="utf-8")
if "import { WorksBoard } from './WorksBoard';" not in t:
    t=t.replace("import { WorkDetail } from './WorkDetail';\n","import { WorkDetail } from './WorkDetail';\nimport { WorksBoard } from './WorksBoard';\n")
t=t.replace("{tab==='works'&&<Works embedded/>}","{tab==='works'&&<WorksBoard/>}")
p.write_text(t,encoding="utf-8")

# globals.css
p=ROOT/"front/app/globals.css"
t=p.read_text(encoding="utf-8")
css=(ROOT/"WORKS_BOARD_CSS.txt").read_text(encoding="utf-8")
if "/* ===== CUADRO DE CONTROL DE OBRAS ===== */" not in t:
    t=t.rstrip()+"\n\n"+css+"\n"
p.write_text(t,encoding="utf-8")
print("OK: Cuadro de control de Obras aplicado.")
