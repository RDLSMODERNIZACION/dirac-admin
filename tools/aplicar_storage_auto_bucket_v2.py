from pathlib import Path

p = Path.cwd() / 'backend/app/routers/documents.py'
t = p.read_text(encoding='utf-8')

if 'import os\n' not in t:
    t = t.replace('import re\n', 'import os\nimport re\n', 1)

old_bucket = 'BUCKET = "administracion-obras"'
new_bucket = 'BUCKET = os.getenv("SUPABASE_STORAGE_BUCKET", "administracion-obras").strip() or "administracion-obras"'
if old_bucket in t:
    t = t.replace(old_bucket, new_bucket, 1)
elif new_bucket not in t:
    raise SystemExit('ERROR: no encontré BUCKET')

if 'async def _ensure_bucket():' not in t:
    marker = 'def _storage_object_url(path: str) -> str:\n    return f"{settings.supabase_url.rstrip(\'/\')}/storage/v1/object/{BUCKET}/{path}"\n\n'
    if marker not in t:
        raise SystemExit('ERROR: _storage_object_url no encontrado')
    helper = '''async def _ensure_bucket():
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


'''
    t = t.replace(marker, marker + helper, 1)

old_upload = 'async def _upload_pdf(work_id: UUID, file: UploadFile) -> tuple[str, str, str | None, int]:\n    if file.content_type != "application/pdf"'
new_upload = 'async def _upload_pdf(work_id: UUID, file: UploadFile) -> tuple[str, str, str | None, int]:\n    await _ensure_bucket()\n    if file.content_type != "application/pdf"'
if old_upload in t:
    t = t.replace(old_upload, new_upload, 1)

old_signed = '@router.get("/{document_id}/signed-url")\nasync def signed_url(document_id: UUID):\n    with db_cursor() as cur:'
new_signed = '@router.get("/{document_id}/signed-url")\nasync def signed_url(document_id: UUID):\n    await _ensure_bucket()\n    with db_cursor() as cur:'
if old_signed in t:
    t = t.replace(old_signed, new_signed, 1)

p.write_text(t, encoding='utf-8')
print('OK: Supabase Storage ahora verifica/crea el bucket automáticamente.')