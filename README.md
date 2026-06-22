# Final DevOps Engineer Course Project

## Application

QuakeWatch - Python Flask application.

## Repository Structure

phase1/QuakeWatch

Contains the Flask application, Dockerfile, docker-compose.yml, Kubernetes manifests, scripts and application documentation.

phase2

Contains the Phase 2 zip deliverable.

phase3

Contains the Phase 3 zip deliverable.

charts/quakewatch

Contains the Helm chart for deploying the application to Kubernetes.

.github/workflows

Contains the GitHub Actions CI/CD workflows.

argocd

Contains the ArgoCD Application manifest.

docs

Contains Phase 3 documentation.

## Phase 1 - Docker

The application was containerized using Docker.

Includes:

- Dockerfile
- docker-compose.yml
- Docker Hub image
- Local build and run instructions

Docker image:

yonathantoledano/quakewatch:latest

## Phase 2 - Kubernetes

The application was deployed to Kubernetes using Docker Desktop.

Includes:

- Deployment
- ReplicaSet
- Service
- ConfigMap
- Secret
- HPA
- CronJob
- Liveness Probe
- Readiness Probe

## Phase 3 - Automation, CI/CD and GitOps

The application was packaged and automated using Helm, GitHub Actions and ArgoCD.

Includes:

- Helm chart
- CI workflow with pylint and Docker build
- CD workflow with Docker image push
- Helm chart publishing to Docker Hub
- ArgoCD Application manifest

## CI/CD

CI runs on every push to non-main branches.

CD runs after a Pull Request is merged into main.

Required GitHub secrets:

- DOCKERHUB_USERNAME
- DOCKERHUB_TOKEN

## Helm

Validate chart:

helm lint charts/quakewatch

Render chart:

helm template quakewatch charts/quakewatch

Install chart:

helm upgrade --install quakewatch charts/quakewatch -n quakewatch --create-namespace

## ArgoCD

Apply ArgoCD Application:

kubectl apply -f argocd/quakewatch-application.yaml
