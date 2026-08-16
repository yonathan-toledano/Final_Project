#!/usr/bin/env bash
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml

apt-get update
apt-get install -y git curl ca-certificates jq

curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="server --write-kubeconfig-mode 644" sh -

until kubectl get nodes >/dev/null 2>&1; do
  sleep 5
done

curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

mkdir -p /opt/final-project
if [ ! -d /opt/final-project/.git ]; then
  git clone --depth 1 --branch "${repository_branch}" "${repository_url}" /opt/final-project
else
  cd /opt/final-project
  git pull --ff-only origin "${repository_branch}"
fi

kubectl create namespace "${argocd_namespace}" --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace "${app_namespace}" --dry-run=client -o yaml | kubectl apply -f -

kubectl create -n "${argocd_namespace}" -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for ArgoCD pods to exist and become ready before applying the application object.
until kubectl -n "${argocd_namespace}" get pods >/dev/null 2>&1; do
  sleep 10
done
kubectl -n "${argocd_namespace}" wait --for=condition=Ready pod --all --timeout=900s || true

kubectl apply -f /opt/final-project/phase4/argocd/monitor-application.yaml
kubectl apply -f /opt/final-project/phase4/argocd/observability-applications.yaml
kubectl patch cm argocd-cm -n argocd --type merge -p '{"data":{"server.insecure":"true"}}' || true
kubectl rollout restart deployment/argocd-server -n argocd || true
kubectl apply -f /opt/final-project/phase4/argocd/argocd-ingress.yaml
