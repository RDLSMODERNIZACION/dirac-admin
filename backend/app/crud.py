from typing import Any
from psycopg import sql
from fastapi import HTTPException

from .core.config import get_settings
from .core.db import db_cursor
from .metadata import TABLES

settings = get_settings()


def table_meta(table: str) -> dict:
    meta = TABLES.get(table)
    if not meta:
        raise HTTPException(status_code=404, detail="Unknown table")
    return meta


def _table_identifier(table: str):
    return sql.Identifier(settings.db_schema, table)


def _sanitize_payload(table: str, payload: dict[str, Any]) -> dict[str, Any]:
    allowed = set(table_meta(table)["writable"])
    cleaned = {k: v for k, v in payload.items() if k in allowed}
    if not cleaned:
        raise HTTPException(status_code=400, detail="No writable fields supplied")
    return cleaned


def list_rows(table: str, limit: int = 50, offset: int = 0, q: str | None = None, filters: dict[str, Any] | None = None):
    meta = table_meta(table)
    where_parts = []
    params: list[Any] = []

    filters = filters or {}
    for key, value in filters.items():
        if value is None or key not in meta["writable"]:
            continue
        where_parts.append(sql.SQL("{} = %s").format(sql.Identifier(key)))
        params.append(value)

    if q and meta.get("search"):
        search_parts = []
        for col in meta["search"]:
            search_parts.append(sql.SQL("CAST({} AS TEXT) ILIKE %s").format(sql.Identifier(col)))
            params.append(f"%{q}%")
        where_parts.append(sql.SQL("(") + sql.SQL(" OR ").join(search_parts) + sql.SQL(")"))

    query = sql.SQL("SELECT * FROM {} ").format(_table_identifier(table))
    if where_parts:
        query += sql.SQL("WHERE ") + sql.SQL(" AND ").join(where_parts) + sql.SQL(" ")
    query += sql.SQL("ORDER BY created_at DESC NULLS LAST LIMIT %s OFFSET %s")
    params.extend([limit, offset])

    with db_cursor() as cur:
        cur.execute(query, params)
        return cur.fetchall()


def get_row(table: str, row_id: str):
    table_meta(table)
    query = sql.SQL("SELECT * FROM {} WHERE id = %s").format(_table_identifier(table))
    with db_cursor() as cur:
        cur.execute(query, [row_id])
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Record not found")
    return row


def create_row(table: str, payload: dict[str, Any]):
    data = _sanitize_payload(table, payload)
    columns = [sql.Identifier(k) for k in data.keys()]
    placeholders = [sql.Placeholder() for _ in data]
    query = sql.SQL("INSERT INTO {} ({}) VALUES ({}) RETURNING *").format(
        _table_identifier(table),
        sql.SQL(", ").join(columns),
        sql.SQL(", ").join(placeholders),
    )
    with db_cursor() as cur:
        cur.execute(query, list(data.values()))
        return cur.fetchone()


def update_row(table: str, row_id: str, payload: dict[str, Any]):
    data = _sanitize_payload(table, payload)
    assignments = [sql.SQL("{} = %s").format(sql.Identifier(k)) for k in data]
    query = sql.SQL("UPDATE {} SET {} WHERE id = %s RETURNING *").format(
        _table_identifier(table), sql.SQL(", ").join(assignments)
    )
    params = list(data.values()) + [row_id]
    with db_cursor() as cur:
        cur.execute(query, params)
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Record not found")
    return row


def delete_row(table: str, row_id: str):
    table_meta(table)
    query = sql.SQL("DELETE FROM {} WHERE id = %s RETURNING id").format(_table_identifier(table))
    with db_cursor() as cur:
        cur.execute(query, [row_id])
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Record not found")
    return {"deleted": True, "id": str(row["id"])}
