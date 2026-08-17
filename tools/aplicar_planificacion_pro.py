from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[1]
TARGET=Path.cwd()

# Reemplazar backend y frontend por versiones completas.
for rel in [
    "backend/app/routers/planning.py",
    "front/src/components/Planning.tsx",
]:
    src=ROOT/rel
    dst=TARGET/rel
    dst.parent.mkdir(parents=True,exist_ok=True)
    dst.write_text(src.read_text(encoding="utf-8"),encoding="utf-8")

# Agregar CSS, eliminando bloque previo de esta versión si ya existía.
css_path=TARGET/"front/app/globals.css"
if not css_path.exists():
    raise SystemExit("ERROR: no encontré front/app/globals.css")
current=css_path.read_text(encoding="utf-8")
marker="/* ===== PLANIFICACION PRO DEPENDENCIAS ===== */"
if marker in current:
    current=current[:current.index(marker)].rstrip()
block=(ROOT/"PLANNING_PRO_CSS.txt").read_text(encoding="utf-8")
css_path.write_text(current+"\n\n"+block+"\n",encoding="utf-8")

print("OK: Planificación Pro con dependencias aplicada.")
