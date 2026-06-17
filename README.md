# Buggy una solución agéntica para SRE autómático

## 🚀 Guía de Primera Instalación y Configuración (Modo DEMO)

Para realizar una validación real extremo a extremo del Agente SRE sin alterar tus repositorios de producción, debes configurar un entorno controlado siguiendo estos pasos:

### 1. Preparación del Repositorio en GitLab

1. Inicia sesión en tu cuenta de GitLab.
2. Crea un nuevo proyecto **público o privado** vacío llamado exactamente: `demo-sre-test`.
3. En la raíz del repositorio, crea un archivo llamado `app.py`.
4. Copia y pega el siguiente código intencionalmente roto (no cierres las comillas):

   ```python
   print("Hola Mundo)
   ```

5. Realiza el commit y empuja los cambios a la rama predeterminada (`main`).

![1781240011951](image/README/1781240011951.png)

## Configuración Exacta en la Interfaz de GitLab (Modo DEMO)

Basándonos en la pantalla que tienes abierta, realiza exactamente las siguientes acciones. No inventaremos ninguna configuración extra para mantener el flujo directo:

1. **Project name:** `demo-sre-test` (Tal como lo tienes escrito, está perfecto).
2. **Project URL:** Asegúrate de seleccionar tu usuario o el grupo correcto en el desplegable (en tu imagen se lee `repotestcl`).
3. **Project deployment target (optional):** Déjalo exactamente como está, `No deployment planned`. Como nuestra aplicación de prueba es un simple script de Python (`app.py`), no necesitamos integrarlo con nubes de despliegue (como Kubernetes o AWS) en esta etapa. El pipeline fallará de forma pura por la sintaxis.
4. **Visibility Level:** Manténlo en **`Private`** o cámbialo a  **`Public`**. Si lo dejas en **`Private`** (como está en tu captura), asegúrate de que el token de tu archivo `.env` (`GITLAB_TOKEN`) tenga los permisos llamados **`api`** y **`read_api`** habilitados al crearlo en GitLab para que el agente pueda leerlo.
5. **Haz clic en el botón azul:** `Create project` en la parte inferior de la pantalla.

---

### 2. Configuración de Variables de Entorno (.env)

Configura las credenciales reales en tu archivo `.env` ubicado en la raíz del proyecto del agente:

```env
GITLAB_TOKEN="glpat-TuTokenPersonalDeGitLab"
GITLAB_PROJECT_ID="ElIDDeTuProyectoDemoSreTest"
GITLAB_API_URL="https://gitlab.com"
GCP_PROJECT_ID="TuProyectoDeGoogleCloud"
GCP_VERTEX_AI_ID="TuRegionOIdDeVertexAI"
```

### 3. Ejecución de la Verificación de Instalación

Ejecuta la interfaz de entrada del asistente de instalación:

```bash
python run_agent.py --mode demo
```

Este comando activará de forma asíncrona el `Pre-flight Checklist Engine` para comprobar la viabilidad operativa antes de realizar llamadas a los servicios de red.

## 🔑 Guía para la Generación del Token de Acceso (GitLab Personal Access Token)

El Agente Autónomo SRE requiere permisos de escritura para mitigar las fallas detectadas en el repositorio. Para configurar tu token de forma segura, sigue estos pasos en la interfaz web de GitLab:

1. En la esquina superior izquierda de GitLab, haz clic en tu **Avatar de Usuario** (Foto de perfil).
2. Selecciona **Edit profile** (Editar perfil).
3. En el menú lateral izquierdo, haz clic en **Access Tokens** (Tokens de acceso).
4. Haz clic en el botón **Add new token** (Agregar nuevo token).
5. Configura los siguientes campos:
   * **Token name**: `mcp-sre-agent-token`
   * **Expiration date**: (Puedes dejarlo en blanco o por defecto).
   * **Select scopes** (Permisos obligatorios) [SELECCIONAR ÚNICAMENTE]:
     * [✔] **api** (Otorga acceso completo de lectura y escritura a los repositorios a través de la API).
6. Haz clic en el botón verde **Create personal access token**.
7. **IMPORTANTE**: Copia el token generado inmediatamente (comienza con `glpat-`). No volverá a mostrarse en la pantalla.
8. Pega este valor en tu archivo `.env` en la línea: `GITLAB_TOKEN="glpat-..."`

## Crear el pipeline roto en Gitlab para el modo DEMO, prueba de setup

**Paso 1:** Configurar el Repositorio `demo-sre-test` en GitLabComo estás partiendo de un proyecto en blanco, sigue esta secuencia exacta para crear la estructura base:En la pantalla principal de tu proyecto recién creado (demo-sre-test), busca la sección central que dice "The repository for this project is empty".Haz clic en el botón azul "New file" (o en el botón con el signo "+" y luego "New file").

En el campo "File name", escribe exactamente: **_app.py_** En el editor de código que se despliega abajo, escribe la línea de código intencionalmente rota (sin cerrar las comillas)

```python
print("Hello World)
```

En la sección inferior "Commit message", escribe:

```text
Inject intentional syntax error for SRE agent testing.
```

Asegúrate de que el campo "Target branch" diga **_main_**. Haz clic en el botón verde inferior "Commit changes".

**Paso 2:** Crear el Archivo de Pipeline (.gitlab-ci.yml)Para que GitLab intente compilar tu script de Python, ejecute el linter y genere el pipeline en estado failed real que exige el Check 8 de tu especificación (retomar_pr... p. 2), debemos crear el manifiesto de CI/CD:Regresa a la raíz de tu proyecto demo-sre-test haciendo clic en su nombre en la esquina superior izquierda.Haz clic nuevamente en el botón "+" y selecciona "New file".En el campo "File name", escribe exactamente: .gitlab-ci.yml (asegúrate de incluir el punto al inicio).Copia y pega esta configuración de pipeline estándar de Python:yamlstages:

* test

linter_job:
  stage: test
  image: python:3.11-slim
  script:
    - python app.py
Use code with caution.En "Commit message", escribe: ci: add automation pipeline configHaz clic en el botón verde "Commit changes".Paso 3: Sincronizar el Nuevo ID del ProyectoAl crear este nuevo proyecto, GitLab le asignó un número de identificación único a nivel mundial.En la barra lateral izquierda de tu proyecto demo-sre-test, haz clic en "Project overview" (o en el nombre principal del proyecto).Justo debajo del título del repositorio, verás una etiqueta pequeña que dice: "Project ID: XXXXXXXX" (un número de 8 dígitos).Copia ese número exacto.Abre tu archivo .env en la raíz de tu máquina y actualiza la variable:envGITLAB_PROJECT_ID="TU_NUEVO_NUMERO_DE_ID"
Use code with caution.Abre tu archivo config/repo_config.json y actualiza la llave plana sin alterar su estructura original para mantener la compatibilidad:json"project_id": "TU_NUEVO_NUMERO_DE_ID",
Use code with caution.Paso 4: Ejecución de la Verificación Real de Extremo a ExtremoUna vez que GitLab intente ejecutar el pipeline (tomará unos segundos y se pondrá en color rojo indicando failed debido al error de sintaxis de la cadena sin cerrar), ejecuta el Launcher desde tu consola de Windows:bashpython run_agent.py --mode demo
Use code with caution.El Comportamiento que Verás:El asistente DemoRuntime abrirá el canal TCP asíncrono (retomar_pr... p. 1).Validará que el token posee los scopes correctos.Verificará la identidad: demo-sre-test == demo-sre-test (¡Check aprobado!).Escaneará que existe app.py y contiene la firma rota (retomar_pr... p. 2).Capturará el ID del pipeline real fallido desde los servidores de GitLab Cloud (retomar_pr... p. 1).El LogAnalyzer determinístico tomará el control, desplegará el reporte visual completo en pantalla con la métrica explicativa AUTO_FIX, ejecutará los agentes y guardará el respaldo inmutable de auditoría en config/reports/demo_report.json (retomar_pr... p. 2).Por favor, crea el archivo en la interfaz de GitLab, actualiza el ID en tu entorno y ejecútalo. Quedo atento a la traza definitiva de éxito extremo a extremo para cerrar este gran hito.
