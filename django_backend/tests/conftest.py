import os

import pytest


def _postgres_reachable() -> bool:
    url = os.getenv(
        "DATABASE_URL",
        "postgres://petsfirst:petsfirst123@127.0.0.1:5433/petsfirst_db",
    )
    if url.startswith("sqlite"):
        return True
    try:
        import psycopg

        psycopg.connect(url, connect_timeout=2).close()
        return True
    except Exception:
        return False


requires_postgres = pytest.mark.skipif(
    not _postgres_reachable(),
    reason="PostgreSQL is not reachable (start docker compose db service)",
)
