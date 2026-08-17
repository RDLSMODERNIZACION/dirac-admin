from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
TARGET=Path.cwd()

for rel in ["backend/app/routers/finance_payables.py","front/src/components/FinancePayables.tsx"]:
    src=ROOT/rel;dst=TARGET/rel
    dst.parent.mkdir(parents=True,exist_ok=True)
    dst.write_text(src.read_text(encoding="utf-8"),encoding="utf-8")

# main.py
p=TARGET/"backend/app/main.py"
t=p.read_text(encoding="utf-8")
imp="from .routers.finance_payables import router as finance_payables_router\n"
if imp not in t:
    anchor="from .routers.financial_movements import router as financial_movements_router\n"
    if anchor not in t: raise SystemExit("ERROR: no encontré import financial_movements en main.py")
    t=t.replace(anchor,anchor+imp,1)
if "app.include_router(finance_payables_router)" not in t:
    anchor="app.include_router(financial_movements_router)\n"
    t=t.replace(anchor,anchor+"app.include_router(finance_payables_router)\n",1)
p.write_text(t,encoding="utf-8")

print("OK: Por pagar con Obra/Ítem, Pago desde Cuenta y Comprobante.")
