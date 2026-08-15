from contextlib import contextmanager
from psycopg_pool import ConnectionPool
from psycopg.rows import dict_row
from .config import get_settings

settings = get_settings()

pool = ConnectionPool(
    conninfo=settings.database_url,
    min_size=1,
    max_size=10,
    kwargs={"row_factory": dict_row, "autocommit": False},
    open=False,
)


def open_pool() -> None:
    pool.open(wait=True)


def close_pool() -> None:
    pool.close()


@contextmanager
def db_cursor():
    with pool.connection() as conn:
        try:
            with conn.cursor() as cur:
                yield cur
            conn.commit()
        except Exception:
            conn.rollback()
            raise
