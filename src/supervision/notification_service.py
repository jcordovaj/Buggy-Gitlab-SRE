import logging
from typing import Dict, Any, List
from dataclasses import dataclass

logger = logging.getLogger("NotificationService")

@dataclass(frozen=True)
class ExecutionSummaryDTO:
    """DTO para aislar los datos relacionales de SQLite de la capa de renderizado."""
    pipelines_scanned: int
    failed_jobs: int
    incidents_created: int
    remediations_executed: int
    merge_requests_created: int
    mrs_waiting: List[Dict[str, Any]]
    blocked_incidents: List[Dict[str, Any]]
    execution_id: str
    audit_db_path: str

class NotificationService:
    def __init__(self, registry: Any):
        self.registry = registry

    async def generate_execution_summary(self) -> str:
        """
        Genera y despliega el balance consolidado consumiendo un DTO limpio.
        Garantiza visibilidad al Supervisor si hay elementos pendientes en la flota.
        """
        metrics = self.registry.get_run_metrics()
        
        # Construcción explícita del DTO mapeando los datos crudos de la base de datos
        dto = ExecutionSummaryDTO(
            pipelines_scanned=metrics["total"],
            failed_jobs=metrics["total"],
            incidents_created=metrics["total"],
            remediations_executed=metrics["auto_fix"],
            merge_requests_created=len(metrics["mrs"]),
            mrs_waiting=metrics["mrs"],
            blocked_incidents=metrics["blocked"],
            execution_id=str(self.registry.execution_id),
            audit_db_path=str(self.registry.db_path)
        )
        
        # Condición de Gobernanza optimizada con el DTO: solo omitimos si no hay actividad ni pendientes
        if dto.pipelines_scanned == 0 and not dto.mrs_waiting and not dto.blocked_incidents:
            return ""

        summary = []
        summary.append("\n===================================================\n")
        summary.append("         MCP-GITLAB-SRE EXECUTION SUMMARY          ")
        summary.append(f"\n Execution ID: {dto.execution_id}\n")
        summary.append("===================================================\n")
        summary.append(" GitLab objects scanned:\n")
        summary.append(f"  - Pipelines                  : {dto.pipelines_scanned}\n")
        summary.append(f"  - Failed jobs                : {dto.failed_jobs}\n")
        summary.append(f"  - Incidents created          : {dto.incidents_created}\n")
        summary.append(f"  - Remediations executed      : {dto.remediations_executed}\n")
        summary.append(f"  - Merge Requests created     : {dto.merge_requests_created}\n")
        summary.append("---------------------------------------------------\n")
        
        if dto.mrs_waiting:
            summary.append(" Waiting supervisor approval:\n")
            for mr in dto.mrs_waiting:
                summary.append(f"  ✓ MR !{mr['mr_id']} ({mr['error_type']}) -> {mr['mr_url']}\n")
            summary.append("---------------------------------------------------\n")
            
        if dto.blocked_incidents:
            summary.append(" Human intervention required:\n")
            for block in dto.blocked_incidents:
                summary.append(f"  ❌ Pipeline ID {block['pipeline_id']} -> REASON: {block['reason']}\n")
            summary.append("---------------------------------------------------\n")

        summary.append(f" Audit database log            : {dto.audit_db_path}\n")
        summary.append("===================================================\n")
        
        summary_str = "".join(summary)
        print(summary_str)
        return summary_str

    async def send_supervisor_alert(self, incident_id: int, status: str, details: Dict[str, Any]):
        if status == "WAITING_APPROVAL":
            logger.info(f"📬 [NOTIFICACIÓN] Registro #{incident_id}: Acción requerida -> Aprobar Merge Request en GitLab.")
        elif status == "BLOCKED":
            logger.warning(f"📯 [ALERTA] Registro #{incident_id}: Intervención humana obligatoria en infraestructura.")

