from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

p = ROOT / "backend/app/routers/dashboard.py"
t = p.read_text(encoding="utf-8")

pairs = [
    ("      WHERE r.status IN ('pendiente','parcial')\n    ),", "      WHERE r.status IN ('pendiente','parcial')\n        AND (\n          r.service_id IS NULL\n          OR EXISTS (SELECT 1 FROM {}.services sv WHERE sv.id=r.service_id)\n        )\n    ),"),
    (').format(S, S, S, S, S, S, S, S, S)', ').format(S, S, S, S, S, S, S, S, S, S)'),
    ('          WHERE r.status IN (\'pendiente\',\'parcial\')\n        """).format(S, S))', '          WHERE r.status IN (\'pendiente\',\'parcial\')\n            AND (\n              r.service_id IS NULL\n              OR EXISTS (SELECT 1 FROM {}.services sv WHERE sv.id=r.service_id)\n            )\n        """).format(S, S, S))'),
]
for old,new in pairs:
    if old not in t:
        raise SystemExit("ERROR: bloque esperado no encontrado en dashboard.py")
    t = t.replace(old,new,1)
p.write_text(t, encoding="utf-8")

p = ROOT / "backend/app/routers/services_board.py"
t = p.read_text(encoding="utf-8")
route = '\n\n@router.post("/cleanup-orphan-receivables")\ndef cleanup_orphan_receivables():\n    """\n    Elimina cuentas por cobrar de servicios que ya no existen,\n    siempre que no tengan cobros registrados.\n    """\n    with db_cursor() as cur:\n        cur.execute(sql.SQL("""\n            SELECT r.id\n            FROM {}.receivables r\n            LEFT JOIN {}.services s ON s.id=r.service_id\n            WHERE r.service_id IS NOT NULL\n              AND s.id IS NULL\n              AND NOT EXISTS (\n                SELECT 1\n                FROM {}.financial_movements fm\n                WHERE fm.receivable_id=r.id\n                  AND fm.type=\'ingreso\'\n              )\n        """).format(S, S, S))\n        ids = [row["id"] for row in cur.fetchall()]\n\n        if ids:\n            cur.execute(\n                sql.SQL("DELETE FROM {}.receivables WHERE id = ANY(%s)").format(S),\n                [ids],\n            )\n\n    return {"ok": True, "deleted": len(ids)}\n'
if '@router.post("/cleanup-orphan-receivables")' not in t:
    t = t.rstrip() + route + "\n"
p.write_text(t, encoding="utf-8")

print("OK: corregidos cobros previstos y agregado cleanup de huérfanos.")
