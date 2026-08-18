from __future__ import annotations

import secrets
from threading import Lock

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/auth", tags=["auth"])

_ALLOWED_USERS = {"victor", "luciano"}
_PASSWORD = "admin"
_sessions: dict[str, str] = {}
_lock = Lock()


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(payload: LoginRequest):
    username = payload.username.strip().lower()
    if username not in _ALLOWED_USERS or payload.password != _PASSWORD:
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

    token = secrets.token_urlsafe(32)
    with _lock:
        _sessions[token] = username
    return {"token": token, "username": username}


@router.post("/logout")
def logout(authorization: str | None = Header(default=None)):
    token = extract_token(authorization)
    if token:
        with _lock:
            _sessions.pop(token, None)
    return {"ok": True}


@router.get("/me")
def me(authorization: str | None = Header(default=None)):
    username = require_session(authorization)
    return {"username": username}


def extract_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token


def require_session(authorization: str | None) -> str:
    token = extract_token(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Sesión requerida")
    with _lock:
        username = _sessions.get(token)
    if not username:
        raise HTTPException(status_code=401, detail="Sesión inválida o vencida")
    return username


def token_is_valid(token: str | None) -> bool:
    if not token:
        return False
    with _lock:
        return token in _sessions
