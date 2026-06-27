# QuakeWatch - Dockerized Flask Application

## Project Description

QuakeWatch is a Python Flask web application that displays earthquake data using a web dashboard.

This repository was containerized as part of Phase 1 of the DevOps Engineer final project.

## Docker Hub Image

Image name:

yonathantoledano/quakewatch:phase1

## Prerequisites

Make sure Docker is installed and running.

## Build the Docker Image

Run:

docker build -t yonathantoledano/quakewatch:phase1 .

## Run the Application with Docker

Run:

docker run -d -p 5001:5000 --name quakewatch-phase1 yonathantoledano/quakewatch:phase1

Open the application in the browser:

http://localhost:5001

## Stop and Remove the Docker Container

Run:

docker stop quakewatch-phase1
docker rm quakewatch-phase1

## Run the Application with Docker Compose

Run:

docker compose up -d

Open the application in the browser:

http://localhost:5001

## Stop Docker Compose

Run:

docker compose down

## Push the Image to Docker Hub

Run:

docker push yonathantoledano/quakewatch:phase1

## Project Files Added for Phase 1

Dockerfile
docker-compose.yml
.dockerignore
README.md

## Deliverables

A zip file containing the Flask application and Docker resources.
A Docker image published to Docker Hub.
Documentation explaining how to build and run the application locally.

# Phase 3 - CI/CD, Helm and GitOps

This project includes a Helm chart, GitHub Actions CI/CD workflows and an ArgoCD Application manifest.

## Helm Chart

Location:

charts/quakewatch

## CI

Workflow:

.github/workflows/ci.yml

Runs on every push to non-main branches.

## CD

Workflow:

.github/workflows/cd.yml

Runs when a Pull Request is merged into main.

## ArgoCD

Application manifest:

argocd/quakewatch-application.yaml

## Documentation

See:

PHASE3-CICD-GITOPS.md
