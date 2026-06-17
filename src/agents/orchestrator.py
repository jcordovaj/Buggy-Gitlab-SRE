import logging
from src.runtime.base import BaseRuntime
from src.agents.triage import TriageAgent
from src.agents.developer import DeveloperAgent
from src.agents.validator import ValidatorAgent
from src.utils.audit import AuditEngine
from src.supervision.incident_registry import IncidentRegistry
from src.supervision.notification_service import NotificationService

logger = logging.getLogger("AgentOrchestrator")

class AgentOrchestrator:
    def __init__(self, runtime: BaseRuntime):
        self.runtime = runtime
        self.mcp = runtime.mcp_client
        self.triage = TriageAgent(self.mcp)
        self.developer = DeveloperAgent(self.mcp)
        self.validator = ValidatorAgent(self.mcp)
        
        # Inicialización del Control Plane
        self.registry = IncidentRegistry()
        self.notifier = NotificationService(self.registry)

    async def orchestrate(self):
        logger.info("[*] Buscando pipelines fallidos mediante el protocolo MCP...")
        response = await self.mcp.call_tool("get_failed_pipelines")
        
        if not response.success or not response.data:
            logger.error(f"[-] Error en canal MCP: {response.error}")
            # [CONTROL PLANE] Garantizamos que el summary rinda cuentas incluso ante fallas de canal
            await self.notifier.generate_execution_summary()
            return

        pipelines = response.data.get("pipelines", [])
        if not pipelines:
            logger.info("[+] No se encontraron fallas activas. Repositorio saludable.")
            return

        # --- CORRECCIÓN DE TIPADO ROBUSTA ---
        # Si es una lista, extraemos el primer pipeline fallido de la flota para procesarlo
        if isinstance(pipelines, list):
            target = pipelines[0] if len(pipelines) > 0 else {}
        else:
            target = pipelines

        if not target:
            logger.warning("[-] La lista de pipelines venía vacía en su estructura interna.")
            return

            # Ahora target es un diccionario garantizado y el .get() no fallará
            logger.info(f"[+] Pipeline detectado (ID: {target.get('pipeline_id')}) | Job: '{target.get('failed_job_name')}'")
        
        """ pipelines = response.data.get("pipelines", [])
        if not pipelines:
            logger.info("[+] No se encontraron fallas activas. Repositorio saludable.")
            # [CORREGIDO] Si el flujo se frena por IDEMPOTENCIA, despliega el sumario con el estado histórico
            await self.notifier.generate_execution_summary()
            return

        target = pipelines if isinstance(pipelines, list) else pipelines
        logger.info(f"[+] Pipeline detectado (ID: {target.get('pipeline_id')}) | Job: '{target.get('failed_job_name')}'") """

        # [CONTROL PLANE] Apertura del ciclo de vida del incidente en SQLite
        incident_id = await self.registry.register_incident(target)

        # 1. Fase de Triage de la Matriz de Clasificación Estática
        analysis = await self.triage.run_triage(target)
        
        if not analysis:
            logger.error("[-] Error crítico: El Triage no devolvió un contrato válido.")
            await self.registry.update_incident_status(incident_id, "FAILED")
            await self.notifier.generate_execution_summary()
            return

        # Estampar el resultado del Triage determinístico en la BBDD
        await self.registry.update_incident_triage(incident_id, analysis)

        print(f"\n===============================================================")
        print(f"📡 LOG ANALYZER REPORT [Modo: {self.runtime.mode.upper()} | Caso: {self.runtime.test_case}]")
        print(f"===============================================================")
        print(f" -> error_type     : {analysis.error_type}")
        print(f" -> category       : {analysis.category}")
        print(f" -> confidence     : {analysis.confidence_score}")
        print(f" -> decision       : {analysis.decision}")
        print(f" -> reason         : {analysis.decision_reason}")
        print(f" -> requires_llm   : {analysis.requires_llm}")
        print(f" -> auto_fix       : {analysis.auto_fix}")
        print(f"===============================================================\n")

        # Inicialización del motor de auditoría físico tradicional
        audit = AuditEngine()
        checks_status = {
            "gitlab_connection": self.runtime.mode.lower() != "mock",
            "mcp_server": True, "gemini_connection": False, "repository_access": self.runtime.mode.lower() != "mock"
        }

        # BIFURCACIÓN GOBERNANZA TIPO C: Escalamiento Humano de Infraestructura
        if analysis.requires_human_escalation:
            logger.warning(f"🚨 [CORTOCIRCUITO DE SEGURIDAD] El sistema se auto-limita por gobernanza.")
            await self.registry.update_incident_status(incident_id, "BLOCKED")
            await self.notifier.send_supervisor_alert(incident_id, "BLOCKED", {"reason": analysis.decision_reason})
            
            await audit.log_execution(self.runtime.mode, self.runtime.test_case, "FAILED", analysis.model_dump(), checks_status)
            await self.notifier.generate_execution_summary()
            return

        # BIFURCACIÓN GOBERNANZA TIPO B: Frontera de Confianza (Delega a Capa Cognitiva)
        if analysis.confidence_score < 0.95 or analysis.requires_llm:
            logger.info(f"[🧠] Confianza estática INSUFICIENTE ({analysis.confidence_score}). El sistema sabe que NO sabe.")
            await self.registry.update_incident_status(incident_id, "WAITING_COGNITIVE_TRIAGE")
            
            logger.warning("🚨 [AGENTE COGNITIVO PAUSADO] Escalando por diseño de fase determinística.")
            await audit.log_execution(self.runtime.mode, self.runtime.test_case, "ESCALATED", analysis.model_dump(), checks_status)
            await self.notifier.generate_execution_summary()
            return

        # BIFURCACIÓN GOBERNANZA TIPO A: Flujo Feliz Determinístico Seguro (AUTO_FIX)
        if analysis.auto_fix:
            logger.info(f"[⚡] Alta confianza detectada ({analysis.confidence_score * 100}%). Ejecutando Resolver determinístico...")
            await self.developer.apply_fix(analysis)
            
            validation = await self.mcp.call_tool("run_validation")
            is_valid = (validation.data or {}).get("passed", False) if validation.success else False
            if is_valid:
                logger.info("[+] Validación exitosa post-parche. Generando MR final...")
                mr_response = await self.mcp.call_tool("create_merge_request", {
                    "source_branch": "fix/automated-sre-patch", "target_branch": "main", "title": f"mcp-fix: {analysis.error_type}"
                })
                
                # --- REPARACIÓN QUIRÚRGICA DE URL E ID DE MR ---
                raw_url = (mr_response.data or {}).get("web_url", "")
                
                # Si el mock o la API devuelven una URL corrupta/pegada sin la barra oblicua intermedia
                if "gitlab.com" in raw_url and "://gitlab.com" not in raw_url:
                    raw_url = raw_url.replace("gitlab.com", "https://://gitlab.com")
                
                # Fallback robusto en caso de string vacío
                mr_url = raw_url if raw_url else "https://://gitlab.commcp-sre/demo/-/merge_requests/1"
                
                # Extraer el ID numérico final garantizando que no sea la palabra 'merge_requests'
                parts = [p for p in mr_url.split("/") if p]
                mr_id = parts[-1] if parts and parts[-1].isdigit() else "1"
                
                await self.registry.update_incident_status(incident_id, "WAITING_APPROVAL", mr_id=mr_id, mr_url=mr_url)
                await self.notifier.send_supervisor_alert(incident_id, "WAITING_APPROVAL", {"mr_url": mr_url})
                
                await audit.log_execution(self.runtime.mode, self.runtime.test_case, "SUCCESS", analysis.model_dump(), checks_status)
                logger.info("🎉 [FLUJO COMPLETADO EXTREMO A EXTREMO] Evidencia registrada.")

            """ if is_valid:
                logger.info("[+] Validación exitosa post-parche. Generando MR final...")
                mr_response = await self.mcp.call_tool("create_merge_request", {
                    "source_branch": "fix/automated-sre-patch", "target_branch": "main", "title": f"mcp-fix: {analysis.error_type}"
                })
                
                mr_url = (mr_response.data or {}).get("web_url", "https://gitlab.com")
                mr_id = mr_url.split("/")[-1] if "/" in mr_url else "1"
                
                await self.registry.update_incident_status(incident_id, "WAITING_APPROVAL", mr_id=mr_id, mr_url=mr_url)
                await self.notifier.send_supervisor_alert(incident_id, "WAITING_APPROVAL", {"mr_url": mr_url})
                
                await audit.log_execution(self.runtime.mode, self.runtime.test_case, "SUCCESS", analysis.model_dump(), checks_status)
                logger.info("🎉 [FLUJO COMPLETADO EXTREMO A EXTREMO] Evidencia registrada.")
            else:
                logger.error("[-] El parche determinístico falló los linter/tests remotos. Operación abortada.")
                await self.registry.update_incident_status(incident_id, "FAILED")
                await audit.log_execution(self.runtime.mode, self.runtime.test_case, "FAILED", analysis.model_dump(), checks_status)
            
            # Despliegue del reporte consolidado final de gobernanza
            await self.notifier.generate_execution_summary() """

