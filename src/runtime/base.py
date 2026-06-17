import abc
from typing import Dict, Any, List

class BaseRuntime(abc.ABC):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.mode = config.get("mode", "mock")
        self.test_case = config.get("test_case", "syntax_error")
        
        # Mapeo seguro del JSON unificado
        repo_data = config.get("repository", {})
        self.project_id = str(config.get("project_id", "82290691"))
        self.branch = config.get("source_branch", "main")

        # INYECCIÓN CORREGIDA: Importaciones tardías usando las rutas exactas del disco
        from src.mcp.server import EmbeddedMCPServer
        from src.mcp.client import MCPClient
        
        # El Runtime autogenera su propia tubería de comunicación MCP
        self.mcp_server = EmbeddedMCPServer(self)
        self.mcp_client = MCPClient(self.mcp_server)

    @abc.abstractmethod
    async def get_failed_pipelines(self) -> List[Dict[str, Any]]: pass

    @abc.abstractmethod
    async def read_file(self, file_path: str) -> str: pass

    @abc.abstractmethod
    async def create_branch(self, branch_name: str) -> bool: pass

    @abc.abstractmethod
    async def commit_file(self, file_path: str, content: str, commit_msg: str) -> bool: pass

    @abc.abstractmethod
    async def create_mr(self, source_branch: str, target_branch: str, title: str) -> str: pass

    @abc.abstractmethod
    async def run_validation(self) -> Dict[str, Any]: pass

