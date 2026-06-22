# Final DevOps Engineer Course Project

## Project Overview

This is the final project for the DevOps Engineer course.

The project uses a Python Flask application called QuakeWatch and demonstrates a full DevOps workflow.

The project includes Docker, Docker Compose, Kubernetes, Helm, GitHub Actions, ArgoCD and Docker Hub.

The goal is to show how an application moves from source code to a container, then to Kubernetes, then to Helm, and finally to an automated CI/CD and GitOps workflow.

---

## Repository Structure

    Final_Project
    ├── phase1
    │   ├── QuakeWatch
    │   └── QuakeWatch-phase1.zip
    ├── phase2
    │   └── QuakeWatch-phase2.zip
    ├── phase3
    │   └── QuakeWatch-phase3.zip
    ├── charts
    │   └── quakewatch
    ├── argocd
    │   └── quakewatch-application.yaml
    ├── docs
    │   └── PHASE3-CICD-GITOPS.md
    ├── .github
    │   └── workflows
    │       ├── ci.yml
    │       └── cd.yml
    └── README.md

---

## Main folders

### phase1/QuakeWatch

This is the main Flask application folder.

It contains the application code, Dockerfile, docker-compose.yml, Kubernetes YAML files, scripts and documentation.

Important files:

    phase1/QuakeWatch/Dockerfile
    phase1/QuakeWatch/docker-compose.yml
    phase1/QuakeWatch/app.py
    phase1/QuakeWatch/dashboard.py
    phase1/QuakeWatch/requirements.txt
    phase1/QuakeWatch/k8s/
    phase1/QuakeWatch/scripts/

### charts/quakewatch

This is the Helm chart used to deploy the application to Kubernetes.

### .github/workflows

This folder contains the GitHub Actions CI/CD workflows.

### argocd

This folder contains the ArgoCD Application manifest.

---

# Prerequisites

Before running the project, make sure these tools are installed:

- Docker Desktop
- Kubernetes enabled in Docker Desktop
- kubectl
- Helm
- Git

Check the tools:

    docker --version
    kubectl version --client
    helm version
    git --version

---

# Phase 1 - Docker

## Goal

Run the Flask application inside a Docker container.

## Run the application

From the root of the repository, run:

    cd phase1/QuakeWatch
    docker compose up -d

Open the application in the browser:

    http://localhost:5001

Test it with curl:

    curl http://localhost:5001/info
    curl http://localhost:5001/status

The app should return JSON with the application name, author, status and uptime.

Stop Docker Compose:

    docker compose down

---

# Phase 2 - Kubernetes

## Goal

Deploy the Dockerized app to Kubernetes using Docker Desktop.

## Enable Kubernetes

Open Docker Desktop and go to:

    Settings -> Kubernetes -> Enable Kubernetes -> Apply & Restart

Then run:

    kubectl config use-context docker-desktop
    kubectl cluster-info

If Kubernetes is working, you should see a message that says the Kubernetes control plane is running.

## Deploy Kubernetes manifests

Run:

    cd phase1/QuakeWatch
    kubectl apply -f k8s/

Check the resources:

    kubectl get all -n quakewatch

You should see Pods, Deployment, ReplicaSet, Service, HPA and CronJob.

---

# Port Forwarding

## Why port-forwarding is needed

The application runs inside Kubernetes.

Your browser runs on your Mac.

Sometimes Docker Desktop on Mac does not allow the browser to access a Kubernetes Service directly.

So we use port-forwarding.

Port-forwarding creates a tunnel from your Mac to the Kubernetes Service.

Example:

    localhost:5002 -> quakewatch-service:5000

This means that when you open localhost:5002 in the browser, Kubernetes sends the request to the app service on port 5000.

## Manual Kubernetes port-forward

Run:

    kubectl port-forward service/quakewatch-service 5002:5000 -n quakewatch

Important: keep this terminal open.

Then open in the browser:

    http://localhost:5002

To test from another terminal:

    curl http://localhost:5002/info
    curl http://localhost:5002/status

## Automatic port-forward script

The project includes helper scripts.

Start port-forwarding:

    cd phase1/QuakeWatch
    ./scripts/start-port-forward.sh

Open:

    http://localhost:5002

Stop port-forwarding:

    ./scripts/stop-port-forward.sh

## If the port is already in use

Use another local port.

Example:

    kubectl port-forward service/quakewatch-service 5010:5000 -n quakewatch

Then open:

    http://localhost:5010

---

# Phase 3 - Helm

## Goal

Deploy the app using Helm.

Helm is a package manager for Kubernetes.

## Validate the Helm chart

From the repository root, run:

    helm lint charts/quakewatch

Expected result:

    0 chart(s) failed

## Render the chart

    helm template quakewatch charts/quakewatch

## Install or upgrade with Helm

    helm upgrade --install quakewatch charts/quakewatch -n quakewatch --create-namespace

Check Helm:

    helm list -n quakewatch

Check Kubernetes:

    kubectl get all -n quakewatch

## Open the Helm app with port-forwarding

The Helm Service name is:

    quakewatch-quakewatch-service

Run:

    kubectl port-forward service/quakewatch-quakewatch-service 5003:5000 -n quakewatch

Keep this terminal open.

Then open in the browser:

    http://localhost:5003

Test from another terminal:

    curl http://localhost:5003/info
    curl http://localhost:5003/status

---

# Docker Hub

Docker image:

    yonathantoledano/quakewatch:latest

Build manually:

    cd phase1/QuakeWatch
    docker build -t yonathantoledano/quakewatch:latest .

Push manually:

    docker push yonathantoledano/quakewatch:latest

---

# Helm Chart Publishing

Package the chart:

    helm package charts/quakewatch --destination dist

Login to Docker Hub:

    helm registry login registry-1.docker.io -u yonathantoledano

Use a Docker Hub Access Token when asked for a password.

Push the chart:

    helm push dist/quakewatch-0.1.0.tgz oci://registry-1.docker.io/yonathantoledano

Published chart:

    oci://registry-1.docker.io/yonathantoledano/quakewatch

---

# GitHub Actions CI/CD

## CI

File:

    .github/workflows/ci.yml

Runs on every push to a non-main branch.

CI does this:

- Installs Python
- Installs dependencies
- Installs pylint
- Runs pylint
- Builds Docker image without pushing

## CD

File:

    .github/workflows/cd.yml

Runs when a Pull Request is merged into main.

CD does this:

- Logs in to Docker Hub
- Builds Docker image
- Pushes Docker image
- Packages Helm chart
- Pushes Helm chart to Docker Hub

---

# Required GitHub Secrets

Go to:

    GitHub Repository -> Settings -> Secrets and variables -> Actions

Add:

    DOCKERHUB_USERNAME = yourusername
    DOCKERHUB_TOKEN = Docker Hub Access Token with Read and Write permissions

Do not use your Docker Hub password.

---

# ArgoCD GitOps

ArgoCD watches the GitHub repository and deploys the Helm chart.

Application file:

    argocd/quakewatch-application.yaml

Apply it:

    kubectl apply -f argocd/quakewatch-application.yaml

Check it:

    kubectl get application -n argocd

ArgoCD points to:

    https://github.com/yonathan-toledano/Final_Project.git

Chart path:

    charts/quakewatch

---

# GitOps Demo

Change this file:

    charts/quakewatch/values.yaml

Example change:

    phase: phase3-gitops-demo

Then commit and push:

    git add charts/quakewatch/values.yaml
    git commit -m "Demo GitOps Helm chart value change"
    git push

After merging to main, ArgoCD should detect the change and sync the application.

---

# Quick Test Commands

Docker:

    curl http://localhost:5001/info
    curl http://localhost:5001/status

Kubernetes:

    curl http://localhost:5002/info
    curl http://localhost:5002/status

Helm:

    curl http://localhost:5003/info
    curl http://localhost:5003/status

---

# Clean Up

Stop Docker Compose:

    cd phase1/QuakeWatch
    docker compose down

Stop port-forward:

    cd phase1/QuakeWatch
    ./scripts/stop-port-forward.sh

Delete Kubernetes namespace:

    kubectl delete namespace quakewatch

---

# Final Deliverables

Phase 1:

    phase1/QuakeWatch-phase1.zip

Phase 2:

    phase2/QuakeWatch-phase2.zip

Phase 3:

    phase3/QuakeWatch-phase3.zip

Docker image:

    yonathantoledano/quakewatch:latest

Helm chart:

    oci://registry-1.docker.io/yonathantoledano/quakewatch

GitHub repository:

    https://github.com/yonathan-toledano/Final_Project
