# Phase 4 - Terraform & AWS for Monitor

This phase integrates the real `monitor` application into `Final_Project` using Terraform, K3S, Helm, and ArgoCD.

## What is included
- `phase4/monitor/` - the Monitor application source used for the final project
- `phase4/charts/monitor/` - Helm chart for the Monitor app
- `phase4/argocd/monitor-application.yaml` - ArgoCD Application manifest
- `phase4/terraform/` - Terraform for VPC, EC2, security group, and K3S bootstrap
- `.github/workflows/phase4-monitor-ci.yml` - CI checks for app, Helm, Terraform, and Docker build
- `.github/workflows/phase4-monitor-cd.yml` - builds/pushes the image and updates the Helm values file with an immutable SHA

## Course requirements covered
- New VPC created with a Terraform module
- Security group opens HTTP and SSH only to the public IP of the operator
- EC2 instance with public IP
- K3S installed automatically via EC2 user data
- Git installed during bootstrap
- Repo cloned during bootstrap
- Helm chart used for deployment
- Public HTTP validation through the EC2 public IP

## Important note
This phase is still being finalized. Do not treat it as complete until the Terraform plan/apply, K3S deployment, and public HTTP validation are all verified.

## Local validation commands
From the repository root:

```bash
# App syntax
python -m py_compile phase4/monitor/monitor.py

# Docker build
cd phase4/monitor
docker build -t monitor-phase4:test .

# Helm validation
cd ..
docker run --rm -v "$PWD:/src" -w /src alpine/helm:3.15.4 lint phase4/charts/monitor
docker run --rm -v "$PWD:/src" -w /src alpine/helm:3.15.4 template monitor phase4/charts/monitor

# Terraform validation
cd phase4/terraform
docker run --rm -v "$PWD:/workspace" -w /workspace hashicorp/terraform:1.10.5 fmt -check -recursive
docker run --rm -v "$PWD:/workspace" -w /workspace hashicorp/terraform:1.10.5 init -backend=false
docker run --rm -v "$PWD:/workspace" -w /workspace hashicorp/terraform:1.10.5 validate
```

## Deployment notes
The EC2 instance is intended to be the K3S node. The bootstrap script installs:
- `git`
- `k3s`
- `helm`
- ArgoCD

It then applies the ArgoCD Application that points to the Helm chart in this repository.

## Screenshot placeholder
After public deployment is complete, save the required screenshot here:
- `docs/images/phase4-public-ip.png`

## Next step
Run Terraform `plan`, review the cost and resources, then apply only after approval.
