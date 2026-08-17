from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

# backend/app/main.py
p=ROOT/"backend/app/main.py"
t=p.read_text(encoding="utf-8")
imp="from .routers.services_board import router as services_board_router\n"
if imp not in t:
    anchor="from .routers.service_detail import router as service_detail_router\n"
    if anchor not in t: raise SystemExit("ERROR: no encontré service_detail_router")
    t=t.replace(anchor,anchor+imp)

inc="app.include_router(services_board_router)\n"
if inc not in t:
    anchor="app.include_router(service_detail_router)\n"
    if anchor not in t: raise SystemExit("ERROR: no encontré include service_detail_router")
    t=t.replace(anchor,anchor+inc)
p.write_text(t,encoding="utf-8")

# Jobs.tsx: la pestaña Servicios usa ServicesBoard.
p=ROOT/"front/src/components/Jobs.tsx"
t=p.read_text(encoding="utf-8")
if "import { ServicesBoard } from './ServicesBoard';" not in t:
    t=t.replace("import { ServiceDetail } from './ServiceDetail';\n","import { ServiceDetail } from './ServiceDetail';\nimport { ServicesBoard } from './ServicesBoard';\n")

# Mantener ServiceManager para crear/editar: oculto como fallback no hace falta.
t=t.replace("{tab==='services'&&<ServiceManager embedded/>}","{tab==='services'&&<ServicesBoard/>}")
p.write_text(t,encoding="utf-8")

# globals.css
p=ROOT/"front/app/globals.css"
t=p.read_text(encoding="utf-8")
css=(ROOT/"SERVICES_BOARD_CSS.txt").read_text(encoding="utf-8")
if "/* ===== CUADRO DE CONTROL DE SERVICIOS ===== */" not in t:
    t=t.rstrip()+"\n\n"+css+"\n"
p.write_text(t,encoding="utf-8")

print("OK: cuadro ejecutivo de Servicios aplicado.")
