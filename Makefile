SHELL := /bin/bash

NAMESPACE ?= minio
RELEASE_NAME ?= minio
VALUES_FILE ?= apps/minio/values.yaml
MINIKUBE_PROFILE ?= minikube
MINIKUBE_DRIVER ?=
MINIKUBE_CPUS ?= 4
MINIKUBE_MEMORY ?= 8192
MINIKUBE_DISK_SIZE ?= 30g

.PHONY: cluster-setup minio-install minio-access minio-uninstall minio-status minio-logs

# how to setup
# make cluster-setup MINIKUBE_PROFILE=local MINIKUBE_CPUS=6 MINIKUBE_MEMORY=12288 MINIKUBE_DISK_SIZE=40g
# make cluster-setup MINIKUBE_DRIVER=docker
cluster-setup:
	MINIKUBE_PROFILE=$(MINIKUBE_PROFILE) MINIKUBE_DRIVER=$(MINIKUBE_DRIVER) \
	MINIKUBE_CPUS=$(MINIKUBE_CPUS) MINIKUBE_MEMORY=$(MINIKUBE_MEMORY) \
	MINIKUBE_DISK_SIZE=$(MINIKUBE_DISK_SIZE) \
		bash scripts/setup-cluster.sh

minio-install: cluster-setup
	NAMESPACE=$(NAMESPACE) RELEASE_NAME=$(RELEASE_NAME) VALUES_FILE=$(VALUES_FILE) \
		MINIKUBE_PROFILE=$(MINIKUBE_PROFILE) \
		bash apps/minio/scripts/install.sh

minio-access:
	NAMESPACE=$(NAMESPACE) RELEASE_NAME=$(RELEASE_NAME) \
		bash apps/minio/scripts/access.sh

minio-uninstall:
	NAMESPACE=$(NAMESPACE) RELEASE_NAME=$(RELEASE_NAME) \
		bash apps/minio/scripts/uninstall.sh

minio-status:
	kubectl -n $(NAMESPACE) get all

minio-logs:
	kubectl -n $(NAMESPACE) logs -l app=minio
