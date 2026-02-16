# Platform Migration Agent Instructions

This guide provides instructions on how to use the Platform Migration Agent (both Python and Shell versions) to automate the migration of PCF applications to Kubernetes.

## Prerequisites

### Python Agent
- Python 3.8 or higher.
- Required dependencies (installed via `pip`): `pyyaml`, `jinja2`, `click`.

### Shell Agent
- A Unix-like environment (Linux, macOS, or Git Bash for Windows).
- Standard tools: `sed`, `awk`, `grep`.

---

## 1. Python Migration Agent

The Python agent is the most robust version, supporting more granular detection and flexible template rendering.

### Setup
```bash
# It is recommended to use a virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Usage
To run a migration, use the following command:
```bash
python -m migration_agent.main --source <source_directory> --output <output_directory>
```

**Options:**
- `--source`: Path to the PCF application source code (containing `manifest.yml` or standard build files).
- `--output`: Path where the generated Dockerfile and Helm chart will be saved (default: `./output`).

---

## 2. Shell Migration Agent

The shell agent is a standalone Bash script for environments where Python is not available.

### Usage
```bash
./shell_agent/migrate.sh --source <source_directory> --output <output_directory>
```

**Options:**
- `--source`: Path to the source code.
- `--output`: Path where artifacts will be saved (default: `./shell_output`).

---

## 3. Supported Application Types

Both agents automatically detect the application type and version using the following logic:

| App Type | Detection Logic | Extra Metadata Extracted |
| :--- | :--- | :--- |
| **Java (Maven)** | Presence of `pom.xml` | Java version, Packaging (JAR/WAR) |
| **Python** | Presence of `requirements.txt` | Dependency list |
| **Node.js** | Presence of `package.json` | Node major version (from `engines`) |
| **React** | `package.json` with `react` dependency | Node major version, Multi-stage build |

### Special Detection: PCF `manifest.yml`
If a `manifest.yml` is present, the agents will:
- Extract the application name.
- Inject environment variables into the generated Dockerfile.
- Detect application type via the `buildpack` field.

---

## 4. Generated Artifacts

For every successful migration, the agent creates:

1.  **Dockerfile**: A container image definition optimized for the detected framework.
    - *Example*: Multi-stage builds for React (Node build -> Nginx).
    - *Example*: OpenJDK base images for Java (setting entrypoints for JAR vs WAR).
2.  **Helm Chart**: A standard Kubernetes deployment package including:
    - `Chart.yaml`: Metadata for the application.
    - `values.yaml`: Configurable parameters (replicas, image, service port).
    - `templates/`: Kubernetes manifests (Deployment, Service).

---

## 5. Verification Examples

### Example: Spring Boot Migration
```bash
python -m migration_agent.main --source sample_spring_app --output output/my-spring-app
```
**Results:**
- Detects Java 17 or 21 (based on `pom.xml`).
- Sets `ENTRYPOINT ["java", "-jar", "app.jar"]` (or `.war`).
- Injects PCF environment variables.

### Example: React Migration
```bash
./shell_agent/migrate.sh --source sample_react_app --output output/my-react-app
```
**Results:**
- Identifies React app.
- Generates a multi-stage Dockerfile using `nginx:alpine` for the final stage.
