import logging
from src.mcp.client import MCPClient
from schemas.contracts import AnalysisResult

logger = logging.getLogger("DeveloperAgent")

class DeveloperAgent:
    def __init__(self, mcp_client: MCPClient):
        self.mcp = mcp_client

    async def apply_fix(self, analysis: AnalysisResult) -> bool:
        logger.info("[*] Creando rama de parche automatizada vía canal MCP...")
        # Consumo correcto usando call_tool pasando los parámetros estructurados
        await self.mcp.call_tool("create_branch", {"branch_name": "fix/automated-sre-patch"})
        
        logger.info(f"[*] Aplicando parche de código en el archivo: '{analysis.file_to_modify}'...")
        await self.mcp.call_tool("commit_changes", {
            "file_path": analysis.file_to_modify,
            "content": analysis.code_patch,
            "message": f"fix: {analysis.proposed_fix_description}"
        })
        return True

