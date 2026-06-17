import logging
from typing import Dict, Any, Optional
from src.mcp.server import EmbeddedMCPServer
from src.mcp.models import ToolResponse

logger = logging.getLogger("MCPClient")

class MCPClient:
    def __init__(self, server: EmbeddedMCPServer):
        self.server = server
        logger.debug("[MCP Client] Conectado exitosamente al canal del Servidor Embebido.")

    async def call_tool(self, tool_name: str, params: Optional[Dict[str, Any]] = None) -> ToolResponse:
        parameters = params or {}
        logger.debug(f"[MCP Client] Invocando herramienta remota: '{tool_name}' con parámetros: {parameters}")
        
        response = await self.server.execute_tool(tool_name, parameters)
        
        if not response.success:
            logger.warning(f"[MCP Client] Herramienta '{tool_name}' reportó un fallo: {response.error}")
        return response

