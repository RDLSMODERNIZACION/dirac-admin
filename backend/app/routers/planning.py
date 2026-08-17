from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from psycopg import sql

from ..core.config import get_settings
from ..core.db import db_cursor
from ..core.security import require_api_key

router = APIRouter(prefix="/api/planning", tags=["planning"], dependencies=[Depends(require_api_key)])
settings = get_settings()
S = sql.Identifier(settings.db_schema)


def ensure_table(cur):
    cur.execute(sql.SQL("""
        CREATE TABLE IF NOT EXISTS {}.planning_tasks (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            work_id uuid NOT NULL REFERENCES {}.works(id) ON DELETE CASCADE,
            work_item_id uuid NULL REFERENCES {}.work_items(id) ON DELETE SET NULL,
            title text NOT NULL,
            description text NULL,
            responsible text NULL,
            start_date date NULL,
            end_date date NULL,
            status text NOT NULL DEFAULT 'pendiente',
            priority text NOT NULL DEFAULT 'media',
            progress_percent numeric(5,2) NOT NULL DEFAULT 0,
            notes text NULL,
            created_at timestamptz NOT NULL DEFAULT now(),
            updated_at timestamptz NOT NULL DEFAULT now()
        )
    """).format(S, S, S))
    cur.execute(sql.SQL("""
        CREATE INDEX IF NOT EXISTS planning_tasks_work_id_idx
        ON {}.planning_tasks(work_id)
    """).format(S))
    cur.execute(sql.SQL("""
        CREATE INDEX IF NOT EXISTS planning_tasks_end_date_idx
        ON {}.planning_tasks(end_date)
    """).format(S))


class TaskPayload(BaseModel):
    work_id: UUID
    work_item_id: UUID | None = None
    title: str
    description: str | None = None
    responsible: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    status: str = "pendiente"
    priority: str = "media"
    progress_percent: float = 0
    notes: str | None = None


def normalized_progress(status: str, progress: float):
    if status == "completada":
        return 100
    if status == "pendiente":
        return max(0, min(100, progress or 0))
    return max(0, min(100, progress or 0))


@router.get("/tasks")
def list_tasks(work_id: UUID | None = None):
    with db_cursor() as cur:
        ensure_table(cur)
        where = "WHERE t.work_id=%s" if work_id else ""
        params = [work_id] if work_id else []
        cur.execute(sql.SQL(f"""
            SELECT
                t.*,
                w.name AS work_name,
                c.name AS client_name,
                wi.code AS item_code,
                wi.description AS item_description,
                CASE
                    WHEN t.status <> 'completada'
                     AND t.end_date IS NOT NULL
                     AND t.end_date < CURRENT_DATE
                    THEN true ELSE false
                END AS is_overdue
            FROM {{}}.planning_tasks t
            JOIN {{}}.works w ON w.id=t.work_id
            LEFT JOIN {{}}.clients c ON c.id=w.client_id
            LEFT JOIN {{}}.work_items wi ON wi.id=t.work_item_id
            {where}
            ORDER BY
              CASE WHEN t.status='completada' THEN 1 ELSE 0 END,
              CASE
                WHEN t.status <> 'completada'
                 AND t.end_date IS NOT NULL
                 AND t.end_date < CURRENT_DATE
                THEN 0 ELSE 1
              END,
              t.end_date NULLS LAST,
              t.created_at DESC
        """).format(S, S, S, S), params)
        return cur.fetchall()


@router.get("/summary")
def summary():
    with db_cursor() as cur:
        ensure_table(cur)
        cur.execute(sql.SQL("""
            SELECT
              COUNT(*) FILTER (WHERE status <> 'completada') AS pending,
              COUNT(*) FILTER (WHERE status='en_ejecucion') AS in_progress,
              COUNT(*) FILTER (
                WHERE status <> 'completada'
                  AND end_date IS NOT NULL
                  AND end_date < CURRENT_DATE
              ) AS overdue,
              COUNT(*) FILTER (
                WHERE status <> 'completada'
                  AND end_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '7 days'
              ) AS next_7_days,
              COUNT(*) FILTER (WHERE status='completada') AS completed
            FROM {}.planning_tasks
        """).format(S))
        return cur.fetchone()


@router.post("/tasks")
def create_task(body: TaskPayload):
    if not body.title.strip():
        raise HTTPException(400, "La tarea necesita un título")
    if body.start_date and body.end_date and body.end_date < body.start_date:
        raise HTTPException(400, "La fecha fin no puede ser anterior al inicio")

    with db_cursor() as cur:
        ensure_table(cur)
        cur.execute(sql.SQL("SELECT id FROM {}.works WHERE id=%s").format(S), [body.work_id])
        if not cur.fetchone():
            raise HTTPException(404, "Obra no encontrada")
        if body.work_item_id:
            cur.execute(
                sql.SQL("SELECT id FROM {}.work_items WHERE id=%s AND work_id=%s").format(S),
                [body.work_item_id, body.work_id],
            )
            if not cur.fetchone():
                raise HTTPException(400, "El ítem no pertenece a la obra seleccionada")

        progress = normalized_progress(body.status, body.progress_percent)
        cur.execute(sql.SQL("""
            INSERT INTO {}.planning_tasks
            (work_id,work_item_id,title,description,responsible,start_date,end_date,status,priority,progress_percent,notes)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING *
        """).format(S), [
            body.work_id, body.work_item_id, body.title.strip(), body.description,
            body.responsible, body.start_date, body.end_date, body.status,
            body.priority, progress, body.notes
        ])
        return cur.fetchone()


@router.patch("/tasks/{task_id}")
def update_task(task_id: UUID, body: TaskPayload):
    if not body.title.strip():
        raise HTTPException(400, "La tarea necesita un título")
    if body.start_date and body.end_date and body.end_date < body.start_date:
        raise HTTPException(400, "La fecha fin no puede ser anterior al inicio")

    with db_cursor() as cur:
        ensure_table(cur)
        cur.execute(sql.SQL("SELECT id FROM {}.planning_tasks WHERE id=%s").format(S), [task_id])
        if not cur.fetchone():
            raise HTTPException(404, "Tarea no encontrada")
        if body.work_item_id:
            cur.execute(
                sql.SQL("SELECT id FROM {}.work_items WHERE id=%s AND work_id=%s").format(S),
                [body.work_item_id, body.work_id],
            )
            if not cur.fetchone():
                raise HTTPException(400, "El ítem no pertenece a la obra seleccionada")

        progress = normalized_progress(body.status, body.progress_percent)
        cur.execute(sql.SQL("""
            UPDATE {}.planning_tasks SET
              work_id=%s,
              work_item_id=%s,
              title=%s,
              description=%s,
              responsible=%s,
              start_date=%s,
              end_date=%s,
              status=%s,
              priority=%s,
              progress_percent=%s,
              notes=%s,
              updated_at=now()
            WHERE id=%s
            RETURNING *
        """).format(S), [
            body.work_id, body.work_item_id, body.title.strip(), body.description,
            body.responsible, body.start_date, body.end_date, body.status,
            body.priority, progress, body.notes, task_id
        ])
        return cur.fetchone()


@router.delete("/tasks/{task_id}")
def delete_task(task_id: UUID):
    with db_cursor() as cur:
        ensure_table(cur)
        cur.execute(
            sql.SQL("DELETE FROM {}.planning_tasks WHERE id=%s RETURNING id").format(S),
            [task_id],
        )
        if not cur.fetchone():
            raise HTTPException(404, "Tarea no encontrada")
    return {"ok": True}
