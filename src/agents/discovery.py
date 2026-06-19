import logging
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger("RepositoryAnalyzer")

@dataclass(frozen=True)
class RepositoryProfile:
    """DTO Inmutable de Evidencia Arquitectónica (Gobernanza SRE)."""
    project_id: str
    language: str
    framework: str
    build_system: str
    test_runner: str
    ci_file: str
    confidence_score: float
    evidence: List[str]

class RepositoryAnalyzer:
    def __init__(self, mcp_client):
        self.mcp = mcp_client
        self._gemini_client = None
        self._types = None

    async def analyze_repo(self, project_id: str) -> RepositoryProfile:
        """
        Punto de entrada principal: Aplica 'Determinista primero, cognitivo después'
        utilizando la herramienta MCP de listado plano de estructura.
        """
        logger.info(f"[🔍] Iniciando descubrimiento agnóstico para el repositorio ID: {project_id}")
        
        # 1. Consumo de la herramienta MCP de estructura plana
        response = await self.mcp.call_tool("get_repository_structure")
        if not response.success or not response.data:
            logger.error(f"[-] No se pudo obtener la estructura del repositorio vía MCP: {response.error}")
            return self._generate_unknown_profile(project_id, "Fallo en la consulta de estructura MCP.")

        file_list: List[str] = response.data.get("files", [])
        
        # 2. Fase Determinista: Puntuación de Evidencia Física Real
        profile = await self._evaluate_deterministically(project_id, file_list)
        
        # 3. Fallback Cognitivo Acotado: Solo si la evidencia es ambigua (Confidence < 0.95)
        if profile.confidence_score < 0.95:
            logger.warning(f"[🧠] Confianza estática insuficiente ({profile.confidence_score * 100}%). Derivando ambigüedad a Gemini...")
            profile = await self._call_cognitive_resolution(project_id, file_list, profile)

        return profile

    async def _evaluate_deterministically(self, project_id: str, files: List[str]) -> RepositoryProfile:
        """Matriz SRE aditiva basada en la presencia de firmas físicas en el árbol."""
        score = 0.0
        evidence = []
        
        lang = "unknown"
        framework = "unknown"
        build = "unknown"
        runner = "unknown"
        ci = ".gitlab-ci.yml" if ".gitlab-ci.yml" in files else "unknown"

        if ".gitlab-ci.yml" in files:
            score += 0.05
            evidence.append("✓ .gitlab-ci.yml detectado")

        # --- ECOSISTEMA JAVA ---
        if "pom.xml" in files:
            lang, build, runner, score = "java", "maven", "junit", score + 0.90
            evidence.append("✓ pom.xml (Java Maven)")
            if await self._has_dependency_keyword("pom.xml", "spring-boot"):
                framework, score = "spring_boot", score + 0.05
                evidence.append("✓ Dependencia Spring Boot confirmada")
        
        elif "build.gradle" in files or "build.gradle.kts" in files:
            lang, build, runner, score = "java", "gradle", "junit", score + 0.90
            evidence.append("✓ build.gradle (Java Gradle)")

        # --- ECOSISTEMA JAVASCRIPT / TYPESCRIPT ---
        elif "package.json" in files:
            lang, build, runner, score = "javascript", "npm", "jest", score + 0.85
            evidence.append("✓ package.json (Node.js)")
            if "vite.config.js" in files or "vite.config.ts" in files:
                framework, score = "react_vite", score + 0.10
                evidence.append("✓ Configuración Vite (React Frontend)")

        # --- ECOSISTEMA GO ---
        elif "go.mod" in files:
            lang, build, runner, score = "go", "go_modules", "go_test", score + 0.95
            evidence.append("✓ go.mod (Go Lang)")

        # --- ECOSISTEMA PYTHON (Soporta el caso real sin requirements.txt) ---
        elif "requirements.txt" in files or "pyproject.toml" in files or "app.py" in files or "main.py" in files:
            lang = "python"
            runner = "pytest"
            
            if "requirements.txt" in files or "pyproject.toml" in files:
                build = "pip"
                score += 0.85
                evidence.append("✓ Manifiesto de entorno Python encontrado")
                
                target_file = "pyproject.toml" if "pyproject.toml" in files else "requirements.txt"
                if await self._has_dependency_keyword(target_file, "flask"):
                    framework, score = "flask", score + 0.10
                    evidence.append("✓ Firma de framework Flask detectada")
                elif await self._has_dependency_keyword(target_file, "fastapi"):
                    framework, score = "fastapi", score + 0.10
                    evidence.append("✓ Firma de framework FastAPI detectada")
            else:
                build = "unknown"
                score += 0.40  # Evidencia parcial de soporte (No tiene requirements.txt)
                evidence.append("⚠️ requirements.txt ausente en la raíz")

            if "app.py" in files or "main.py" in files:
                score += 0.15
                evidence.append(f"✓ Archivo ejecutable detectado: {'app.py' if 'app.py' in files else 'main.py'}")

        return RepositoryProfile(
            project_id=project_id,
            language=lang,
            framework=framework,
            build_system=build,
            test_runner=runner,
            ci_file=ci,
            confidence_score=min(score, 1.0),
            evidence=evidence
        )

    async def _has_dependency_keyword(self, file_path: str, keyword: str) -> bool:
        """Lectura dirigida ultra-acotada mediante MCP para buscar palabras clave."""
        response = await self.mcp.call_tool("read_file", {"file_path": file_path})
        if response.success and response.data:
            content = response.data.get("content", "").lower()
            return keyword.lower() in content
        return False

    def _generate_unknown_profile(self, project_id: str, reason: str) -> RepositoryProfile:
        return RepositoryProfile(
            project_id=project_id, language="unknown", framework="unknown", 
            build_system="unknown", test_runner="unknown", ci_file="unknown", 
            confidence_score=0.0, evidence=[f"Fallo en descubrimiento estático: {reason}"]
        )

    async def _call_cognitive_resolution(self, project_id: str, files: List[str], partial_profile: RepositoryProfile) -> RepositoryProfile:
        """Gemini actúa EXCLUSIVAMENTE para resolver la ambigüedad del árbol de archivos."""
        if self._gemini_client is None:
            from google import genai
            from google.genai import types
            self._gemini_client = genai.Client()
            self._types = types

        prompt = f"""
        Analiza el siguiente árbol plano de archivos de un repositorio desconocido y determina su stack básico.
        Estructura detectada de archivos: {json.dumps(files[:50])}
        Perfil parcial calculado: {json.dumps(asdict(partial_profile))}
        """

        try:
            response = self._gemini_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=self._types.GenerateContentConfig(
                    system_instruction="Eres un Discovery Agent experto. Devuelve obligatoriamente la estructura RepositoryProfile completa respetando el project_id.",
                    response_mime_type="application/json",
                    response_schema=RepositoryProfile,
                    temperature=0.1
                )
            )
            return response.parsed
        except Exception as e:
            logger.error(f"[-] Fallo en resolución cognitiva de repositorio: {e}")
            return partial_profile

