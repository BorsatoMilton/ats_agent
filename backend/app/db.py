from contextlib import contextmanager

import psycopg2
import psycopg2.extras
from psycopg2.pool import ThreadedConnectionPool
from pgvector.psycopg2 import register_vector

from app.config import settings

_pool: ThreadedConnectionPool | None = None

# inicia pool de conexiones
def init_pool(minconn: int = 1, maxconn: int = 10) -> None:
    global _pool
    if _pool is not None:
        return
    _pool = ThreadedConnectionPool(
        minconn,
        maxconn,
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        dbname=settings.POSTGRES_DB,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
    )

# cierra pool de conexiones
def close_pool() -> None:
    global _pool
    if _pool is not None:
        _pool.closeall()
        _pool = None


@contextmanager
def get_conn():
    if _pool is None:
        init_pool()
    conn = _pool.getconn()
    try:
        register_vector(conn)
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        _pool.putconn(conn)

# funciones de conveniencia para SELECT/INSERT/UPDATE/DELETE
def fetch_all(query: str, params: tuple | dict | None = None) -> list[dict]:
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params)
            return [dict(row) for row in cur.fetchall()]

# funcion para obtener una sola fila
def fetch_one(query: str, params: tuple | dict | None = None) -> dict | None:
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params)
            row = cur.fetchone()
            return dict(row) if row else None

# funcion para ejecutar un query sin retornar nada
def execute(query: str, params: tuple | dict | None = None) -> None:
    """Para INSERT/UPDATE/DELETE sin RETURNING."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)

# funcion para ejecutar un query y retornar una fila
def execute_returning(query: str, params: tuple | dict | None = None) -> dict | None:
    """Para INSERT ... RETURNING * (o columnas puntuales)."""
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params)
            row = cur.fetchone()
            return dict(row) if row else None
