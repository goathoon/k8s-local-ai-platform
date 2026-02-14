#!/usr/bin/env bash
set -euo pipefail

MINIKUBE_PROFILE="${MINIKUBE_PROFILE:-minikube}"
MINIKUBE_DRIVER="${MINIKUBE_DRIVER:-docker}"
MINIKUBE_CPUS="${MINIKUBE_CPUS:-4}"
MINIKUBE_MEMORY="${MINIKUBE_MEMORY:-8192}"
MINIKUBE_DISK_SIZE="${MINIKUBE_DISK_SIZE:-30g}"

if ! command -v minikube >/dev/null 2>&1; then
  echo "[ERROR] minikube command not found"
  exit 1
fi

if ! command -v kubectl >/dev/null 2>&1; then
  echo "[ERROR] kubectl command not found"
  exit 1
fi

MINIKUBE_HOST_STATUS="$(minikube status -p "${MINIKUBE_PROFILE}" --format='{{.Host}}' 2>/dev/null || true)"
if [[ "${MINIKUBE_HOST_STATUS}" != "Running" ]]; then
  echo "[INFO] Starting minikube profile=${MINIKUBE_PROFILE}"
  START_CMD=(
    minikube start
    -p "${MINIKUBE_PROFILE}"
    --cpus="${MINIKUBE_CPUS}"
    --memory="${MINIKUBE_MEMORY}"
    --disk-size="${MINIKUBE_DISK_SIZE}"
  )
  if [[ -n "${MINIKUBE_DRIVER}" ]]; then
    START_CMD+=(--driver="${MINIKUBE_DRIVER}")
  fi
  "${START_CMD[@]}"
else
  echo "[INFO] minikube profile=${MINIKUBE_PROFILE} is already running"
fi

minikube update-context -p "${MINIKUBE_PROFILE}" >/dev/null

echo "[INFO] Enabling addons: ingress, metrics-server"
minikube addons enable ingress -p "${MINIKUBE_PROFILE}" >/dev/null
minikube addons enable metrics-server -p "${MINIKUBE_PROFILE}" >/dev/null

echo "[INFO] Waiting for ingress controller rollout"
kubectl -n ingress-nginx rollout status deploy/ingress-nginx-controller --timeout=5m

echo "[INFO] Waiting for metrics-server rollout"
kubectl -n kube-system rollout status deploy/metrics-server --timeout=5m

echo "[INFO] Waiting for nodes to be ready"
kubectl wait --for=condition=Ready node --all --timeout=3m >/dev/null

echo "[OK] Cluster setup completed"
echo " - profile: ${MINIKUBE_PROFILE}"
echo " - addons: ingress, metrics-server"
