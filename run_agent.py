import os
import json
import asyncio
import argparse
import logging

# Formateador limpio con soporte a marcas de tiempo estandarizadas
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("Launcher")

def load_env_file(filepath: str = ".env"):
    """Parser nativo industrial para cargar el .env en la memoria de Windows sin librerías."""
    if not os.path.exists(filepath):
        logger.warning(f"[-] Archivo de secretos {filepath} no detectado físicamente.")
        return
        
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # Ignorar comentarios o líneas vacías
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                # Inyección explícita en el entorno del sistema operativo
                os.environ[key] = val
        logger.debug("[✔] Secretos del archivo .env cargados en os.environ de forma nativa.")
    except Exception as e:
        logger.error(f"[-] Error parseando el archivo .env de forma nativa: {e}")

async def main():
    parser = argparse.ArgumentParser(description="MCP-GitLab-SRE: Agente autónomo de SRE con protocolo MCP")
    parser.add_argument("--mode", type=str, choices=["mock", "demo", "repo"], default="mock", help="Modo operativo del sistema")
    parser.add_argument(
        "--test-case", 
        type=str, 
        choices=["syntax_error", "missing_dependencies", "vuln", "permission_denied", "timeout", "unknown_error"], 
        default="syntax_error", 
        help="Caso de prueba para inyección local"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Aumenta la verbosidad de salida de logs a nivel DEBUG")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # 1. EJECUCIÓN DEL PARSER NATIVO: Cargamos los secretos reales en memoria antes de instanciar la factoría
    load_env_file(".env")

    # Lazyloading de fábricas pesadas para optimizar recursos en Cloud Run
    from src.runtime.factory import RuntimeFactory
    from src.agents.orchestrator import AgentOrchestrator

    config_path = "config/repo_config.json"
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"[-] Falla crítica leyendo archivo operativo base: {e}")
        return

    # Inyección dinámica en caliente
    config["mode"] = args.mode
    config["test_case"] = args.test_case

    logger.info("===============================================================")
    logger.info(f"🚀 MCP-GitLab-SRE Agent Orchestrator Inicializado")
    logger.info(f"[+] Modo activo: {config['mode'].upper()}")
    if config["mode"] == "mock":
        logger.info(f"[+] Inyectando caso de prueba: {config['test_case'].upper()}")
    logger.info("===============================================================")

    try:
        runtime = RuntimeFactory.create(config)
    except NotImplementedError as e:
        logger.error(e)
        return

    orchestrator = AgentOrchestrator(runtime=runtime)
    await orchestrator.orchestrate()

if __name__ == "__main__":
    asyncio.run(main())
