import os
import json
import sqlite3
import logging
from datetime import datetime
from typing import Dict, Any
from schemas.contracts import AuditReport

logger = logging.getLogger("AuditEngine")

class AuditEngine:
    def __init__(self, db_path: str = "config/sre_audit.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        os.makedirs("config/reports", exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Inicializa de forma determinística la tabla de auditoría relacional."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS executions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    status TEXT NOT NULL,
                    test_case TEXT NOT NULL,
                    error_type TEXT,
                    decision TEXT,
                    confidence REAL,
                    raw_report TEXT NOT NULL
                )
            """)
            conn.commit()

    async def log_execution(self, mode: str, test_case: str, status: str, analysis_meta: Dict[str, Any], checks_meta: Dict[str, bool]) -> str:
        """Persiste la evidencia de ejecución en SQLite y genera el artefacto JSON físico."""
        timestamp = datetime.now().isoformat()
        
        # Mapeo estructurado idéntico a tu especificación de caso de uso
        decision = analysis_meta.get("decision", "ESCALATE_HUMAN")
        supervisor_action = "APPROVE_MR" if decision == "AUTO_FIX" else ("ESCALATE_HUMAN" if decision == "ESCALATE_HUMAN" else "NONE")
        
        report = AuditReport(
            timestamp=timestamp,
            execution_mode=mode.upper(),
            status=status,
            test_case=test_case,
            checks=checks_meta,
            pipeline={
                "status": "failed" if status != "SUCCESS" else "stable",
                "error": analysis_meta.get("error_type", "Unknown")
            },
            resolution={
                "decision": decision,
                "confidence": analysis_meta.get("confidence_score", 0.0),
                "mr_created": analysis_meta.get("auto_fix", False)
            },
            supervisor_action=supervisor_action
        )

        # 1. Persistencia en SQLite
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO executions (timestamp, mode, status, test_case, error_type, decision, confidence, raw_report)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    timestamp, mode, status, test_case, 
                    report.pipeline["error"], report.resolution["decision"], 
                    report.resolution["confidence"], report.model_dump_json()
                ))
                conn.commit()
                report.execution_id = cursor.lastrowid
        except Exception as e:
            logger.error(f"[-] Error guardando trazabilidad en SQLite: {e}")

        # 2. Persistencia en JSON Físico (Artefacto de respaldo para auditorías rápidas)
        report_filename = f"config/reports/demo_report.json" if mode.lower() == "demo" else f"config/reports/report_{timestamp.replace(':', '-')}.json"
        try:
            with open(report_filename, "w") as f:
                json.dump(report.model_dump(), f, indent=2)
            logger.info(f"[✔] Evidencia de auditoría respaldada en: {report_filename}")
        except Exception as e:
            logger.error(f"[-] Error escribiendo JSON de respaldo: {e}")

        return report_filename
