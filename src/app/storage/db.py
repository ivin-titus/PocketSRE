"""Neon Postgres persistence (PRD §9.2).

Sync psycopg driver — call sites run inside `asyncio.to_thread` where async.
Schema mirrors the PRD DDL so the Neon SQL-editor setup step matches in-repo.
"""

from uuid import UUID

import psycopg

DDL = """
CREATE TABLE IF NOT EXISTS incidents (
    id VARCHAR(64) PRIMARY KEY,
    service_name VARCHAR(64) NOT NULL,
    status VARCHAR(32) NOT NULL,
    severity VARCHAR(16) NOT NULL,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    incident_id VARCHAR(64) REFERENCES incidents(id),
    actor_id VARCHAR(64) NOT NULL,
    actor_role VARCHAR(32) NOT NULL,
    action_type VARCHAR(64) NOT NULL,
    status VARCHAR(32) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS budget_ledger (
    id SERIAL PRIMARY KEY,
    incident_id VARCHAR(64),
    provider VARCHAR(32) NOT NULL DEFAULT 'llm',
    amount_spent NUMERIC(10,4) DEFAULT 0.0000,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
"""


class Database:
    """Thin write-through layer over Neon Postgres."""

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn
        self.init_schema()

    def init_schema(self) -> None:
        with psycopg.connect(self._dsn) as conn, conn.cursor() as cur:
            cur.execute(DDL)
            conn.commit()

    def keepalive(self) -> None:
        """Neon suspends idle free-tier computes; ping to keep it warm."""
        with psycopg.connect(self._dsn) as conn, conn.cursor() as cur:
            cur.execute("SELECT 1")

    def upsert_incident(
        self,
        incident_id: UUID,
        service: str,
        status: str,
        severity: str,
        error_message: str,
        resolved: bool,
    ) -> None:
        sql = (
            "INSERT INTO incidents (id, service_name, status, severity, error_message)"
            " VALUES (%s, %s, %s, %s, %s)"
            " ON CONFLICT (id) DO UPDATE SET"
            "   status = EXCLUDED.status,"
            "   resolved_at = CASE WHEN %s THEN NOW() ELSE incidents.resolved_at END"
        )
        with psycopg.connect(self._dsn) as conn, conn.cursor() as cur:
            cur.execute(
                sql, (str(incident_id), service, status, severity, error_message, resolved)
            )
            conn.commit()

    def append_audit(
        self,
        incident_id: UUID,
        actor_id: str,
        actor_role: str,
        action_type: str,
        status: str,
    ) -> None:
        sql = (
            "INSERT INTO audit_logs"
            " (incident_id, actor_id, actor_role, action_type, status)"
            " VALUES (%s, %s, %s, %s, %s)"
        )
        with psycopg.connect(self._dsn) as conn, conn.cursor() as cur:
            cur.execute(
                sql, (str(incident_id), actor_id, actor_role, action_type, status)
            )
            conn.commit()

    def record_spend(self, incident_id: UUID | None, provider: str, amount: float) -> None:
        sql = (
            "INSERT INTO budget_ledger (incident_id, provider, amount_spent)"
            " VALUES (%s, %s, %s)"
        )
        with psycopg.connect(self._dsn) as conn, conn.cursor() as cur:
            cur.execute(sql, (str(incident_id) if incident_id else None, provider, amount))
            conn.commit()

    def incident_spend(self, incident_id: UUID) -> float:
        sql = "SELECT COALESCE(SUM(amount_spent), 0) FROM budget_ledger WHERE incident_id = %s"
        with psycopg.connect(self._dsn) as conn, conn.cursor() as cur:
            cur.execute(sql, (str(incident_id),))
            return float(cur.fetchone()[0])
