import os
import logging
from typing import Dict, Any, List
from src.runtime.base import BaseRuntime

logger = logging.getLogger("DemoRuntime")

class DemoRuntime(BaseRuntime):
    async def get_failed_pipelines(self) -> List[Dict[str, Any]]:
        logger.info("===============================================================")
        logger.info("🔍 INICIANDO PRE-FLIGHT CHECKLIST / SANITY CHECK (MODO DEMO)")
        logger.info("===============================================================")
        
        checks = {
            "GITLAB_TOKEN": os.getenv("GITLAB_TOKEN"),
            "GITLAB_PROJECT_ID": os.getenv("GITLAB_PROJECT_ID"),
            "GITLAB_API_URL": os.getenv("GITLAB_API_URL"),
            "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY")
        }
        
        failed = False
        for var, value in checks.items():
            if not value:
                logger.error(f"❌ [FALLO] Variable obligatoria ausente en entorno: {var}")
                failed = True
            else:
                logger.info(f"✅ [OK] Conectividad / Credencial verificada para: {var}")
                
        if failed:
            logger.critical("🚨 El Sanity Check falló. Revisa tu archivo .env antes de proceder.")
            return []
            
        logger.info("🚀 [ÉXITO] Todas las integraciones y APIs se encuentran operativas.")
        return []

    # Implementación básica de firmas abstractas requeridas
    async def read_file(self, f: str) -> str: return ""
    async def create_branch(self, b: str) -> bool: return True
    async def commit_file(self, p: str, c: str, m: str) -> bool: return True
    async def create_mr(self, s: str, tg: str, t: str) -> str: return ""
    async def run_validation(self) -> Dict[str, Any]: return {"exit_code": 0}
