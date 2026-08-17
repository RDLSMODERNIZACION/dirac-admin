from datetime import date, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from psycopg import sql

from ..core.config import get_settings
from ..core.db import db_cursor
from ..core.security import require_api_key

router = APIRouter(prefix="/api/planning", tags=["planning"], dependencies=[Depends(require_api_key)])
settings = get_settings()
S = sql.Identifier(settings.db_schema)


def ensure_tables(cur):
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
            task_type text NOT NULL DEFAULT 'tarea',
            created_at timestamptz NOT NULL DEFAULT now(),
            updated_at timestamptz NOT NULL DEFAULT now()
        )
    """).format(S, S, S))

    cur.execute(sql.SQL("""
        ALTER TABLE {}.planning_tasks
        ADD COLUMN IF NOT EXISTS task_type text NOT NULL DEFAULT 'tarea'
    """).format(S))

    cur.execute(sql.SQL("""
        CREATE TABLE IF NOT EXISTS {}.planning_task_dependencies (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            task_id uuid NOT NULL REFERENCES {}.planning_tasks(id) ON DELETE CASCADE,
            depends_on_task_id uuid NOT NULL REFERENCES {}.planning_tasks(id) ON DELETE CASCADE,
            relation_type text NOT NULL DEFAULT 'finish_start',
            created_at timestamptz NOT NULL DEFAULT now(),
            UNIQUE(task_id, depends_on_task_id)
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
    cur.execute(sql.SQL("""
        CREATE INDEX IF NOT EXISTS planning_dep_task_idx
        ON {}.planning_task_dependencies(task_id)
    """).format(S))
    cur.execute(sql.SQL("""
        CREATE INDEX IF NOT EXISTS planning_dep_parent_idx
        ON {}.planning_task_dependencies(depends_on_task_id)
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
    progress_percent: float = Field(default=0, ge=0, le=100)
    notes: str | None = None
    task_type: str = "tarea"
    predecessor_ids: list[UUID] = []


class MovePayload(BaseModel):
    start_date: date
    end_date: date
    cascade: bool = True


def validate_payload(body: TaskPayload):
    if not body.title.strip():
        raise HTTPException(400, "La tarea necesita un título")
    if body.start_date and body.end_date and body.end_date < body.start_date:
        raise HTTPException(400, "La fecha fin no puede ser anterior al inicio")
    if body.task_type not in ("tarea", "hito"):
        raise HTTPException(400, "Tipo de tarea inválido")
    if body.status not in ("pendiente", "en_ejecucion", "pausada", "completada"):
        raise HTTPException(400, "Estado inválido")
    if body.priority not in ("baja", "media", "alta", "critica"):
        raise HTTPException(400, "Prioridad inválida")


def normalized_progress(status: str, progress: float):
    if status == "completada":
        return 100
    return max(0, min(100, progress or 0))


def ensure_work_item(cur, work_id, work_item_id):
    cur.execute(sql.SQL("SELECT id FROM {}.works WHERE id=%s").format(S), [work_id])
    if not cur.fetchone():
        raise HTTPException(404, "Obra no encontrada")
    if work_item_id:
        cur.execute(
            sql.SQL("SELECT id FROM {}.work_items WHERE id=%s AND work_id=%s").format(S),
            [work_item_id, work_id],
        )
        if not cur.fetchone():
            raise HTTPException(400, "El ítem no pertenece a la obra seleccionada")


def would_create_cycle(cur, task_id: UUID, predecessor_id: UUID):
    if task_id == predecessor_id:
        return True
    cur.execute(sql.SQL("""
        WITH RECURSIVE upstream(id) AS (
            SELECT depends_on_task_id
            FROM {}.planning_task_dependencies
            WHERE task_id=%s
            UNION
            SELECT d.depends_on_task_id
            FROM {}.planning_task_dependencies d
            JOIN upstream u ON d.task_id=u.id
        )
        SELECT EXISTS(SELECT 1 FROM upstream WHERE id=%s) AS cycle
    """).format(S, S), [predecessor_id, task_id])
    return bool(cur.fetchone()["cycle"])


def save_dependencies(cur, task_id: UUID, predecessor_ids: list[UUID], work_id: UUID):
    predecessor_ids = list(dict.fromkeys(predecessor_ids or []))
    for pid in predecessor_ids:
        cur.execute(
            sql.SQL("SELECT work_id FROM {}.planning_tasks WHERE id=%s").format(S),
            [pid],
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(400, "Una antecesora seleccionada ya no existe")
        if row["work_id"] != work_id:
            raise HTTPException(400, "Las antecesoras deben pertenecer a la misma obra")
        if would_create_cycle(cur, task_id, pid):
            raise HTTPException(400, "Esa dependencia generaría un ciclo en el cronograma")

    cur.execute(
        sql.SQL("DELETE FROM {}.planning_task_dependencies WHERE task_id=%s").format(S),
        [task_id],
    )
    for pid in predecessor_ids:
        cur.execute(sql.SQL("""
            INSERT INTO {}.planning_task_dependencies
            (task_id, depends_on_task_id, relation_type)
            VALUES (%s,%s,'finish_start')
            ON CONFLICT (task_id, depends_on_task_id) DO NOTHING
        """).format(S), [task_id, pid])


def task_select_sql(where_clause=""):
    return sql.SQL(f"""
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
            END AS is_overdue,
            COALESCE((
                SELECT json_agg(json_build_object(
                    'id', p.id,
                    'title', p.title,
                    'start_date', p.start_date,
                    'end_date', p.end_date,
                    'status', p.status
                ) ORDER BY p.end_date NULLS LAST, p.title)
                FROM {{}}.planning_task_dependencies d
                JOIN {{}}.planning_tasks p ON p.id=d.depends_on_task_id
                WHERE d.task_id=t.id
            ), '[]'::json) AS predecessors,
            COALESCE((
                SELECT json_agg(json_build_object(
                    'id', s.id,
                    'title', s.title,
                    'start_date', s.start_date,
                    'end_date', s.end_date,
                    'status', s.status
                ) ORDER BY s.start_date NULLS LAST, s.title)
                FROM {{}}.planning_task_dependencies d
                JOIN {{}}.planning_tasks s ON s.id=d.task_id
                WHERE d.depends_on_task_id=t.id
            ), '[]'::json) AS successors
        FROM {{}}.planning_tasks t
        JOIN {{}}.works w ON w.id=t.work_id
        LEFT JOIN {{}}.clients c ON c.id=w.client_id
        LEFT JOIN {{}}.work_items wi ON wi.id=t.work_item_id
        {where_clause}
    """)


@router.get("/tasks")
def list_tasks(work_id: UUID | None = None):
    with db_cursor() as cur:
        ensure_tables(cur)
        where = "WHERE t.work_id=%s" if work_id else ""
        params = [work_id] if work_id else []
        q = task_select_sql(where) + sql.SQL("""
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
        return cur.fetchall()


@router.get("/tasks/{task_id}")
def get_task(task_id: UUID):
    with db_cursor() as cur:
        ensure_tables(cur)
        q = task_select_sql("WHERE t.id=%s")
        cur.execute(q.format(S, S, S, S, S, S, S, S), [task_id])
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "Tarea no encontrada")
        return row


@router.get("/summary")
def summary(work_id: UUID | None = None):
    with db_cursor() as cur:
        ensure_tables(cur)
        where = "WHERE work_id=%s" if work_id else ""
        params = [work_id] if work_id else []
        cur.execute(sql.SQL(f"""
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
            FROM {{}}.planning_tasks
            {where}
        """).format(S), params)
        return cur.fetchone()


@router.post("/tasks")
def create_task(body: TaskPayload):
    validate_payload(body)
    with db_cursor() as cur:
        ensure_tables(cur)
        ensure_work_item(cur, body.work_id, body.work_item_id)

        start_date = body.start_date
        end_date = body.end_date
        if body.task_type == "hito" and start_date:
            end_date = start_date

        progress = normalized_progress(body.status, body.progress_percent)
        cur.execute(sql.SQL("""
            INSERT INTO {}.planning_tasks
            (work_id,work_item_id,title,description,responsible,start_date,end_date,status,
             priority,progress_percent,notes,task_type)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING *
        """).format(S), [
            body.work_id, body.work_item_id, body.title.strip(), body.description,
            body.responsible, start_date, end_date, body.status,
            body.priority, progress, body.notes, body.task_type
        ])
        row = cur.fetchone()
        save_dependencies(cur, row["id"], body.predecessor_ids, body.work_id)
        return row


@router.patch("/tasks/{task_id}")
def update_task(task_id: UUID, body: TaskPayload):
    validate_payload(body)
    with db_cursor() as cur:
        ensure_tables(cur)
        ensure_work_item(cur, body.work_id, body.work_item_id)

        cur.execute(
            sql.SQL("SELECT * FROM {}.planning_tasks WHERE id=%s FOR UPDATE").format(S),
            [task_id],
        )
        previous = cur.fetchone()
        if not previous:
            raise HTTPException(404, "Tarea no encontrada")

        start_date = body.start_date
        end_date = body.end_date
        if body.task_type == "hito" and start_date:
            end_date = start_date

        progress = normalized_progress(body.status, body.progress_percent)
        cur.execute(sql.SQL("""
            UPDATE {}.planning_tasks SET
              work_id=%s, work_item_id=%s, title=%s, description=%s, responsible=%s,
              start_date=%s, end_date=%s, status=%s, priority=%s, progress_percent=%s,
              notes=%s, task_type=%s, updated_at=now()
            WHERE id=%s
            RETURNING *
        """).format(S), [
            body.work_id, body.work_item_id, body.title.strip(), body.description,
            body.responsible, start_date, end_date, body.status,
            body.priority, progress, body.notes, body.task_type, task_id
        ])
        row = cur.fetchone()
        save_dependencies(cur, task_id, body.predecessor_ids, body.work_id)
        return row


@router.post("/tasks/{task_id}/move")
def move_task(task_id: UUID, body: MovePayload):
    if body.end_date < body.start_date:
        raise HTTPException(400, "La fecha fin no puede ser anterior al inicio")
    with db_cursor() as cur:
        ensure_tables(cur)
        cur.execute(
            sql.SQL("SELECT * FROM {}.planning_tasks WHERE id=%s FOR UPDATE").format(S),
            [task_id],
        )
        task = cur.fetchone()
        if not task:
            raise HTTPException(404, "Tarea no encontrada")

        old_start = task["start_date"]
        old_end = task["end_date"]
        start_date = body.start_date
        end_date = body.start_date if task["task_type"] == "hito" else body.end_date

        cur.execute(sql.SQL("""
            UPDATE {}.planning_tasks
            SET start_date=%s,end_date=%s,updated_at=now()
            WHERE id=%s
        """).format(S), [start_date, end_date, task_id])

        if body.cascade and old_end and end_date:
            delta = (end_date - old_end).days
            if delta != 0:
                cur.execute(sql.SQL("""
                    WITH RECURSIVE downstream(id, depth) AS (
                        SELECT task_id, 1
                        FROM {}.planning_task_dependencies
                        WHERE depends_on_task_id=%s
                        UNION
                        SELECT d.task_id, ds.depth+1
                        FROM {}.planning_task_dependencies d
                        JOIN downstream ds ON d.depends_on_task_id=ds.id
                    )
                    SELECT DISTINCT id, MIN(depth) AS depth
                    FROM downstream
                    GROUP BY id
                    ORDER BY MIN(depth)
                """).format(S, S), [task_id])
                dependent_ids = [x["id"] for x in cur.fetchall()]
                for sid in dependent_ids:
                    cur.execute(
                        sql.SQL("SELECT start_date,end_date FROM {}.planning_tasks WHERE id=%s FOR UPDATE").format(S),
                        [sid],
                    )
                    dep = cur.fetchone()
                    if dep and dep["start_date"]:
                        ns = dep["start_date"] + timedelta(days=delta)
                        ne = dep["end_date"] + timedelta(days=delta) if dep["end_date"] else ns
                        cur.execute(sql.SQL("""
                            UPDATE {}.planning_tasks
                            SET start_date=%s,end_date=%s,updated_at=now()
                            WHERE id=%s
                        """).format(S), [ns, ne, sid])

    return {"ok": True}


@router.post("/tasks/{task_id}/duplicate")
def duplicate_task(task_id: UUID):
    with db_cursor() as cur:
        ensure_tables(cur)
        cur.execute(
            sql.SQL("SELECT * FROM {}.planning_tasks WHERE id=%s").format(S),
            [task_id],
        )
        t = cur.fetchone()
        if not t:
            raise HTTPException(404, "Tarea no encontrada")
        cur.execute(sql.SQL("""
            INSERT INTO {}.planning_tasks
            (work_id,work_item_id,title,description,responsible,start_date,end_date,status,
             priority,progress_percent,notes,task_type)
            VALUES (%s,%s,%s,%s,%s,%s,%s,'pendiente',%s,0,%s,%s)
            RETURNING id
        """).format(S), [
            t["work_id"], t["work_item_id"], f'{t["title"]} (copia)', t["description"],
            t["responsible"], t["start_date"], t["end_date"], t["priority"],
            t["notes"], t["task_type"]
        ])
        new_id = cur.fetchone()["id"]
        cur.execute(sql.SQL("""
            INSERT INTO {}.planning_task_dependencies(task_id,depends_on_task_id,relation_type)
            SELECT %s,depends_on_task_id,relation_type
            FROM {}.planning_task_dependencies
            WHERE task_id=%s
        """).format(S, S), [new_id, task_id])
    return {"ok": True, "id": new_id}


@router.delete("/tasks/{task_id}")
def delete_task(task_id: UUID):
    with db_cursor() as cur:
        ensure_tables(cur)
        cur.execute(
            sql.SQL("DELETE FROM {}.planning_tasks WHERE id=%s RETURNING id").format(S),
            [task_id],
        )
        if not cur.fetchone():
            raise HTTPException(404, "Tarea no encontrada")
    return {"ok": True}
