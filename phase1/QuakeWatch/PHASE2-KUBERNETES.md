# Phase 2 - Kubernetes Orchestration

## Objective

The objective of Phase 2 is to deploy the Dockerized QuakeWatch Flask application to Kubernetes using Docker Desktop.

The goal is to create a scalable and highly available deployment using Kubernetes resources.

## Kubernetes Cluster Setup

Kubernetes was enabled using Docker Desktop.

To verify the cluster:

kubectl config use-context docker-desktop
kubectl cluster-info

## Docker Image

The application uses the Docker image created in Phase 1:

yonathantoledano/quakewatch:phase1

## Kubernetes Manifests

The manifests are located in the k8s directory.

Files:

00-namespace.yaml
01-configmap.yaml
02-secret.yaml
03-deployment.yaml
04-service.yaml
05-hpa.yaml
06-cronjob.yaml

## Resources Created

Namespace:

quakewatch

Deployment:

quakewatch-deployment

Replica count:

3

Service:

quakewatch-service

Service type:

NodePort

External port:

30081

HPA:

quakewatch-hpa

CronJob:

quakewatch-health-check

## Deploy the Application

Run:

kubectl apply -f k8s/

## Check Kubernetes Resources

kubectl get all -n quakewatch

Check pods:

kubectl get pods -n quakewatch

Check deployment:

kubectl get deployment -n quakewatch

Check ReplicaSet:

kubectl get rs -n quakewatch

Check service:

kubectl get service -n quakewatch

Check HPA:

kubectl get hpa -n quakewatch

Check CronJob:

kubectl get cronjob -n quakewatch

## Access the Application

Open:

http://localhost:30081

## Port Forward Alternative

If NodePort does not work, run:

kubectl port-forward service/quakewatch-service 5002:5000 -n quakewatch

Then open:

http://localhost:5002

## Liveness and Readiness Probes

The Deployment includes both readinessProbe and livenessProbe.

Both probes check:

/

on port:

5000

Readiness Probe checks if the application is ready to receive traffic.

Liveness Probe checks if the application is healthy and should keep running.

## CronJob Health Check

The CronJob runs every 5 minutes and checks the service from inside the cluster:

http://quakewatch-service:5000/

## Delete the Kubernetes Resources

kubectl delete namespace quakewatch

## Automatic Port Forwarding

On Docker Desktop for Mac, NodePort may not always be available directly through localhost.

For this reason, the project includes scripts for automatic local port forwarding.

Start port-forwarding:

./scripts/start-port-forward.sh

Stop port-forwarding:

./scripts/stop-port-forward.sh

Deploy Kubernetes and start port-forwarding automatically:

./scripts/deploy-k8s-with-port-forward.sh

After starting port-forwarding, open:

http://localhost:5002

The port-forward command maps:

localhost:5002

to the Kubernetes service:

quakewatch-service:5000
