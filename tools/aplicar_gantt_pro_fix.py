from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = Path.cwd()

payload_planning = ROOT / "payload" / "Planning.tsx"
payload_css = ROOT / "payload" / "PLANNING_GANTT_PRO_CSS.txt"

planning_dst = TARGET / "front" / "src" / "components" / "Planning.tsx"
css_dst = TARGET / "front" / "app" / "globals.css"

if not payload_planning.exists():
    raise SystemExit("ERROR: falta payload/Planning.tsx")
if not css_dst.exists():
    raise SystemExit("ERROR: no encontré front/app/globals.css. Ejecutá esto desde la raíz de dirac-admin.")

# Escritura directa: evita shutil.copy2 y el bloqueo de Windows/OneDrive.
planning_dst.parent.mkdir(parents=True, exist_ok=True)
planning_dst.write_text(payload_planning.read_text(encoding="utf-8"), encoding="utf-8")

css = css_dst.read_text(encoding="utf-8")
block = payload_css.read_text(encoding="utf-8")
marker = "/* ===== PLANNING GANTT PRO ===== */"

if marker in css:
    css = css[:css.index(marker)].rstrip()

css_dst.write_text(css + "\n\n" + block + "\n", encoding="utf-8")

print("OK: Planning.tsx restaurado con Gantt Pro y CSS actualizado.")
