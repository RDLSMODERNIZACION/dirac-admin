import os
import re
from pathlib import Path
from uuid import UUID, uuid4

import httpx
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from psycopg import sql

from ..core.config import get_settings
from ..core.db import db_cursor
from ..core.security import require_api_key

router = APIRouter(prefix="/api/work-documents", tags=["work-documents"], dependencies=[Depends(require_api_key)])
settings = get_settings()
S = sql.Identifier(settings.db_schema)
BUCKET = os.getenv("SUPABASE_STORAGE_BUCKET", "administracion-obras").strip() or "administracion-obras"


def _storage_headers(content_type: str | None = None):
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise HTTPException(503, "Faltan SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY en Render")
    h = {
        "Authorization": f"Bearer {settings.supabase_service_role_key}",
        "apikey": settings.supabase_service_role_key,
    }
    if content_type:
        h["Content-Type"] = content_type
    return h


def _safe_name(name: str) -> str:
    base = Path(name).name
    return re.sub(r"[^A-Za-z0-9._-]+", "_", base)


def _storage_object_url(path: str) -> str:
    return f"{settings.supabase_url.rstrip('/')}/storage/v1/object/{BUCKET}/{path}"

async def _ensure_bucket():
    base = settings.supabase_url.rstrip("/")

    async with httpx.AsyncClient(timeout=30) as client:
        check = await client.get(
            f"{base}/storage/v1/bucket/{BUCKET}",
            headers=_storage_headers(),
        )

        if check.status_code == 200:
            return

        if check.status_code != 404:
            raise HTTPException(502, f"No se pudo consultar bucket '{BUCKET}': {check.text}")

        create = await client.post(
            f"{base}/storage/v1/bucket",
            headers={**_storage_headers("application/json")},
            json={"id": BUCKET, "name": BUCKET, "public": False},
        )

    if create.status_code in (200, 201):
        return

    body = (create.text or "").lower()
    if create.status_code in (400, 409) and (
        "already exists" in body or "duplicate" in body or "bucket exists" in body
    ):
        return

    raise HTTPException(502, f"No se pudo crear bucket '{BUCKET}': {create.text}")



async def _upload_pdf(work_id: UUID, file: UploadFile) -> tuple[str, str, str | None, int]:
    await _ensure_bucket()
    if file.content_type != "application/pdf" and not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(400, "Por ahora la documentación debe ser PDF")
    data = await file.read()
    if len(data) > 20 * 1024 * 1024:
        raise HTTPException(400, "El PDF supera el máximo de 20 MB")

    filename = _safe_name(file.filename or "documento.pdf")
    path = f"works/{work_id}/{uuid4()}-{filename}"
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            _storage_object_url(path),
            headers={**_storage_headers(file.content_type), "x-upsert": "false"},
            content=data,
        )
    if r.status_code >= 300:
        raise HTTPException(502, f"Supabase Storage rechazó el archivo: {r.text}")
    return filename, path, file.content_type, len(data)


async def _delete_storage_file(path: str | None, *, strict: bool = False):
    if not path:
        return
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.delete(_storage_object_url(path), headers=_storage_headers())
    if strict and r.status_code not in (200, 204, 404):
        raise HTTPException(502, f"No se pudo eliminar el archivo de Supabase Storage: {r.text}")


@router.post("/upload")
async def upload_document(
    work_id: UUID = Form(...),
    document_type: str = Form(...),
    title: str = Form(...),
    description: str | None = Form(None),
    related_type: str | None = Form(None),
    related_id: UUID | None = Form(None),
    file: UploadFile = File(...),
):
    filename, path, mime_type, file_size = await _upload_pdf(work_id, file)

    with db_cursor() as cur:
        cur.execute(
            sql.SQL("""
                INSERT INTO {}.work_documents
                (work_id,document_type,title,description,file_name,file_path,mime_type,file_size,related_type,related_id)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                RETURNING *
            """).format(S),
            [work_id, document_type, title, description, filename, path, mime_type, file_size, related_type, related_id],
        )
        return cur.fetchone()


@router.patch("/{document_id}")
async def edit_document(
    document_id: UUID,
    document_type: str | None = Form(None),
    title: str | None = Form(None),
    description: str | None = Form(None),
    file: UploadFile | None = File(None),
):
    with db_cursor() as cur:
        cur.execute(sql.SQL("SELECT * FROM {}.work_documents WHERE id=%s").format(S), [document_id])
        doc = cur.fetchone()
    if not doc:
        raise HTTPException(404, "Documento no encontrado")

    new_file = None
    if file is not None and file.filename:
        new_file = await _upload_pdf(doc["work_id"], file)

    # Los documentos vinculados a facturas/cobros conservan su tipo para no romper la relación funcional.
    final_type = doc["document_type"] if doc.get("related_type") else (document_type or doc["document_type"])
    final_title = (title or "").strip() or doc["title"]
    final_description = description if description is not None else doc.get("description")

    if new_file:
        filename, path, mime_type, file_size = new_file
    else:
        filename, path, mime_type, file_size = doc["file_name"], doc["file_path"], doc.get("mime_type"), doc.get("file_size")

    with db_cursor() as cur:
        cur.execute(
            sql.SQL("""
                UPDATE {}.work_documents
                SET document_type=%s, title=%s, description=%s,
                    file_name=%s, file_path=%s, mime_type=%s, file_size=%s
                WHERE id=%s
                RETURNING *
            """).format(S),
            [final_type, final_title, final_description, filename, path, mime_type, file_size, document_id],
        )
        updated = cur.fetchone()

    if new_file and doc.get("file_path") != path:
        # La BD ya apunta al nuevo PDF. Si falla la limpieza del viejo no se rompe el documento nuevo.
        await _delete_storage_file(doc.get("file_path"), strict=False)

    return updated


@router.delete("/{document_id}")
async def delete_document(document_id: UUID):
    with db_cursor() as cur:
        cur.execute(sql.SQL("SELECT * FROM {}.work_documents WHERE id=%s").format(S), [document_id])
        doc = cur.fetchone()
    if not doc:
        raise HTTPException(404, "Documento no encontrado")

    # Primero borramos el objeto. Si Storage falla, no eliminamos el registro para evitar perder la referencia.
    await _delete_storage_file(doc.get("file_path"), strict=True)

    with db_cursor() as cur:
        cur.execute(sql.SQL("DELETE FROM {}.work_documents WHERE id=%s RETURNING id").format(S), [document_id])
        deleted = cur.fetchone()
    return {"ok": True, "id": str(deleted["id"] if deleted else document_id)}


@router.get("/{document_id}/signed-url")
async def signed_url(document_id: UUID):
    await _ensure_bucket()
    with db_cursor() as cur:
        cur.execute(sql.SQL("SELECT file_path,file_name FROM {}.work_documents WHERE id=%s").format(S), [document_id])
        doc = cur.fetchone()
        if not doc:
            raise HTTPException(404, "Documento no encontrado")
    url = f"{settings.supabase_url.rstrip('/')}/storage/v1/object/sign/{BUCKET}/{doc['file_path']}"
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(url, headers={**_storage_headers("application/json")}, json={"expiresIn": 3600})
    if r.status_code >= 300:
        raise HTTPException(502, f"No se pudo firmar el documento: {r.text}")
    payload = r.json()
    signed = payload.get("signedURL") or payload.get("signedUrl")
    if signed and signed.startswith("/"):
        signed = settings.supabase_url.rstrip("/") + "/storage/v1" + signed if not signed.startswith("/storage/v1") else settings.supabase_url.rstrip("/") + signed
    return {"url": signed, "file_name": doc["file_name"], "expires_in": 3600}
