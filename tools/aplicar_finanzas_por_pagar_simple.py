from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TARGET=Path.cwd()

# New component
src=ROOT/"front/src/components/FinancePayables.tsx"
dst=TARGET/"front/src/components/FinancePayables.tsx"
dst.parent.mkdir(parents=True,exist_ok=True)
dst.write_text(src.read_text(encoding="utf-8"),encoding="utf-8")

# Modules.tsx
p=TARGET/"front/src/components/Modules.tsx"
t=p.read_text(encoding="utf-8")

if "import { FinancePayables } from './FinancePayables';" not in t:
    anchor="import { SupplierAnalytics } from './SupplierAnalytics';\n"
    if anchor in t:
        t=t.replace(anchor,anchor+"import { FinancePayables } from './FinancePayables';\n",1)
    else:
        anchor="import { ClientAnalytics } from './ClientAnalytics';\n"
        if anchor in t:
            t=t.replace(anchor,anchor+"import { FinancePayables } from './FinancePayables';\n",1)
        else:
            raise SystemExit("ERROR: no encontré dónde insertar import FinancePayables")

old=">{tab==='summary'?<FinanceSummary/>:tab==='debts'?<DebtManager/>:tab==='salaries'?<SalaryManager/>:<ResourceManager hideTitle spec={specs[tab]}/>}</div>}"
new=">{tab==='summary'?<FinanceSummary/>:tab==='payables'?<FinancePayables/>:tab==='debts'?<DebtManager/>:tab==='salaries'?<SalaryManager/>:<ResourceManager hideTitle spec={specs[tab]}/>}</div>}"

if old not in t:
    raise SystemExit("ERROR: no encontré la lógica actual de Finance en Modules.tsx")

t=t.replace(old,new,1)
p.write_text(t,encoding="utf-8")

# CSS
p=TARGET/"front/app/globals.css"
t=p.read_text(encoding="utf-8")
marker="/* ===== FINANZAS POR PAGAR SIMPLE ===== */"
if marker in t:
    t=t[:t.index(marker)].rstrip()
block=(ROOT/"FINANCE_PAYABLES_CSS.txt").read_text(encoding="utf-8")
p.write_text(t+"\n\n"+block+"\n",encoding="utf-8")

print("OK: Finanzas > Por pagar ahora usa alta simple tipo costo de obra.")
