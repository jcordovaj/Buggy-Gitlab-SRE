import logging
from typing import Dict, Any, Optional
from src.runtime.base import BaseRuntime
from src.mcp.models import ToolResponse

logger = logging.getLogger("MCPServer")

class EmbeddedMCPServer:
    # Usamos anotación por string para romper cualquier acoplamiento con carpetas de runtimes
    def __init__(self, runtime: "BaseRuntime"):
        self.runtime = runtime
        logger.debug("[MCP Server] Inicializado correctamente con Runtime inyectado.")

    async def execute_tool(self, tool_name: str, params: Dict[str, Any]) -> ToolResponse:
        method_name = f"_{tool_name}"
        method = getattr(self, method_name, None)
        
        if not method:
            return ToolResponse(
                success=False, 
                error=f"La herramienta MCP '{tool_name}' no está registrada en el servidor."
            )
        
        try:
            return await method(params)
        except Exception as e:
            logger.error(f"[MCP Server] Error ejecutando {tool_name}: {str(e)}")
            return ToolResponse(success=False, error=str(e))

    # --- ENRUTAMIENTO DIRECTO ASÍNCRONO ---

    async def _get_failed_pipelines(self, params: Dict[str, Any]) -> ToolResponse:
        pipelines = await self.runtime.get_failed_pipelines()
        return ToolResponse(success=True, data={"pipelines": pipelines, "count": len(pipelines)})

    async def _read_repository_file(self, params: Dict[str, Any]) -> ToolResponse:
        file_path = params.get("file_path")
        if not file_path:
            return ToolResponse(success=False, error="Parámetro 'file_path' obligatorio.")
        content = await self.runtime.read_file(file_path)
        return ToolResponse(success=True, data={"file_path": file_path, "content": content, "encoding": "utf-8"})

    async def _create_branch(self, params: Dict[str, Any]) -> ToolResponse:
        branch_name = params.get("branch_name")
        if not branch_name:
            return ToolResponse(success=False, error="Parámetro 'branch_name' obligatorio.")
        success = await self.runtime.create_branch(branch_name)
        return ToolResponse(success=success)

    async def _commit_changes(self, params: Dict[str, Any]) -> ToolResponse:
        success = await self.runtime.commit_file(
            file_path=params.get("file_path", ""),
            content=params.get("content", ""),
            commit_msg=params.get("message", "fix: automated mcp patch")
        )
        return ToolResponse(success=success)

    async def _create_merge_request(self, params: Dict[str, Any]) -> ToolResponse:
        mr_url = await self.runtime.create_mr(
            source_branch=params.get("source_branch", ""),
            target_branch=params.get("target_branch", "main"),
            title=params.get("title", "Automated Fix")
        )
        return ToolResponse(success=True, data={"merge_request_url": mr_url})

    async def _run_validation(self, params: Dict[str, Any]) -> ToolResponse:
        res = await self.runtime.run_validation()
        return ToolResponse(success=True, data={
            "passed": res.get("exit_code") == 0,
            "exit_code": res.get("exit_code", 1),
            "logs": res.get("logs", "Validación ejecutada de forma determinística.")
        })
