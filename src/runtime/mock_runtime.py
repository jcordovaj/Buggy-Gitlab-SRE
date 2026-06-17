import json
import logging
from typing import Dict, Any, List
from src.runtime.base import BaseRuntime

logger = logging.getLogger("MockRuntime")

class MockRuntime(BaseRuntime):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

    async def get_failed_pipelines(self) -> List[Dict[str, Any]]:
        base_path = "config/fixtures"
        
        # Mapeo unificado de los 6 casos de prueba del Hackathon
        test_cases = {
            "syntax_error": {
                "file": "syntax_error.log", "pipeline_id": "991",
                "failed_job_name": "linter_checks", "error_type": "SYNTAX", "loader": "text"
            },
            "missing_dependencies": { 
                "file": "missing_dependencies.log", "pipeline_id": "992",
                "failed_job_name": "pip_install", "error_type": "TEST_FAILURE", "loader": "text"
            },
            "vuln": {
                "file": "vulnerability.json", "pipeline_id": "993",
                "failed_job_name": "security_scan", "error_type": "VULN", "loader": "json"
            },
            "permission_denied": {
                "file": "human_intervention.json", "pipeline_id": "994",
                "failed_job_name": "db_migrations", "error_type": "PERMISSION_DENIED", "loader": "nested_json"
            },
            "timeout": {
                "file": "timeout.json", "pipeline_id": "995",
                "failed_job_name": "integration_tests", "error_type": "TIMEOUT", "loader": "nested_json"
            },
            "unknown_error": {
                "file": "unknown_error.json", "pipeline_id": "996",
                "failed_job_name": "build_assets", "error_type": "UNKNOWN_ERROR", "loader": "nested_json"
            }
        }

        if self.test_case not in test_cases:
            logger.warning(f"[-] Caso de prueba no registrado en el mock: '{self.test_case}'")
            return []

        cfg = test_cases[self.test_case]
        file_path = f"{base_path}/{cfg['file']}"

        try:
            with open(file_path, "r") as f:
                if cfg["loader"] == "json":
                    content = json.dumps(json.load(f), indent=2)
                elif cfg["loader"] == "nested_json":
                    infra_data = json.load(f)
                    content = infra_data.get("error_log_snippet", "")
                else:
                    content = f.read()

            return [{
                "pipeline_id": cfg["pipeline_id"],
                "project_id": self.project_id,
                "branch": self.branch,
                "failed_job_name": cfg["failed_job_name"],
                "error_log_snippet": content,
                "error_type": cfg["error_type"],
            }]

        except FileNotFoundError:
            logger.error(f"[-] Archivo fixture crítico ausente: {file_path}")
            return []

    async def read_file(self, file_path: str) -> str:
        if self.test_case == "syntax_error": return "def login(user)\n    print(user)"
        if self.test_case == "missing_dependencies": return "import httpx"
        return "# Mock de archivo para análisis"

    async def create_branch(self, branch_name: str) -> bool: return True
    async def commit_file(self, file_path: str, content: str, commit_msg: str) -> bool: return True
    async def create_mr(self, source_branch: str, target_branch: str, title: str) -> str: return "https://gitlab.mock"
    async def run_validation(self) -> Dict[str, Any]: return {"exit_code": 0}
