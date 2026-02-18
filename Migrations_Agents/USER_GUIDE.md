# Platform Migration Agent: User Guide

Welcome to the **Platform Migration Agent**! This tool is designed to simplify and accelerate the process of migrating applications from Pivotal Cloud Foundry (PCF) to Kubernetes by automatically generating the necessary containerization and orchestration artifacts.

---

## 🚀 Quick Start

### 1. Installation
The agent is available in both Python and Bash versions to suit your environment.

#### Python Version (Recommended)
```bash
# Set up a clean environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### Shell Version
No installation required! Just ensure you have `bash`, `sed`, and `awk` available.

---

## 🛠️ How to Use

### Python Agent
Execute the migration via the command line:
```bash
python -m migration_agent.main --source ./my-pcf-app --output ./k8s-artifacts
```

### Shell Agent
For environments without Python:
```bash
bash shell_agent/migrate.sh --source ./my-pcf-app --output ./k8s-artifacts
```

---

## 🔍 How It Works

The agent follows a three-step process:

### Phase 1: Discovery
The `discovery.py` module scans your source directory to build an application profile.
*   **PCF Manifest**: Reads `manifest.yml` for app names, environment variables, and services.
*   **Buildpack Detection**: Identifies the language (Python, Java, Node) from the PCF buildpack.
*   **Code Heuristics**: If no manifest exists, it looks for standard files like `pom.xml`, `requirements.txt`, or `package.json`.

### Phase 2: Metadata Extraction
Once the type is identified, the agent extracts deep metadata:
*   **Java**: Detects Java major version (17, 21) and packaging type (JAR/WAR) from Maven.
*   **Node.js**: Extracts Node version from `engines` and distinguishes between standard Node and React apps.
*   **React**: Identifies React apps to apply multi-stage Nginx templates.

### Phase 3: Generation
The agent renders Jinja2 templates (or Heredocs in Bash) to create:
1.  **Dockerfile**: Optimized for the specific language and runtime.
2.  **Helm Chart**: A full Kubernetes deployment structure (Deployment, Service, Values).

---

## 📦 Supported Technologies

| Framework | Detection File | Output Style |
| :--- | :--- | :--- |
| **Java / Spring Boot** | `pom.xml` | OpenJDK based, JAR/WAR aware |
| **Python** | `requirements.txt` | Slim Python based |
| **Node.js** | `package.json` | Alpine Node based |
| **React** | `package.json` (w/ react) | Multi-stage (Build -> Nginx) |

---

## 📋 Artifacts Generated

All generated files are placed in your specified `--output` directory:
*   `Dockerfile`: Ready for `docker build`.
*   `chart/`: A Helm chart directory containing:
    *   `Chart.yaml`: Project metadata.
    *   `values.yaml`: Customizable deployment parameters.
    *   `templates/deployment.yaml`: The Kubernetes Deployment manifest.
    *   `templates/service.yaml`: The Kubernetes Service manifest.

---

## 💡 Troubleshooting

*   **App Type Not Detected**: Ensure your project has the standard entry files (`pom.xml`, `package.json`, etc.) in the root directory.
*   **Wrong Java Version**: The agent extracts the version from `<java.version>` in `pom.xml`. Ensure this tag is present for accurate detection.
*   **Environment Variables Missing**: Make sure they are defined under the `env` section of your PCF `manifest.yml`.
