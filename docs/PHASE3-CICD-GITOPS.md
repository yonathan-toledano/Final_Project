# Phase 3 - Automation, Helm, GitHub Actions and GitOps

## Objective

Establish a full CI/CD and GitOps workflow for the QuakeWatch Kubernetes application.

## Repository

https://github.com/yonathan-toledano/Final_Project

## Branching Strategy

main is the stable branch.

feature/* branches are used for development.

Every push to a non-main branch runs CI.

Every merged Pull Request into main runs CD.

## CI Workflow

File:

.github/workflows/ci.yml

The CI workflow runs pylint on all Python files and builds the Docker image without pushing it.

## CD Workflow

File:

.github/workflows/cd.yml

The CD workflow builds and pushes the Docker image to Docker Hub and publishes the Helm chart to Docker Hub as an OCI artifact.

## Required GitHub Secrets

DOCKERHUB_USERNAME

DOCKERHUB_TOKEN

## Helm Chart

Chart path:

charts/quakewatch

Validate:

helm lint charts/quakewatch

Package:

helm package charts/quakewatch --destination dist

Publish:

helm push dist/quakewatch-0.1.0.tgz oci://registry-1.docker.io/yonathantoledano

## ArgoCD

Manifest:

argocd/quakewatch-application.yaml

Apply:

kubectl apply -f argocd/quakewatch-application.yaml
CI retry
