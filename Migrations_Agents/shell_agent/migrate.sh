#!/bin/bash

# Platform Migration Agent (Shell Version)
# Automates PCF -> Kubernetes migration

SOURCE_DIR=""
OUTPUT_DIR="./shell_output"

usage() {
    echo "Usage: $0 --source <path> [--output <path>]"
    exit 1
}

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --source) SOURCE_DIR="$2"; shift ;;
        --output) OUTPUT_DIR="$2"; shift ;;
        *) echo "Unknown parameter: $1"; usage ;;
    esac
    shift
done

if [ -z "$SOURCE_DIR" ]; then
    usage
fi

echo "Starting migration for: $SOURCE_DIR"

# 1. Discovery
APP_TYPE="unknown"
APP_NAME=$(basename "$SOURCE_DIR")
JAVA_VER="11"
PACKAGING="jar"
NODE_VER="18"

# Check manifest.yml
if [ -f "$SOURCE_DIR/manifest.yml" ]; then
    # Improved name extraction (strip leading space and handle potential \r)
    M_NAME=$(grep "name:" "$SOURCE_DIR/manifest.yml" | head -1 | sed 's/.*name: *//' | tr -d '\r' | xargs)
    [ ! -z "$M_NAME" ] && APP_NAME=$M_NAME
    
    BUILDPACK=$(grep "buildpack:" "$SOURCE_DIR/manifest.yml" | head -1)
    if [[ "$BUILDPACK" == *"python"* ]]; then APP_TYPE="python"; fi
    if [[ "$BUILDPACK" == *"java"* ]]; then APP_TYPE="java-maven"; fi
    if [[ "$BUILDPACK" == *"nodejs"* ]]; then APP_TYPE="nodejs"; fi
fi

# Fallback heuristics
if [ "$APP_TYPE" == "unknown" ]; then
    if [ -f "$SOURCE_DIR/pom.xml" ]; then APP_TYPE="java-maven"; fi
    if [ -f "$SOURCE_DIR/requirements.txt" ]; then APP_TYPE="python"; fi
    if [ -f "$SOURCE_DIR/package.json" ]; then
        if grep -q "\"react\"" "$SOURCE_DIR/package.json"; then
            APP_TYPE="react"
        else
            APP_TYPE="nodejs"
        fi
    fi
fi

echo "Detected application: $APP_NAME ($APP_TYPE)"

# 2. Extract versions
if [ "$APP_TYPE" == "java-maven" ]; then
    # Extract java.version using sed
    JV=$(sed -n 's/.*<java.version>\(.*\)<\/java.version>.*/\1/p' "$SOURCE_DIR/pom.xml" | tr -d '\r' | xargs)
    [ ! -z "$JV" ] && JAVA_VER=$JV
    PK=$(sed -n 's/.*<packaging>\(.*\)<\/packaging>.*/\1/p' "$SOURCE_DIR/pom.xml" | tr -d '\r' | xargs)
    [ ! -z "$PK" ] && PACKAGING=$PK
    echo "Java Version: $JAVA_VER, Packaging: $PACKAGING"
fi

if [[ "$APP_TYPE" == "nodejs" || "$APP_TYPE" == "react" ]]; then
    # Extract node version using sed and grep
    NV=$(sed -n 's/.*"node": *"\([^"]*\)".*/\1/p' "$SOURCE_DIR/package.json" | grep -o '[0-9]\+' | head -1)
    [ ! -z "$NV" ] && NODE_VER=$NV
    echo "Node Version: $NODE_VER"
fi

# 3. Artifact Generation
mkdir -p "$OUTPUT_DIR"

generate_dockerfile() {
    case $APP_TYPE in
        python)
            cat <<EOF > "$OUTPUT_DIR/Dockerfile"
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "app.py"]
EOF
            ;;
        java-maven)
            cat <<EOF > "$OUTPUT_DIR/Dockerfile"
FROM openjdk:${JAVA_VER}-jre-slim
WORKDIR /app
COPY target/${APP_NAME}.${PACKAGING} app.${PACKAGING}
ENTRYPOINT ["java", "-jar", "app.${PACKAGING}"]
EOF
            ;;
        nodejs)
            cat <<EOF > "$OUTPUT_DIR/Dockerfile"
FROM node:${NODE_VER}-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
CMD ["npm", "start"]
EOF
            ;;
        react)
            cat <<EOF > "$OUTPUT_DIR/Dockerfile"
# Build Stage
FROM node:${NODE_VER}-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Serve Stage
FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
EOF
            ;;
        *)
            echo "Warning: Unknown app type, generating generic Dockerfile"
            echo "FROM alpine" > "$OUTPUT_DIR/Dockerfile"
            ;;
    esac
}

generate_helm() {
    CHART_DIR="$OUTPUT_DIR/chart/$APP_NAME"
    mkdir -p "$CHART_DIR/templates"
    
    # Chart.yaml
    cat <<EOF > "$CHART_DIR/Chart.yaml"
apiVersion: v2
name: $APP_NAME
description: A Helm chart for $APP_NAME
type: application
version: 0.1.0
appVersion: "1.0.0"
EOF

    # values.yaml
    cat <<EOF > "$CHART_DIR/values.yaml"
replicaCount: 1
image:
  repository: $APP_NAME
  pullPolicy: IfNotPresent
  tag: "latest"
service:
  type: ClusterIP
  port: 80
EOF

    # deployment.yaml
    cat <<EOF > "$CHART_DIR/templates/deployment.yaml"
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "${APP_NAME}.fullname" . }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      {{- include "${APP_NAME}.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      labels:
        {{- include "${APP_NAME}.selectorLabels" . | nindent 8 }}
    spec:
      containers:
        - name: {{ .Chart.Name }}
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          ports:
            - containerPort: {{ .Values.service.port }}
EOF
}

generate_dockerfile
generate_helm

echo "Artifacts generated in: $OUTPUT_DIR"
