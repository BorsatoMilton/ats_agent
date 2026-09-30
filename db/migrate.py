import os
import sys
import glob
import psycopg2

MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "migrations")


def get_connection():
    return psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        port=os.environ.get("POSTGRES_PORT", "5432"),
        dbname=os.environ.get("POSTGRES_DB", "ats_db"),
        user=os.environ.get("POSTGRES_USER", "ats_user"),
        password=os.environ.get("POSTGRES_PASSWORD", "ats_pass"),
    )


def ensure_migrations_table(conn):
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                filename    TEXT PRIMARY KEY,
                applied_at  TIMESTAMPTZ NOT NULL DEFAULT now()
            );
            """
        )
    conn.commit()


def get_applied(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT filename FROM schema_migrations;")
        return {row[0] for row in cur.fetchall()}


def run_migrations():
    conn = get_connection()
    try:
        ensure_migrations_table(conn)
        applied = get_applied(conn)

        files = sorted(glob.glob(os.path.join(MIGRATIONS_DIR, "*.sql")))
        pending = [f for f in files if os.path.basename(f) not in applied]

        if not pending:
            print("No hay migraciones pendientes.")
            return

        for filepath in pending:
            filename = os.path.basename(filepath)
            print(f"Aplicando {filename} ...")
            with open(filepath, "r", encoding="utf-8") as f:
                sql = f.read()
            with conn.cursor() as cur:
                cur.execute(sql)
                cur.execute(
                    "INSERT INTO schema_migrations (filename) VALUES (%s);",
                    (filename,),
                )
            conn.commit()
            print(f"  OK: {filename}")

        print(f"Listo. {len(pending)} migracion(es) aplicada(s).")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    try:
        run_migrations()
    except Exception as exc:  # noqa: BLE001
        print(f"Error corriendo migraciones: {exc}", file=sys.stderr)
        sys.exit(1)
