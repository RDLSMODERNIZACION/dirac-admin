from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
p = ROOT / "front/src/components/ClientAnalytics.tsx"
t = p.read_text(encoding="utf-8")

start_marker = '  <div className="client-kpis">'
end_marker = '  <Card>\n   <div className="client-toolbar">'

start = t.find(start_marker)
end = t.find(end_marker, start)

if start == -1 or end == -1:
    raise SystemExit("ERROR: no encontré el bloque de KPI/gráficos esperado en ClientAnalytics.tsx")

# Conservamos la tabla ejecutiva y todo lo que viene después.
t = t[:start] + end_marker + t[end + len(end_marker):]

p.write_text(t, encoding="utf-8")
print("OK: KPI y gráficos superiores eliminados de Clientes.")
