from pathlib import Path

p = Path.cwd() / "backend/app/routers/works_board.py"
t = p.read_text(encoding="utf-8")

# Evita que psycopg.sql.SQL.format interprete {} de JSON como placeholders.
t = t.replace("COALESCE(admin.checklist,'{}'::jsonb) AS checklist",
              "COALESCE(admin.checklist,jsonb_build_object()) AS checklist")

t = t.replace("""            '{}'::jsonb
          ) AS checklist""",
              """            jsonb_build_object()
          ) AS checklist""")

# Con los {} JSON eliminados, la consulta tiene 11 identificadores de esquema.
old = '""").format(S,S,S,S,S,S,S,S,S,S,S,S))'
new = '""").format(S,S,S,S,S,S,S,S,S,S,S))'
if old in t:
    t = t.replace(old, new, 1)
elif new not in t:
    raise SystemExit("ERROR: no encontré el .format esperado en works_board.py")

p.write_text(t, encoding="utf-8")
print("OK: works_board.py corregido.")
