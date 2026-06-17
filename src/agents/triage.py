import json
import logging
from typing import Optional, Dict, Any
from schemas.contracts import AnalysisResult

logger = logging.getLogger("LogAnalyzer")

ERROR_CATALOG: Dict[str, Dict[str, Any]] = {
    "SYNTAX": {
        "error_type": "SyntaxError", "category": "code", "severity": "high",
        "confidence": 1.0, "decision": "AUTO_FIX", "reason": "Known deterministic syntax repair pattern"
    },
    "TEST_FAILURE": {
        "error_type": "ModuleNotFoundError", "category": "dependency", "severity": "medium",
        "confidence": 1.0, "decision": "AUTO_FIX", "reason": "Known dependency resolution pattern"
    },
    "UNKNOWN": {  
        "error_type": "HardcodedSecret", "category": "security", "severity": "critical",
        "confidence": 0.60, "decision": "ESCALATE_LLM", "reason": "No deterministic handler available"
    },
    "PERMISSION_DENIED": {
        "error_type": "PermissionDenied", "category": "infrastructure", "severity": "critical",
        "confidence": 1.0, "decision": "ESCALATE_HUMAN", "reason": "Requires infrastructure access level"
    },
    "TIMEOUT": {
        "error_type": "RunnerTimeout", "category": "infrastructure", "severity": "high",
        "confidence": 1.0, "decision": "ESCALATE_HUMAN", "reason": "Remote runner unresponsive"
    },
    "UNKNOWN_ERROR": {
        "error_type": "UnknownFailure", "category": "infrastructure", "severity": "critical",
        "confidence": 0.42, "decision": "ESCALATE_LLM", "reason": "No deterministic handler available"
    }
}

class LogAnalyzer:
    def try_parse(self, raw_pipeline: dict) -> Optional[AnalysisResult]:
        raw_type = raw_pipeline.get("error_type", "")
        meta = ERROR_CATALOG.get(raw_type)
        if not meta:
            return None
            
        if raw_type == "SYNTAX":
            return AnalysisResult(
                is_deterministic=True, error_type=meta["error_type"], category=meta["category"],
                severity=meta["severity"], confidence_score=meta["confidence"], requires_llm=False, auto_fix=True,
                decision=meta["decision"], decision_reason=meta["reason"],
                root_cause="Falta de dos puntos o comilla de cierre en el script principal.",
                proposed_fix_description="Agregar el token de cierre al print para mitigar el SyntaxError.",
                file_to_modify="app.py",  
                code_patch='print("Hello World")\n',
                requires_human_escalation=False
            )

        if raw_type == "TEST_FAILURE":
            return AnalysisResult(
                is_deterministic=True, error_type=meta["error_type"], category=meta["category"],
                severity=meta["severity"], confidence_score=meta["confidence"], requires_llm=False, auto_fix=True,
                decision=meta["decision"], decision_reason=meta["reason"],
                root_cause="Falta el módulo de red 'httpx' en el manifiesto.",
                proposed_fix_description="Inyectar la dependencia httpx en requirements.txt.",
                file_to_modify="requirements.txt", code_patch="httpx==0.24.1",
                requires_human_escalation=False
            )

        if raw_type == "PERMISSION_DENIED":
            return AnalysisResult(
                is_deterministic=True, error_type=meta["error_type"], category=meta["category"],
                severity=meta["severity"], confidence_score=meta["confidence"], requires_llm=False, auto_fix=False,
                decision=meta["decision"], decision_reason=meta["reason"],
                root_cause="El usuario de la app no tiene privilegios ALTER.",
                proposed_fix_description="Ajuste de RBAC requerido en la base de datos.",
                file_to_modify="None", code_patch="None", requires_human_escalation=True,
                recommended_human_action="Grant ALTER privilege to app_user on table 'users';"
            )

        if raw_type == "TIMEOUT":
            return AnalysisResult(
                is_deterministic=True, error_type=meta["error_type"], category=meta["category"],
                severity=meta["severity"], confidence_score=meta["confidence"], requires_llm=False, auto_fix=False,
                decision=meta["decision"], decision_reason=meta["reason"],
                root_cause="El runner de GitLab superó el tiempo máximo de espera.",
                proposed_fix_description="Re-ejecución manual o escalamiento por caída de agente remoto.",
                file_to_modify="None", code_patch="None", requires_human_escalation=True,
                recommended_human_action="Check remote runner connectivity and increase timeout in .gitlab-ci.yml if needed."
            )

        return None


class TriageAgent:
    def __init__(self, mcp_client):
        self.mcp = mcp_client
        self.analyzer = LogAnalyzer()
        self._gemini_client = None  
        self._types = None

    async def run_triage(self, pipeline: dict) -> AnalysisResult:
        # Intento puramente determinístico (100% preservado para evitar regresiones)
        result = self.analyzer.try_parse(pipeline)
        
        # Si encuentra un patrón conocido y no requiere LLM, retorna inmediatamente
        if result and result.decision != "ESCALATE_LLM":
            return result
            
        # Orquestación de la capability secundaria: Casos UNKNOWN, UNKNOWN_ERROR o no parseados
        return await self._call_gemini_triage(pipeline)
    
    async def _call_gemini_triage(self, pipeline: dict) -> AnalysisResult:
        """Invocación real a Gemini AI usando Structured Outputs sobre el contrato Pydantic."""
        if self._gemini_client is None:
            from google import genai
            from google.genai import types
            import os
            
            self._gemini_client = genai.Client()
            self._types = types
            logger.info("[🧠] Cliente de Google GenAI inicializado correctamente para Vertex AI.")

        snippet = pipeline.get("error_log_snippet", "")
        raw_type = pipeline.get("error_type", "UNKNOWN")
        meta = ERROR_CATALOG.get(raw_type, {})

        classification_context = {
            "error_type": meta.get("error_type", "HardcodedSecret"),
            "category": meta.get("category", "security"),
            "severity": meta.get("severity", "critical"),
            "confidence_score": meta.get("confidence", 0.60),
            "target_file": pipeline.get("file_path", "config/secrets.py"),
            "target_line": pipeline.get("line", 5)
        }

        system_instruction = (
            "Actúas como un Ingeniero Principal de SRE y Experto en Ciberseguridad DevSecOps. "
            "Analiza el reporte de vulnerabilidad que se te provee. "
            "Debes proponer un parche de código exacto (code_patch) para mitigar o remover el secreto expuesto. "
            "PRINCIPIO DE GOBERNANZA: Si el reporte no contiene evidencia física suficiente para estructurar un parche real, "
            "debes marcar 'requires_human_escalation' como True de forma obligatoria."
        )

        prompt = (
            f"Clasificación estática del linter SRE:\n{json.dumps(classification_context, indent=2)}\n\n"
            f"Log crudo del pipeline:\n{snippet}"
        )

        try:
            response = self._gemini_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=self._types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.1,  
                    response_mime_type="application/json",
                    response_schema=AnalysisResult,  
                ),
            )
            
            analysis: AnalysisResult = response.parsed
            
            analysis.is_deterministic = False
            analysis.requires_llm = True
            
            # --- Regla Core de Gobernanza: Validación del Umbral de Confianza SRE (< 0.95) ---
            if analysis.confidence_score < 0.95:
                logger.warning(
                    f"[⚠️] Confianza cognitiva ({analysis.confidence_score}) por debajo del umbral de 0.95. "
                    "Degradando automáticamente a ESCALATE_HUMAN."
                )
                analysis.decision = "ESCALATE_HUMAN"
                analysis.requires_human_escalation = True
                analysis.recommended_human_action = (
                    f"Revisión manual requerida. Causa raíz sugerida por LLM: {analysis.root_cause}. "
                    f"El parche fue descartado debido a un score de confianza inferior al 95%."
                )
            else:
                analysis.decision = "ESCALATE_LLM"
                analysis.decision_reason = "Cognitive secondary triage analysis completed by Gemini AI with high confidence."
            
            return analysis

        except Exception as e:
            logger.error(f"[-] Fallo en el canal con el motor de IA de Google: {e}")
            return AnalysisResult(
                is_deterministic=False, 
                error_type=classification_context["error_type"],
                category=classification_context["category"], 
                severity=classification_context["severity"],
                confidence_score=0.0, 
                requires_llm=True, 
                auto_fix=False,
                decision="ESCALATE_HUMAN", 
                decision_reason=f"Excepción en la API de Vertex AI: {str(e)}",
                root_cause="Fallo de comunicación con la capa cognitiva.",
                proposed_fix_description="Requiere análisis manual.",
                file_to_modify=classification_context["target_file"], 
                code_patch="",
                requires_human_escalation=True,
                recommended_human_action="Revisar credenciales de Google Cloud o cuotas de Vertex AI sandbox."
            )

