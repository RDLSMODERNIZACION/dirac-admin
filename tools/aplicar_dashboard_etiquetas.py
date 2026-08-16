from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
p = ROOT / "front/src/components/Dashboard.tsx"
t = p.read_text(encoding="utf-8")

repls = {
    '<span>Cobros previstos · {currentMonth}</span>': '<span>Cobros previstos</span>',
    '<span>Pagos operativos · {currentMonth}</span>': '<span>Pagos operativos</span>',
    '<span>Costos fijos · {currentMonth}</span>': '<span>Costos fijos</span>',
    '<span>Deudas · {currentMonth}</span>': '<span>Deudas</span>',
    '<span>Sueldos · {currentMonth}</span>': '<span>Sueldos</span>',
}

changed = False
for old, new in repls.items():
    if old in t:
        t = t.replace(old, new)
        changed = True

if not changed:
    raise SystemExit("ERROR: no encontré las etiquetas mensuales esperadas en Dashboard.tsx")

p.write_text(t, encoding="utf-8")
print("OK: etiquetas del flujo mensual simplificadas.")
