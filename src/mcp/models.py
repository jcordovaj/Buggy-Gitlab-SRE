from pydantic import BaseModel
from typing import Dict, Any, Optional

class ToolResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# Excepciones controladas requeridas por la especificación
class ToolExecutionError(Exception):
    """Fallo en la ejecución interna de la herramienta MCP."""
    pass

class GitLabConnectionError(Exception):
    """Fallo de comunicación con la API de GitLab."""
    pass

class ValidationError(Exception):
    """Los parámetros de entrada o resultados violan los contratos de datos."""
    pass
