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
BUCKET = "administracion-obras"


def _storage_headers(content_type: str | None = None):
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise HTTPException(503, "Faltan SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY en Render")
    h = {"Authorization": f"Bearer {settings.supabase_service_role_key}", "apikey": settings.supabase_service_role_key}
    if content_type:
        h["Content-Type"] = content_type
    return h


def _safe_name(name: str) -> str:
    base = Path(name).name
    return re.sub(r"[^A-Za-z0-9._-]+", "_", base)


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
    if file.content_type != "application/pdf" and not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(400, "Por ahora la documentación debe ser PDF")
    data = await file.read()
    if len(data) > 20 * 1024 * 1024:
        raise HTTPException(400, "El PDF supera el máximo de 20 MB")
    filename = _safe_name(file.filename or "documento.pdf")
    path = f"works/{work_id}/{uuid4()}-{filename}"
    url = f"{settings.supabase_url.rstrip('/')}/storage/v1/object/{BUCKET}/{path}"
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(url, headers={**_storage_headers(file.content_type), "x-upsert": "false"}, content=data)
    if r.status_code >= 300:
        raise HTTPException(502, f"Supabase Storage rechazó el archivo: {r.text}")

    with db_cursor() as cur:
        cur.execute(sql.SQL("""
            INSERT INTO {}.work_documents
            (work_id,document_type,title,description,file_name,file_path,mime_type,file_size,related_type,related_id)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING *
        """).format(S), [work_id, document_type, title, description, filename, path, file.content_type, len(data), related_type, related_id])
        return cur.fetchone()


@router.get("/{document_id}/signed-url")
async def signed_url(document_id: UUID):
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
