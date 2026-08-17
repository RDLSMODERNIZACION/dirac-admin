from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

p = ROOT / "front/src/components/WorksBoard.tsx"
t = p.read_text(encoding="utf-8")

aside_start = t.find('    <aside className="works-guide-card">')
aside_end = t.find('    </aside>', aside_start)

if aside_start == -1 or aside_end == -1:
    raise SystemExit("ERROR: no encontré el panel 'Cómo leer el cuadro' en WorksBoard.tsx")

aside_end += len('    </aside>\n')
t = t[:aside_start] + t[aside_end:]
p.write_text(t, encoding="utf-8")

p = ROOT / "front/app/globals.css"
css = p.read_text(encoding="utf-8")

css = css.replace(
    ".works-board-layout{display:grid;grid-template-columns:minmax(0,1fr) 230px;gap:18px;align-items:start}",
    ".works-board-layout{display:block;width:100%}"
)

css = css.replace(
    ".works-control-card,.works-guide-card{background:#fff;border:1px solid #e2e8f0;border-radius:18px;box-shadow:0 8px 28px rgba(15,23,42,.035)}",
    ".works-control-card{background:#fff;border:1px solid #e2e8f0;border-radius:18px;box-shadow:0 8px 28px rgba(15,23,42,.035)}"
)

css = css.replace(
    ".works-control-card{padding:20px}",
    ".works-control-card{padding:20px;width:100%;min-width:0}"
)

css = css.replace(
    ".works-board-table{font-size:13px}",
    ".works-board-table{font-size:13px;width:100%;table-layout:auto}"
)

css = css.replace(
    ".works-board-table td:first-child{min-width:230px}.works-board-table td:nth-child(2){min-width:190px}",
    ".works-board-table td:first-child{min-width:200px}.works-board-table td:nth-child(2){min-width:160px}"
)

css += '''
/* Ajuste: cuadro de obras a ancho completo */
.works-guide-card{display:none!important}
.works-board-table-wrap{width:100%;overflow-x:auto}
@media(min-width:1200px){
  .works-board-table-wrap{overflow-x:visible}
  .works-board-table th,
  .works-board-table td{padding-left:12px;padding-right:12px}
}
'''

p.write_text(css, encoding="utf-8")
print("OK: eliminado panel lateral y cuadro de obras ampliado a todo el ancho.")
