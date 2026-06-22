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

**Paso 2:** Crear el Archivo de Pipeline (.gitlab-ci.yml)

Para que GitLab intente compilar el script de Python, ejecutando el linter y genere el pipeline en estado failed real que exige el Check de la ejecución, debes crear el manifiesto de CI/CD.

Entonces, en Gitlab, ve a la raíz de tu proyecto "demo-sre-test" haciendo clic en su nombre en la esquina superior izquierda. Haz clic, nuevamente, en el botón "+" y selecciona "New file". En el campo "File name", escribe: ".gitlab-ci.yml" (asegúrate de incluir el punto al inicio). Luego, copia y pega esta configuración de pipeline estándar:

'''yml
  linter_job:
  stage: test
  image: python:3.11-slim
  script:
    - python app.py'''

En "Commit message", puedes escribir: "Add automation pipeline config". Haz clic en el botón "Commit changes".

**Paso 3:** Sincronizar el Nuevo ID del Proyecto

Al crear este nuevo proyecto, GitLab le asigna un número de identificación único a nivel mundial. En la barra lateral izquierda de tu proyecto "demo-sre-test", haz clic en en el nombre principal del proyecto. Justo debajo del título del repositorio, verás una etiqueta pequeña que dice: "Project ID: XXXXXXXX" (un número de 8 dígitos). Copia ese número exacto. Abre tu archivo ".env" en la raíz de tu máquina y actualiza la variable: GITLAB_PROJECT_ID="TU_NUEVO_NUMERO_DE_ID"

Abre tu archivo "config/repo_config.json" y actualiza la llave, sin alterar su estructura original para mantener la compatibilidad: "project_id": "TU_NUEVO_NUMERO_DE_ID",

**Paso 4:** Ejecución de la Verificación Real de Extremo a Extremo

Una vez que GitLab intente ejecutar el pipeline (tomará unos segundos y se pondrá en color rojo indicando failed debido al error de sintaxis de la cadena sin cerrar), luego ejecuta el Launcher desde tu consola de Windows: "run_agent.py --mode demo"

El Comportamiento que deberías ver: El asistente DemoRuntime abrirá el canal TCP asíncrono. Validará que el token posee los scopes correctos. Verificará la identidad: demo-sre-test == demo-sre-test (¡Check aprobado!). Escaneará que existe app.py y que contiene la firma rota. Capturará el ID del pipeline real fallido desde los servidores de GitLab Cloud. La clase LogAnalyzer, determinística, dentro del agente triage, tomará el control, desplegará el reporte visual completo en pantalla con la métrica explicativa AUTO_FIX, ejecutará los agentes subsecuentes del flujo cognitivo y guardará el respaldo inmutable de auditoría en config/reports/demo_report.json estampando el hash de idempotencia.

Síntesis, crea el archivo en la interfaz de GitLab, actualiza el ID en tu entorno y ejecútalo el comando con el modificador '--demo'.

En progreso...modo 'REPO' que es el SRE agnóstico para resolver problemas de flujos CI/CD en forma automática con supervisión HITL para revisar los pipelines corregidos y aprobar, rechazar o completar otras tareas que falten (por ejemplo, actualizar una versión incompatible)

## PRUEBA REPO NODE EN GITLAB

### Paso 1 — Crear nuevo proyecto en GitLab

1.1 Crear proyecto:

Name: demo-node-sre
Namespace: demo-sre-test-group

Visibility: Private

Initialize repository:

```text
NO README
NO .gitignore
NO LICENSE
```

Motivo: No queremos que GitLab agregue archivos que puedan contaminar el Discovery.

El repo debe iniciar vacío.

namespace:

```text
Nombre del grupo en el que se creo el proyecto
```

Resultado esperado:

```bash
    https://gitlab.com/<namespace>/demo-node-sre
```

### Paso 2 — Clonar localmente en una carpeta separada

```bash
cd C:\Repos\tracked
git clone https://gitlab.com/<namespace>/demo-node-sre.git
cd demo-node-sre
```

Validación:

```bash
git status
```

Debe decir:

```text
On branch main
No commits yet
```

### Paso 3 — Crear estructura del proyecto

La estructura será deliberadamente estándar:

```bash
demo-node-sre/
    ├── package.json
    ├── tsconfig.json
    ├── .gitlab-ci.yml
    │
    └── src/
       └── server.ts
```

Nada más.

La razón: Discovery debe demostrar que puede inferir

* Evidencia Inferencia
* package.json Node ecosystem
* tsconfig.json TypeScript
* src/*.ts lenguaje
* scripts build/test

### Paso 4 — Crear package.json

Contenido:

```json
{
  "name": "demo-node-sre",
  "version": "1.0.0",
  "description": "Repository for MCP-GitLab-SRE REPO validation",
  "main": "dist/server.js",
  "scripts": {
    "build": "tsc",
    "start": "node dist/server.js",
    "test": "jest"
  },
  "dependencies": {
    "express": "^4.18.3"
  },
  "devDependencies": {
    "typescript": "^5.4.0",
    "@types/node": "^20.0.0",
    "@types/express": "^4.17.0"
  }
}
```

Discovery esperado:

```text
language=node/typescript
build_system=npm
framework=express
test_runner=jest
confidence >= 0.95
```

### Paso 5 — Crear tsconfig.json

Contenido:

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "rootDir": "src",
    "outDir": "dist",
    "strict": true
  }
}
```

Evidencia:

```text
tsconfig.json encontrado
```

Sube el score.

### Paso 6 — Crear la falla intencional

Archivo:

```bash
src/server.ts
```

Contenido:

```typescript
import express from "express";
const app = express();
const DATABASE_PASSWORD = "prod_password=SuperSecret123";
app.get("/", (_, res) => {
    res.json({
        status:"running",
        service:"demo-node-sre"
    });
});
app.listen(3000);
```

Esta falla NO es de sintaxis, es importante porque se quiere romper la hipótesis: "todo error se arregla con regex".

Aquí debe ocurrir:

LogAnalyzer
      |
      |
UNKNOWN_PATTERN
      |
      v
  TriageAgent
      |
      |
    Gemini
      |
      |
Remediation Plan

### Paso 7 — Crear pipeline GitLab

Archivo:

```bash
  .gitlab-ci.yml
  ```

Contenido:

```bash
stages:
  - test

node_validation:

  image:
    node:20

  stage: 
    test

  script:
    npm install
    npm run build
   ```

Objetivo: Generar pipeline real. No buscamos que falle por build.

Buscamos que el agente vea:

* pipeline exists
* job exists
* logs available

### Paso 8 — Commit inicial

```bash
git add .
git commit -m "Initial Node TypeScript SRE demo"
git push origin main
```

### Paso 9 — Verificación manual GitLab

Antes de lanzar SRE:

En GitLab:

Pipelines:

Debe existir:

```bash
node_validation
```

Estado:

**_passed_**

o

**_failed_**

ambos sirven.

Lo importante:

Existe un objeto GitLab CI real.

### Paso 10 — Forzar incidente SRE para provocar el caso

Modificar:

```js
const DATABASE_PASSWORD = "prod_password=SuperSecret123";
```

Agregar:

```js
const AWS_SECRET = "AKIA_TEST_SECRET_EXPOSED";
```

Commit:

```bash
git add .
git commit -m "Introduce credential leak test"
git push
```

Ahora GitLab tendrá:

```text
 Pipeline N
     |
     v
 job node_validation
     |
     v
    logs
```

### Paso 11 — Ejecutar MCP-GitLab-SRE

Desde:

Buggy-Gitlab-SRE

configurar:

```js
.env
```

Debe apuntar al nuevo repo:

Ejemplo conceptual:

```bash
GITLAB_PROJECT_ID=<demo-node-sre>
GITLAB_TOKEN=<token>
GITLAB_URL=https://gitlab.com
```

Luego:

```python
python run_agent.py --mode repo
```
