from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from psycopg import sql

from .core.config import get_settings
from .core.db import open_pool, close_pool, db_cursor
from .routers.generic import router as generic_router
from .routers.dashboard import router as dashboard_router
from .routers.reports import router as reports_router
from .routers.works import router as works_router
from .routers.work_detail import router as work_detail_router
from .routers.documents import router as documents_router
from .routers.service_detail import router as service_detail_router
from .routers.service_documents import router as service_documents_router
from .routers.debts import router as debts_router
from .routers.financial_movements import router as financial_movements_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    open_pool()
    yield
    close_pool()


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Backend de gestión integral de Dirac sobre el schema PostgreSQL administracion.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"service": settings.app_name, "status": "ok", "docs": "/docs"}


@app.get("/health")
def health():
    with db_cursor() as cur:
        cur.execute(sql.SQL("SELECT current_database() AS database, current_schema() AS default_schema, now() AS server_time"))
        db = cur.fetchone()
        cur.execute(sql.SQL("SELECT EXISTS(SELECT 1 FROM information_schema.schemata WHERE schema_name=%s) AS schema_exists"), [settings.db_schema])
        schema = cur.fetchone()
    return {"status": "ok", "database": db, "schema": settings.db_schema, **schema}


app.include_router(dashboard_router)
app.include_router(reports_router)
app.include_router(works_router)
app.include_router(work_detail_router)
app.include_router(documents_router)
app.include_router(service_detail_router)
app.include_router(service_documents_router)
app.include_router(debts_router)
app.include_router(financial_movements_router)
app.include_router(generic_router)
