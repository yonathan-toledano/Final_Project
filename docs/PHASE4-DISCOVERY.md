# Phase 4 Discovery — Monitor integration

## Scope
Integrate the real `monitor` application into `Final_Project` while preserving Phase 1–3 deliverables.

## Repositories inspected
- Instructor reference: `EliMutchnik/devops-experts`
- Application source: `yonathan-toledano/monitor`
- Final course repo: `yonathan-toledano/Final_Project`

## Machine state
- OS: Ubuntu 26.04 LTS
- CPU: 2 vCPU
- RAM: 7.6 GiB
- Disk: 48 GiB total, ~35 GiB free
- User: `root`
- Public IP: `16.192.187.101`
- Private IP: `172.31.11.204`
- Installed: Git, Docker
- Missing locally: `aws`, `terraform`, `kubectl`, `helm`, `k3s`, `argocd`, `gh`

## Access state
- AWS credentials: working
- GitHub SSH access: working
- GitHub write access to `Final_Project`: working

## Monitor application facts
- Framework: FastAPI
- Runtime: Uvicorn
- WebSockets: yes
- Dedicated health endpoint: `/health`
- Docker healthcheck probes `/health`
- Environment variables observed:
  - `PUBLIC_BASE_URL`
  - `TOKEN_SECRET`
  - `TOKEN_TTL_SECONDS`
  - `TURN_HOST`
  - `TURN_USERNAME`
  - `TURN_PASSWORD`
- No `/ready` endpoint yet
- No `/metrics` endpoint yet

## Final_Project facts
- Existing course work is QuakeWatch, not Monitor
- Phase 1–3 artifacts exist and should be preserved
- Existing GitHub Actions are for QuakeWatch and are not yet the final Monitor pipeline
- Existing ArgoCD manifest points to QuakeWatch
- Helm chart exists for QuakeWatch
- No Terraform Phase 4 root yet

## Instructor repo patterns seen
- Terraform examples include VPC module usage and simple EC2 patterns
- GitHub Actions examples include build/push and reusable deploy workflows
- Kubernetes/Helm/ArgoCD examples are course-compatible and intentionally simple
- Monitoring example exists in the instructor repo, but the current project should stay lightweight unless monitoring is validated as needed

## Gap matrix
| Requirement | Current State | Status | Action |
|---|---|---|---|
| Preserve Phase 1–3 | Present in repo | DONE | Keep intact |
| Use real Monitor app | App exists separately in `monitor` repo | PARTIAL | Integrate without rebuilding from scratch |
| Terraform VPC | Missing | MISSING | Add Terraform using course-style VPC module |
| Terraform EC2 | Missing | MISSING | Add one small EC2 with public IP |
| K3S bootstrap | Missing | MISSING | Install via EC2 user_data |
| Helm deploy | QuakeWatch chart exists only | MISSING | Add Monitor chart and validate with lint/template |
| ArgoCD GitOps | QuakeWatch manifest exists only | MISSING | Point to Monitor chart/revision |
| CI | QuakeWatch CI exists only | PARTIAL | Replace/add Monitor validation jobs in final repo |
| CD | QuakeWatch CD exists only | PARTIAL | Make a single clear GitOps flow for Monitor |
| Public validation | Not yet validated for Monitor on AWS | MISSING | Test from outside the cluster via public EC2 IP |
| Health checks | `/health` exists | PARTIAL | Add Kubernetes probes and validate end-to-end |
| Readiness | Missing | MISSING | Add `/ready` or equivalent if needed |
| Metrics | Missing | MISSING | Add minimal real metrics only if useful/required |
| Security scan / secrets hygiene | No obvious secrets committed | NEEDS VALIDATION | Keep scanning before any push |

## Recommended cheapest course-compliant architecture
1. One Terraform-created small EC2 instance.
2. New VPC and networking owned by Terraform.
3. K3S single-node cluster installed in `user_data`.
4. Monitor packaged as a Helm chart and deployed to K3S.
5. ArgoCD reconciles the chart from `Final_Project` Git.
6. GitHub Actions validates the app, image, Helm, and Terraform.
7. Image tags use immutable commit SHAs.
8. Expose the app through the EC2 public IP for demo validation.

## Why this is the cheapest sensible option
- No EKS
- No ALB
- No NAT Gateway
- No RDS
- No extra nodes
- No hosted monitoring platform
- Uses only the minimum AWS resources needed for the course phase

## Immediate next implementation steps
1. Create a Phase 4 folder structure in `Final_Project`.
2. Copy or adapt the Monitor source into the final repo in a clean way.
3. Add Helm chart templates and values for Monitor.
4. Add Terraform root files and VPC module usage.
5. Add EC2 user-data to install K3S.
6. Replace QuakeWatch-era deployment docs with accurate Phase 4 docs.
