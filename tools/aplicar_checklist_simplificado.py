from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
p = ROOT / "front/src/components/WorkDetail.tsx"
t = p.read_text(encoding="utf-8")

old = ''' const defs=[
  ['presupuesto','Presupuesto presentado'],
  ['nota','Nota presentada'],
  ['memoria_descriptiva','Memoria descriptiva'],
  ['contrato','Contrato'],
  ['certificacion','Certificación'],
  ['factura','Factura'],
  ['cobro','Cobro'],
 ] as [string,string][];'''

new = ''' const defs=[
  ['presupuesto','Presupuesto presentado'],
  ['contrato','Contrato'],
  ['certificacion','Certificación'],
  ['factura','Factura'],
  ['cobro','Cobro'],
 ] as [string,string][];'''

if old not in t:
    raise SystemExit("ERROR: no encontré la definición del checklist en WorkDetail.tsx")

t = t.replace(old, new, 1)
p.write_text(t, encoding="utf-8")

print("OK: Nota y Memoria descriptiva removidas del checklist visual.")
