from typing import Any
from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, ConfigDict

from ..crud import list_rows, get_row, create_row, update_row, delete_row
from ..core.security import require_api_key
from ..metadata import TABLES

router = APIRouter(prefix="/api", dependencies=[Depends(require_api_key)])


class Payload(BaseModel):
    model_config = ConfigDict(extra="allow")


@router.get("/meta/tables")
def tables():
    return {name: {"writable": meta["writable"], "search": meta.get("search", [])} for name, meta in TABLES.items()}


@router.get("/{table}")
def rows(
    request: Request,
    table: str,
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    q: str | None = None,
):
    # Any other query parameter matching a writable column becomes an equality filter.
    reserved = {"limit", "offset", "q"}
    filters: dict[str, Any] = {k: v for k, v in request.query_params.items() if k not in reserved}
    return list_rows(table, limit=limit, offset=offset, q=q, filters=filters)


@router.get("/{table}/{row_id}")
def row(table: str, row_id: str):
    return get_row(table, row_id)


@router.post("/{table}", status_code=201)
def create(table: str, payload: Payload):
    return create_row(table, payload.model_dump(exclude_unset=True))


@router.patch("/{table}/{row_id}")
def update(table: str, row_id: str, payload: Payload):
    return update_row(table, row_id, payload.model_dump(exclude_unset=True))


@router.delete("/{table}/{row_id}")
def delete(table: str, row_id: str):
    return delete_row(table, row_id)
