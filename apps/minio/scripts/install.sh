#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="${NAMESPACE:-minio}"
RELEASE_NAME="${RELEASE_NAME:-minio}"
VALUES_FILE="${VALUES_FILE:-apps/minio/values.yaml}"
MINIKUBE_PROFILE="${MINIKUBE_PROFILE:-minikube}"

if ! command -v helm >/dev/null 2>&1; then
  echo "[ERROR] helm command not found"
  exit 1
fi

if ! command -v kubectl >/dev/null 2>&1; then
  echo "[ERROR] kubectl command not found"
  exit 1
fi

if ! command -v minikube >/dev/null 2>&1; then
  echo "[ERROR] minikube command not found"
  exit 1
fi

if [[ "$(minikube status -p "${MINIKUBE_PROFILE}" --format='{{.Host}}' 2>/dev/null || true)" != "Running" ]]; then
  echo "[ERROR] minikube profile ${MINIKUBE_PROFILE} is not running"
  exit 1
fi

helm repo add minio https://charts.min.io/ >/dev/null 2>&1 || true
helm repo update minio >/dev/null

kubectl get ns "${NAMESPACE}" >/dev/null 2>&1 || kubectl create ns "${NAMESPACE}" >/dev/null

helm upgrade --install "${RELEASE_NAME}" minio/minio \
  --namespace "${NAMESPACE}" \
  --values "${VALUES_FILE}" \
  --wait \
  --timeout 10m

echo "[OK] MinIO installed"
echo " - namespace: ${NAMESPACE}"
echo " - release:   ${RELEASE_NAME}"
