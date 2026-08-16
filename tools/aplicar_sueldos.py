from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

p=ROOT/'backend/app/main.py'; t=p.read_text(encoding='utf-8')
if 'from .routers.salaries import router as salaries_router\n' not in t:
    t=t.replace('from .routers.debts import router as debts_router\n','from .routers.debts import router as debts_router\nfrom .routers.salaries import router as salaries_router\n')
if 'app.include_router(salaries_router)\n' not in t:
    t=t.replace('app.include_router(debts_router)\n','app.include_router(debts_router)\napp.include_router(salaries_router)\n')
p.write_text(t,encoding='utf-8')

p=ROOT/'front/src/components/Modules.tsx'; t=p.read_text(encoding='utf-8')
old="export function Finance(){const [tab,setTab]=useState<'summary'|'receivables'|'payables'|'debts'|'financial_movements'|'fixed_costs'>('summary');return <div className=\"page-stack\"><SectionTitle title=\"Finanzas\" subtitle=\"Caja, cobros, pagos, deudas, vencimientos y costos fijos.\"/><Tabs tabs={[[\'summary\',\'Resumen\'],[\'receivables\',\'Por cobrar\'],[\'payables\',\'Por pagar\'],[\'debts\',\'Deudas\'],[\'financial_movements\',\'Caja\'],[\'fixed_costs\',\'Costos fijos\']]} value={tab} set={setTab}/>{tab===\'summary\'?<FinanceSummary/>:tab===\'debts\'?<DebtManager/>:<ResourceManager hideTitle spec={specs[tab]}/>}</div>}"
new="export function Finance(){const [tab,setTab]=useState<'summary'|'receivables'|'payables'|'debts'|'salaries'|'financial_movements'|'fixed_costs'>('summary');return <div className=\"page-stack\"><SectionTitle title=\"Finanzas\" subtitle=\"Caja, cobros, pagos, deudas, sueldos, vencimientos y costos fijos.\"/><Tabs tabs={[[\'summary\',\'Resumen\'],[\'receivables\',\'Por cobrar\'],[\'payables\',\'Por pagar\'],[\'debts\',\'Deudas\'],[\'salaries\',\'Sueldos\'],[\'financial_movements\',\'Caja\'],[\'fixed_costs\',\'Costos fijos\']]} value={tab} set={setTab}/>{tab===\'summary\'?<FinanceSummary/>:tab===\'debts\'?<DebtManager/>:tab===\'salaries\'?<SalaryManager/>:<ResourceManager hideTitle spec={specs[tab]}/>}</div>}"
if "tab==='salaries'?<SalaryManager/>" not in t:
    if old not in t: raise SystemExit('ERROR: Finance() actual no coincide')
    t=t.replace(old,new)
if 'function SalaryManager()' not in t:
    i=t.find('\nfunction DebtManager()')
    if i<0: raise SystemExit('ERROR: no encontré DebtManager')
    comp=(ROOT/'tools/SalaryManager.snippet.txt').read_text(encoding='utf-8')
    t=t[:i]+'\n'+comp+t[i:]
p.write_text(t,encoding='utf-8')

# Dashboard: usa períodos salariales existentes; el endpoint /periods los genera al abrir Sueldos.
p=ROOT/'backend/app/routers/dashboard.py'; t=p.read_text(encoding='utf-8')
t=t.replace('today + timedelta(days=i): {"in": Decimal("0"), "out": Decimal("0"), "fixed": Decimal("0"), "debt": Decimal("0")}', 'today + timedelta(days=i): {"in": Decimal("0"), "out": Decimal("0"), "fixed": Decimal("0"), "debt": Decimal("0"), "salary": Decimal("0")}')
# corregir clasificación de deudas si quedó invertida
bad='''        if d <= end:\n            daily[d]["out"] += amount\n            daily[d]["debt"] += amount\n    for inst in debt_installments:'''
if bad in t: t=t.replace(bad,'''        if d <= end:\n            daily[d]["out"] += amount\n    for inst in debt_installments:''')
old='''    for inst in debt_installments:\n        amount = Decimal(str(inst.get("remaining") or 0))\n        if amount <= 0: continue\n        d = max(today, inst.get("due_date") or today)\n        if d <= end: daily[d]["out"] += amount\n\n    for cost in costs:'''
new='''    for inst in debt_installments:\n        amount = Decimal(str(inst.get("remaining") or 0))\n        if amount <= 0: continue\n        d = max(today, inst.get("due_date") or today)\n        if d <= end:\n            daily[d]["out"] += amount\n            daily[d]["debt"] += amount\n\n    with db_cursor() as cur:\n        cur.execute(sql.SQL("""\n          SELECT sp.due_date,GREATEST(0,(sp.base_amount+sp.adjustments)-COALESCE(p.paid,0)) remaining\n          FROM {}.salary_periods sp\n          LEFT JOIN LATERAL (SELECT COALESCE(SUM(amount),0) paid FROM {}.salary_payments sap WHERE sap.salary_period_id=sp.id) p ON true\n          WHERE sp.due_date<=%s AND GREATEST(0,(sp.base_amount+sp.adjustments)-COALESCE(p.paid,0))>0\n        """).format(S,S), [end])\n        salary_due=cur.fetchall()\n    for sal in salary_due:\n        amount=Decimal(str(sal.get("remaining") or 0)); d=max(today,sal.get("due_date") or today)\n        if amount>0 and d<=end:\n            daily[d]["out"]+=amount; daily[d]["salary"]+=amount\n\n    for cost in costs:'''
if old not in t: raise SystemExit('ERROR: no encontré loop de deudas en dashboard')
t=t.replace(old,new)
t=t.replace('''            "debt_out": values["debt"],\n            "projected_cash": running,''','''            "debt_out": values["debt"],\n            "salary_out": values["salary"],\n            "projected_cash": running,''')
t=t.replace('''            "debt_out": Decimal("0"),\n            "closing_cash": None,''','''            "debt_out": Decimal("0"),\n            "salary_out": Decimal("0"),\n            "closing_cash": None,''')
t=t.replace('''        buckets[ms]["debt_out"] += Decimal(str(row.get("debt_out") or 0))\n        buckets[ms]["closing_cash"]''','''        buckets[ms]["debt_out"] += Decimal(str(row.get("debt_out") or 0))\n        buckets[ms]["salary_out"] += Decimal(str(row.get("salary_out") or 0))\n        buckets[ms]["closing_cash"]''')
t=t.replace('''        debt = b["debt_out"]\n        other_out = b["expected_out"] - fixed - debt''','''        debt = b["debt_out"]\n        salary = b["salary_out"]\n        other_out = b["expected_out"] - fixed - debt - salary''')
t=t.replace('''            "debt_out": debt,\n            "expected_out": b["expected_out"],''','''            "debt_out": debt,\n            "salary_out": salary,\n            "expected_out": b["expected_out"],''')
# breakdown
mb=t.find('@router.get("/monthly-breakdown")')
if mb>=0 and 'salary_breakdown=cur.fetchall()' not in t[mb:]:
    a='''        paid_fixed = {(str(x["fixed_cost_id"]), x["period_start"]) for x in cur.fetchall()}\n'''
    ins='''        paid_fixed = {(str(x["fixed_cost_id"]), x["period_start"]) for x in cur.fetchall()}\n        cur.execute(sql.SQL("""\n          SELECT sp.due_date,e.name employee_name,GREATEST(0,(sp.base_amount+sp.adjustments)-COALESCE(p.paid,0)) remaining\n          FROM {}.salary_periods sp JOIN {}.salary_employees e ON e.id=sp.employee_id\n          LEFT JOIN LATERAL (SELECT COALESCE(SUM(amount),0) paid FROM {}.salary_payments sap WHERE sap.salary_period_id=sp.id) p ON true\n          WHERE sp.period_month BETWEEN %s AND %s\n        """).format(S,S,S), [first_month,last_month])\n        salary_breakdown=cur.fetchall()\n'''
    j=t.find(a,mb)
    if j>=0: t=t[:j]+ins+t[j+len(a):]
if mb>=0 and '"sueldo")' not in t[mb:]:
    a='''    for cost in costs:\n        start_month = max(first_month, _month_start(cost.get("start_date") or today))'''
    ins='''    for sal in salary_breakdown:\n        amount=Decimal(str(sal.get("remaining") or 0))\n        if amount<=0: continue\n        target=max(today,sal.get("due_date") or today)\n        if target<=last_day: add(_month_start(target),"expense",f"Sueldo · {sal.get('employee_name') or 'Personal'}",amount,"sueldo")\n\n    for cost in costs:\n        start_month = max(first_month, _month_start(cost.get("start_date") or today))'''
    j=t.find(a,mb)
    if j>=0: t=t[:j]+ins+t[j+len(a):]
p.write_text(t,encoding='utf-8')

p=ROOT/'front/src/components/Dashboard.tsx'; t=p.read_text(encoding='utf-8')
t=t.replace("x.source==='deuda'?'Deuda / financiamiento':x.source==='cuenta_por_pagar'?'Cuenta por pagar'", "x.source==='deuda'?'Deuda / financiamiento':x.source==='sueldo'?'Sueldo':x.source==='cuenta_por_pagar'?'Cuenta por pagar'")
t=t.replace('Cobros y pagos previstos, incluyendo costos fijos y cuotas de deudas pendientes.','Cobros y pagos previstos, incluyendo costos fijos, deudas y sueldos pendientes.')
t=t.replace('''        <div className="negative"><span>Deudas · {currentMonth}</span><strong>− {money(current.debt_out)}</strong></div>\n        <div className={Number(current.closing_cash)>=0?'positive':'negative'}>''','''        <div className="negative"><span>Deudas · {currentMonth}</span><strong>− {money(current.debt_out)}</strong></div>\n        <div className="negative"><span>Sueldos · {currentMonth}</span><strong>− {money(current.salary_out)}</strong></div>\n        <div className={Number(current.closing_cash)>=0?'positive':'negative'}>''')
t=t.replace('<th>Costos fijos</th><th>Deudas</th><th>Caja final</th>','<th>Costos fijos</th><th>Deudas</th><th>Sueldos</th><th>Caja final</th>')
t=t.replace('''<td className="amount-out">− {money(m.debt_out)}</td><td className={Number(m.closing_cash)>=0?'closing-positive':'closing-negative'}>''','''<td className="amount-out">− {money(m.debt_out)}</td><td className="amount-out">− {money(m.salary_out)}</td><td className={Number(m.closing_cash)>=0?'closing-positive':'closing-negative'}>''')
p.write_text(t,encoding='utf-8')
print('OK: módulo Sueldos aplicado')
