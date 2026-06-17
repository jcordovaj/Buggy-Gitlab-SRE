from typing import Dict, Any, Type
from src.runtime.base import BaseRuntime
from src.runtime.mock_runtime import MockRuntime
from src.runtime.repo_runtime import DemoRuntime, RepoRuntime

class RuntimeFactory:
    _registry: Dict[str, Type[BaseRuntime]] = {
        "mock": MockRuntime,
        "demo": DemoRuntime,
        "repo": RepoRuntime
    }

    @classmethod
    def create(cls, config: Dict[str, Any]) -> BaseRuntime:
        mode = config.get("mode", "mock").lower()
        runtime_class = cls._registry.get(mode)
        
        if not runtime_class:
            raise ValueError(f"[-] Modo de ejecución no soportado en la factoría: {mode}")
            
        # Permitimos la instanciación de DemoRuntime para correr el Sanity Checklist
        if runtime_class == RepoRuntime:
            raise NotImplementedError(f"[-] El modo 'REPO' está mapeado pero requiere inyectar la librería de GitLab.")
            
        return runtime_class(config)
