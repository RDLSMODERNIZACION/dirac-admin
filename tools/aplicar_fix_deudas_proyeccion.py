from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# BACKEND
p = ROOT / "backend/app/routers/dashboard.py"
t = p.read_text(encoding="utf-8")

t = t.replace(
'today + timedelta(days=i): {"in": Decimal("0"), "out": Decimal("0"), "fixed": Decimal("0")}',
'today + timedelta(days=i): {"in": Decimal("0"), "out": Decimal("0"), "fixed": Decimal("0"), "debt": Decimal("0")}'
)

t = t.replace(
'if d <= end: daily[d]["out"] += amount',
'if d <= end:\n            daily[d]["out"] += amount\n            daily[d]["debt"] += amount',
1
)

t = t.replace(
'"fixed_cost_out": values["fixed"],\n            "projected_cash": running,',
'"fixed_cost_out": values["fixed"],\n            "debt_out": values["debt"],\n            "projected_cash": running,'
)

t = t.replace(
'"fixed_cost_out": Decimal("0"),\n            "closing_cash": None,',
'"fixed_cost_out": Decimal("0"),\n            "debt_out": Decimal("0"),\n            "closing_cash": None,'
)

t = t.replace(
'buckets[ms]["fixed_cost_out"] += Decimal(str(row.get("fixed_cost_out") or 0))\n        buckets[ms]["closing_cash"]',
'buckets[ms]["fixed_cost_out"] += Decimal(str(row.get("fixed_cost_out") or 0))\n        buckets[ms]["debt_out"] += Decimal(str(row.get("debt_out") or 0))\n        buckets[ms]["closing_cash"]'
)

t = t.replace(
'fixed = b["fixed_cost_out"]\n        other_out = b["expected_out"] - fixed',
'fixed = b["fixed_cost_out"]\n        debt = b["debt_out"]\n        other_out = b["expected_out"] - fixed - debt'
)

t = t.replace(
'"fixed_cost_out": fixed,\n            "expected_out": b["expected_out"],',
'"fixed_cost_out": fixed,\n            "debt_out": debt,\n            "expected_out": b["expected_out"],'
)

mb = '@router.get("/monthly-breakdown")'
pos = t.find(mb)
if pos == -1:
    raise SystemExit("No encontré monthly-breakdown")

sub = t[pos:]
if 'source": "deuda"' not in sub:
    anchor = '        paid_fixed = {(str(x["fixed_cost_id"]), x["period_start"]) for x in cur.fetchall()}\n\n    for r in receivables:'
    repl = '        paid_fixed = {(str(x["fixed_cost_id"]), x["period_start"]) for x in cur.fetchall()}\n\n        cur.execute(sql.SQL("""\n          SELECT di.due_date,\n                 GREATEST(0,di.amount-di.paid_amount) AS remaining,\n                 d.creditor,\n                 d.description\n          FROM {}.debt_installments di\n          JOIN {}.debts d ON d.id=di.debt_id\n          WHERE d.status=\'activa\'\n            AND di.status IN (\'pendiente\',\'parcial\')\n            AND di.due_date <= %s\n        """).format(S, S), [last_day])\n        debt_breakdown = cur.fetchall()\n\n    for r in receivables:'
    if anchor not in t:
        raise SystemExit("No encontré anchor de breakdown")
    t = t.replace(anchor, repl, 1)

    anchor2 = '    for cost in costs:\n        start_month = max(first_month, _month_start(cost.get("start_date") or today))'
    repl2 = '    for inst in debt_breakdown:\n        amount = Decimal(str(inst.get("remaining") or 0))\n        if amount <= 0:\n            continue\n        target = max(today, inst.get("due_date") or today)\n        if target > last_day:\n            continue\n        label = inst.get("creditor") or "Deuda"\n        if inst.get("description"):\n            label = f"{label} · {inst[\'description\']}"\n        add(_month_start(target), "expense", label, amount, "deuda")\n\n    for cost in costs:\n        start_month = max(first_month, _month_start(cost.get("start_date") or today))'
    if anchor2 not in t:
        raise SystemExit("No encontré anchor2 de breakdown")
    t = t.replace(anchor2, repl2, 1)

p.write_text(t, encoding="utf-8")

# FRONT
p = ROOT / "front/src/components/Dashboard.tsx"
t = p.read_text(encoding="utf-8")

t = t.replace(
"x.source==='costo_fijo'?'Costo fijo':x.source==='cuenta_por_pagar'?'Cuenta por pagar'",
"x.source==='costo_fijo'?'Costo fijo':x.source==='deuda'?'Deuda / financiamiento':x.source==='cuenta_por_pagar'?'Cuenta por pagar'"
)

t = t.replace(
"Cobros y pagos previstos, incluyendo los costos fijos activos todavía no pagados.",
"Cobros y pagos previstos, incluyendo costos fijos y cuotas de deudas pendientes."
)

t = t.replace(
'<div className="negative"><span>Otros pagos · {currentMonth}</span><strong>− {money(current.other_payments)}</strong></div>\n        <div className="negative"><span>Costos fijos · {currentMonth}</span><strong>− {money(current.fixed_cost_out)}</strong></div>',
'<div className="negative"><span>Pagos operativos · {currentMonth}</span><strong>− {money(current.other_payments)}</strong></div>\n        <div className="negative"><span>Costos fijos · {currentMonth}</span><strong>− {money(current.fixed_cost_out)}</strong></div>\n        <div className="negative"><span>Deudas · {currentMonth}</span><strong>− {money(current.debt_out)}</strong></div>'
)

t = t.replace(
"<th>Otros pagos</th><th>Costos fijos</th><th>Caja final</th>",
"<th>Pagos operativos</th><th>Costos fijos</th><th>Deudas</th><th>Caja final</th>"
)

t = t.replace(
'<td className="amount-out">− {money(m.other_payments)}</td><td className="amount-out">− {money(m.fixed_cost_out)}</td><td className={Number(m.closing_cash)>=0?\'closing-positive\':\'closing-negative\'}>',
'<td className="amount-out">− {money(m.other_payments)}</td><td className="amount-out">− {money(m.fixed_cost_out)}</td><td className="amount-out">− {money(m.debt_out)}</td><td className={Number(m.closing_cash)>=0?\'closing-positive\':\'closing-negative\'}>'
)

p.write_text(t, encoding="utf-8")
print("OK: deudas visibles en proyección y desglose.")
