"""DORMANT: Lakebase (Autoscaling Postgres) connection pool.

Not imported by the app yet -- kept ready for future user-state (saved plans,
chat history). When enabled, set ENDPOINT_NAME plus the PG* env vars (the first
DB resource on a Databricks App is auto-injected: PGHOST/PGPORT/PGDATABASE/
PGUSER/PGSSLMODE).

Credentials are minted just-in-time per physical connection and recycled before
the ~1h token expiry. No token is ever stored or written to disk.
"""
import os

# Imported lazily so the app runs without psycopg installed locally.
def build_pool():
    import psycopg
    from psycopg_pool import ConnectionPool
    from databricks.sdk import WorkspaceClient

    w = WorkspaceClient()

    class OAuthConnection(psycopg.Connection):
        @classmethod
        def connect(cls, conninfo="", **kwargs):
            cred = w.postgres.generate_database_credential(
                endpoint=os.environ["ENDPOINT_NAME"]
            )
            kwargs["password"] = cred.token
            return super().connect(conninfo, **kwargs)

    return ConnectionPool(
        conninfo=(
            f"dbname={os.environ['PGDATABASE']} "
            f"user={os.environ['PGUSER']} "
            f"host={os.environ['PGHOST']} "
            f"port={os.environ.get('PGPORT', '5432')} "
            f"sslmode={os.environ.get('PGSSLMODE', 'require')}"
        ),
        connection_class=OAuthConnection,
        min_size=1,
        max_size=10,
        max_lifetime=2700,  # recycle before token expiry
        open=True,
    )
