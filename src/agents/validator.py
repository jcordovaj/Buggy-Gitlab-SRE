import logging
from src.mcp.client import MCPClient
from schemas.contracts import ValidationResult

logger = logging.getLogger("ValidatorAgent")

class ValidatorAgent:
    def __init__(self, mcp_client: MCPClient):
        self.mcp = mcp_client

    async def validate(self) -> ValidationResult:
        logger.info("[*] Ejecutando suite de validación pre-Merge Request vía MCP...")
        # Cambiado a call_tool siguiendo el contrato unificado
        response = await self.mcp.call_tool("run_validation")
        
        if not response.success:
            return ValidationResult(is_valid=False, feedback=f"Fallo de infraestructura: {response.error}", exit_code=1)
            
        data = response.data or {}
        return ValidationResult(
            is_valid=data.get("passed", False),
            feedback=data.get("logs", ""),
            exit_code=data.get("exit_code", 0)
        )
