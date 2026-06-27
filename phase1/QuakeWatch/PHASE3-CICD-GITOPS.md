# Phase 3 - Automation, Helm, GitHub Actions and GitOps

## Objective

The objective of Phase 3 is to establish a complete CI/CD and GitOps workflow for the QuakeWatch Kubernetes application.

This phase includes:

- Helm packaging
- Git repository setup
- Branching strategy
- CI workflow with pylint and Docker build
- CD workflow with Docker image push
- Helm chart publishing to Docker Hub
- ArgoCD declarative deployment

## Repository

GitHub repository:

https://github.com/yonathan-toledano/devops-final-project.git

## Branching Strategy

main:

Stable production branch.

feature/*:

Development branches.

Pull Request flow:

1. Create a feature branch.
2. Push code to the feature branch.
3. CI runs automatically on every push to non-main branches.
4. Open a Pull Request to main.
5. Merge the Pull Request.
6. CD runs automatically after the PR is merged into main.

## CI Workflow

File:

.github/workflows/ci.yml

Trigger:

Every push to non-main branches.

Actions:

- Checkout code
- Install Python dependencies
- Install pylint
- Run pylint on all Python files
- Build Docker image without pushing it

## CD Workflow

File:

.github/workflows/cd.yml

Trigger:

When a Pull Request into main is closed and merged.

Actions:

- Checkout code
- Login to Docker Hub
- Build and push Docker image
- Package Helm chart
- Push Helm chart to Docker Hub as an OCI artifact

## Required GitHub Secrets

DOCKERHUB_USERNAME

Value:

yonathantoledano

DOCKERHUB_TOKEN

Value:

Docker Hub access token.

Do not use your Docker Hub password. Use an access token.

## Helm Chart

Chart location:

charts/quakewatch

Validate the chart:

helm lint charts/quakewatch

Render the chart:

helm template quakewatch charts/quakewatch

Package the chart:

helm package charts/quakewatch --destination dist

Push the chart to Docker Hub:

helm registry login registry-1.docker.io -u yonathantoledano
helm push dist/quakewatch-0.1.0.tgz oci://registry-1.docker.io/yonathantoledano

Published chart:

oci://registry-1.docker.io/yonathantoledano/quakewatch

## ArgoCD

ArgoCD application manifest:

argocd/quakewatch-application.yaml

Apply the ArgoCD Application:

kubectl apply -f argocd/quakewatch-application.yaml

Check application:

kubectl get application -n argocd

## GitOps Change Demo

A helper script was added:

./scripts/gitops-demo-change.sh

This script changes a value in the Helm chart and commits the change.

After pushing and merging to main, ArgoCD should detect the change and sync the application.

## Local Kubernetes Test with Helm

Install or upgrade locally:

helm upgrade --install quakewatch charts/quakewatch -n quakewatch --create-namespace

Check resources:

kubectl get all -n quakewatch

Port forward:

./scripts/start-port-forward.sh

Open:

http://localhost:5002
