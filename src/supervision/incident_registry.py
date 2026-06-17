import sqlite3
import os
import hashlib
import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger("IncidentRegistry")


class IncidentRegistry:
    def __init__(self, db_path: str = "config/sre_audit.db"):
        self.db_path = db_path
        self.execution_id = datetime.now().strftime("%Y-%m-%d-%H%M")

        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        self._init_db()

    def _init_db(self):
        """Inicializa el esquema relacional definitivo para el Control Plane."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS incidents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    execution_id TEXT NOT NULL,
                    fingerprint TEXT UNIQUE,
                    pipeline_id TEXT NOT NULL,
                    job_name TEXT NOT NULL,
                    detected_at TEXT NOT NULL,
                    error_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    decision TEXT NOT NULL,
                    mr_id TEXT,
                    mr_url TEXT,
                    status TEXT NOT NULL,
                    recommended_action TEXT,
                    reason TEXT
                )
            """)

            conn.commit()

    def calculate_fingerprint(self, pipeline: Dict[str, Any]) -> str:
        """Genera una firma criptográfica única del incidente (SHA-256)."""

        ctx_string = (
            f"{pipeline.get('project_id', '')}:"
            f"{pipeline.get('pipeline_id', '')}:"
            f"{pipeline.get('failed_job_name', '')}:"
            f"{pipeline.get('error_type', '')}"
        )

        return hashlib.sha256(
            ctx_string.encode("utf-8")
        ).hexdigest()

    async def is_already_treated(self, fingerprint: str) -> bool:
        """Comprueba de forma determinística si el incidente ya fue procesado."""

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT id
                FROM incidents
                WHERE fingerprint = ?
                AND status IN ('WAITING_APPROVAL', 'BLOCKED')
                """,
                (fingerprint,)
            )

            return cursor.fetchone() is not None

    async def register_incident(self, pipeline: Dict[str, Any]) -> int:
        fingerprint = self.calculate_fingerprint(pipeline)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            try:
                cursor.execute("""
                    INSERT INTO incidents (
                        execution_id,
                        fingerprint,
                        pipeline_id,
                        job_name,
                        detected_at,
                        error_type,
                        severity,
                        confidence,
                        decision,
                        status
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.execution_id,
                    fingerprint,
                    str(pipeline.get("pipeline_id", "0")),
                    pipeline.get("failed_job_name", "unknown_job"),
                    datetime.now().isoformat(),
                    pipeline.get("error_type", "UNKNOWN"),
                    "high",
                    0.0,
                    "PENDING",
                    "OPEN"
                ))

                conn.commit()

                return cursor.lastrowid

            except sqlite3.IntegrityError:
                cursor.execute(
                    "SELECT id FROM incidents WHERE fingerprint = ?",
                    (fingerprint,)
                )

                row = cursor.fetchone()

                return row[0] if row else None

    async def update_incident_triage(
        self,
        incident_id: int,
        analysis_meta: Any
    ):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE incidents
                SET
                    error_type = ?,
                    severity = ?,
                    confidence = ?,
                    decision = ?,
                    reason = ?,
                    recommended_action = ?
                WHERE id = ?
            """, (
                analysis_meta.error_type,
                analysis_meta.severity,
                analysis_meta.confidence_score,
                analysis_meta.decision,
                analysis_meta.decision_reason,
                analysis_meta.recommended_human_action or "None",
                incident_id
            ))

            conn.commit()

    async def update_incident_status(
        self,
        incident_id: int,
        status: str,
        mr_id: str = None,
        mr_url: str = None
    ):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE incidents
                SET
                    status = ?,
                    mr_id = ?,
                    mr_url = ?
                WHERE id = ?
            """, (
                status,
                mr_id,
                mr_url,
                incident_id
            ))

            conn.commit()

    def get_run_metrics(self) -> Dict[str, Any]:
        """
        Aísla los conteos de la corrida actual pero expone
        el inventario total de MRs pendientes.
        """

        with sqlite3.connect(self.db_path) as conn:

            cursor = conn.cursor()

            t_raw = cursor.execute(
                """
                SELECT COUNT(*)
                FROM incidents
                WHERE execution_id = ?
                """,
                (self.execution_id,)
            ).fetchone()

            af_raw = cursor.execute(
                """
                SELECT COUNT(*)
                FROM incidents
                WHERE execution_id = ?
                  AND decision = 'AUTO_FIX'
                """,
                (self.execution_id,)
            ).fetchone()

            el_raw = cursor.execute(
                """
                SELECT COUNT(*)
                FROM incidents
                WHERE execution_id = ?
                AND decision = 'ESCALATE_LLM'
                """,
                (self.execution_id,)
            ).fetchone()

            eh_raw = cursor.execute(
                """
                SELECT COUNT(*)
                FROM incidents
                WHERE execution_id = ?
                AND decision = 'ESCALATE_HUMAN'
                """,
                (self.execution_id,)
            ).fetchone()

            total = t_raw[0] if t_raw else 0
            auto_fix = af_raw[0] if af_raw else 0
            escalate_llm = el_raw[0] if el_raw else 0
            escalate_human = eh_raw[0] if eh_raw else 0

            conn.row_factory = sqlite3.Row
            cursor_mrs = conn.cursor()

            mrs = cursor_mrs.execute("""
                SELECT
                    mr_id,
                    mr_url,
                    error_type
                FROM incidents
                WHERE status = 'WAITING_APPROVAL'
            """).fetchall()

            blocked = cursor_mrs.execute("""
                SELECT
                    pipeline_id,
                    reason
                FROM incidents
                WHERE status = 'BLOCKED'
            """).fetchall()

            return {
                "total": total,
                "auto_fix": auto_fix,
                "escalate_llm": escalate_llm,
                "escalate_human": escalate_human,
                "mrs": [dict(row) for row in mrs],
                "blocked": [dict(row) for row in blocked]
            }

