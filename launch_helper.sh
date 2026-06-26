#!/bin/bash
# ══════════════════════════════════════════════════════════════
# 🚀 LAUNCH HELPER GATEWAY - BUGGY - MCP-GitLab-SRE
# ══════════════════════════════════════════════════════════════

clear
echo "============================================================="
echo "⚙️  INICIALIZANDO PLATAFORMA AUTÓNOMA BUGGY SRE"
echo "============================================================="

# 1. VALIDACIÓN DE ENTORNO (.env)
if [ ! -f .env ]; then
    echo "❌ [ERROR] Archivo de secretos .env no encontrado en la raíz."
    echo "💡 Copia .env.example a .env y rellena las credenciales correspondientes."
    exit 1
fi

# 2. SELECCIÓN DE MODOS INTERACTIVOS ( Buggy CLI)
echo -e "\n--- Modos de Operación Disponibles ---"
echo "1) MOCK (Pruebas locales con archivos de log)"
echo "2) DEMO (Pre-flight Checklist "Hello World" / Sanity Check Integraciones)"
echo "3) REPO (Ejecución Autónoma en Producción)"
read -p "Seleccione una opción operativa [1-3]: " opt

case $opt in
    1)
        echo -e "\n--- Casos de Prueba Disponibles ---"
        echo "a) syntax_error (Lee config/fixtures/syntax_error.log)"
        echo "b) missing_dep  (Lee config/fixtures/missing_dependencies.log)"
        echo "c) vuln         (Lee config/fixtures/vulnerability.json)"
        read -p "Seleccione caso de inyección [a-c]: " case_opt
        
        case $case_opt in
            a) python run_agent.py --mode mock --test-case syntax_error ;;
            b) python run_agent.py --mode mock --test-case missing_dep --verbose ;;
            c) python run_agent.py --mode mock --test-case vuln ;;
            *) echo "❌ Opción inválida."; exit 1 ;;
        esac
        ;;
    2)
        echo "[*] Lanzando Sanity Checklist del entorno..."
        python run_agent.py --mode demo
        ;;
    3)
        echo "⚠️  ADVERTENCIA: Iniciando modo producción REPO."
        python run_agent.py --mode repo --verbose
        ;;
    *)
        echo "❌ Selección fuera de rango."
        exit 1
        ;;
esac
