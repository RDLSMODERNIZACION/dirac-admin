from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
p = ROOT / 'backend/app/routers/planning.py'
t = p.read_text(encoding='utf-8')

old = '''        q = task_select_sql(where) + sql.SQL("""
            ORDER BY
              CASE WHEN t.status='completada' THEN 1 ELSE 0 END,
              CASE
                WHEN t.status <> 'completada'
                 AND t.end_date IS NOT NULL
                 AND t.end_date < CURRENT_DATE
                THEN 0 ELSE 1
              END,
              t.start_date NULLS LAST,
              t.end_date NULLS LAST,
              t.created_at DESC
        """)
        # task_select_sql has 8 schema identifiers
        cur.execute(q.format(S, S, S, S, S, S, S, S), params)
'''

new = '''        # Formatear primero el SQL base. Al sumarle ORDER BY se convierte en
        # psycopg.sql.Composed, que no admite .format().
        q = task_select_sql(where).format(S, S, S, S, S, S, S, S) + sql.SQL("""
            ORDER BY
              CASE WHEN t.status='completada' THEN 1 ELSE 0 END,
              CASE
                WHEN t.status <> 'completada'
                 AND t.end_date IS NOT NULL
                 AND t.end_date < CURRENT_DATE
                THEN 0 ELSE 1
              END,
              t.start_date NULLS LAST,
              t.end_date NULLS LAST,
              t.created_at DESC
        """)
        cur.execute(q, params)
'''

if old not in t:
    raise SystemExit('ERROR: no encontré el bloque esperado en planning.py. No se modificó ningún archivo.')

t = t.replace(old, new, 1)
p.write_text(t, encoding='utf-8')
print('OK: corregida consulta GET /api/planning/tasks.')