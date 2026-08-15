import re
from pathlib import Path
from uuid import UUID, uuid4

import httpx
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from psycopg import sql

from ..core.config import get_settings
from ..core.db import db_cursor
from ..core.security import require_api_key

router = APIRouter(prefix="/api/service-documents", tags=["service-documents"], dependencies=[Depends(require_api_key)])
settings = get_settings()
S = sql.Identifier(settings.db_schema)
BUCKET = "administracion-servicios"


def _headers(content_type: str | None = None):
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise HTTPException(503, "Faltan SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY en Render")
    h = {"Authorization": f"Bearer {settings.supabase_service_role_key}", "apikey": settings.supabase_service_role_key}
    if content_type:
        h["Content-Type"] = content_type
    return h


def _safe_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", Path(name).name)


async def _ensure_bucket():
    base = settings.supabase_url.rstrip("/")
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(f"{base}/storage/v1/bucket/{BUCKET}", headers=_headers())
        if r.status_code == 404:
            c = await client.post(f"{base}/storage/v1/bucket", headers={**_headers("application/json")},
                                  json={"id": BUCKET, "name": BUCKET, "public": False, "file_size_limit": 20971520})
            if c.status_code >= 300 and c.status_code != 409:
                raise HTTPException(502, f"No se pudo crear bucket: {c.text}")
        elif r.status_code >= 300:
            raise HTTPException(502, f"No se pudo consultar bucket: {r.text}")


@router.post("/upload")
async def upload_service_document(
    service_id: UUID = Form(...),
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

    await _ensure_bucket()
    filename = _safe_name(file.filename or "documento.pdf")
    path = f"services/{service_id}/{uuid4()}-{filename}"
    url = f"{settings.supabase_url.rstrip('/')}/storage/v1/object/{BUCKET}/{path}"
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(url, headers={**_headers(file.content_type), "x-upsert": "false"}, content=data)
    if r.status_code >= 300:
        raise HTTPException(502, f"Supabase Storage rechazó el archivo: {r.text}")

    with db_cursor() as cur:
        cur.execute(sql.SQL("""
            INSERT INTO {}.service_documents
              (service_id,document_type,title,description,file_name,file_path,mime_type,file_size,related_type,related_id)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING *
        """).format(S), [service_id, document_type, title, description, filename, path,
                          file.content_type, len(data), related_type, related_id])
        return cur.fetchone()


@router.get("/{document_id}/signed-url")
async def signed_url(document_id: UUID):
    with db_cursor() as cur:
        cur.execute(sql.SQL("SELECT file_path,file_name FROM {}.service_documents WHERE id=%s").format(S), [document_id])
        doc = cur.fetchone()
        if not doc:
            raise HTTPException(404, "Documento no encontrado")

    await _ensure_bucket()
    url = f"{settings.supabase_url.rstrip('/')}/storage/v1/object/sign/{BUCKET}/{doc['file_path']}"
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(url, headers={**_headers("application/json")}, json={"expiresIn": 3600})
    if r.status_code >= 300:
        raise HTTPException(502, f"No se pudo firmar el documento: {r.text}")
    payload = r.json()
    signed = payload.get("signedURL") or payload.get("signedUrl")
    if signed and signed.startswith("/"):
        signed = settings.supabase_url.rstrip("/") + signed
    return {"url": signed, "file_name": doc["file_name"], "expires_in": 3600}
