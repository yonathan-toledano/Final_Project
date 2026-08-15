# Phase 4 Validation Log

## Current deployment

- Public domain: `https://finalproject.networkyonathan.com`
- Project EC2: `i-0c41b69739cb5eace`
- Project private IP: `10.40.1.212`
- Project public IP: `3.216.124.207`
- Hermes management EC2: `i-08be2a623140bcce6` (separate and untouched)
- Running application version: `889065022b986c639ba52bd6fe813faadfa15ad1`
- Docker image digest: `sha256:0891c1294480608b2273116f8cfd2be8baac8b0899c4db9f9d3a81c3413801ce`

## Verified infrastructure

- Terraform replacement affected only `aws_instance.k3s`; networking was preserved.
- AWS instance state: `running`.
- AWS system status: `ok`.
- AWS instance status: `ok`.
- `cloud-init` completed without a `scripts_user` failure.
- K3S started successfully during bootstrap.
- ArgoCD Application `monitor` was created by bootstrap.
- ArgoCD detected Git changes and rolled out immutable image tags.

## Verified application endpoints

All checks passed through the public HTTPS domain:

- `/health` -> HTTP 200
- `/ready` -> HTTP 200 and the expected immutable version
- `/status` -> HTTP 200 with pod, node, uptime, version, environment, and deployment timestamp
- `/metrics` -> HTTP 200 with real request and WebSocket metrics
- `/` -> creates a room and redirects to the connection workflow
- `/host/<room>` -> host page loads
- `/view/<room>` -> viewer page loads and connects automatically

## UX validation

- The connection page uses a responsive two-step workflow.
- The viewer QR points directly to the public HTTPS viewer URL.
- No manual IP lookup or LAN address field is required.
- The host attempts camera/microphone startup automatically and keeps a manual fallback button.
- The viewer uses muted autoplay for browser compatibility and exposes an explicit sound button.
- Browser visual inspection confirmed a polished RTL layout with no blocking layout defects.

## Token persistence validation

Room tokens are stored through a K3S `local-path` PersistentVolumeClaim:

- An init container creates the secret only when the persistent file is absent.
- The application reads the secret through `TOKEN_SECRET_FILE`.
- A viewer URL was generated before a Kubernetes rollout.
- After a confirmed rollout, the same pre-rollout viewer URL returned HTTP 200.

This prevents active QR links from becoming unauthorized during ordinary pod rollouts.

## Local quality gates

- Python byte-compilation passed.
- Docker build and container smoke tests passed.
- Helm lint and template rendering passed.
- Terraform format and validation passed.
- GitHub Actions workflow lint passed.
- Current-tree secret scan found no tracked credentials, private keys, `.env`, or Terraform state.

## CI/CD status

- `phase4-monitor-ci` passes on application changes.
- GitOps updates with immutable image tags are detected and deployed by ArgoCD.
- Temporary manual Docker build/push was used because the GitHub Actions Docker Hub credential is not currently available to the CD job.
- Commits marked `[skip cd]` keep CI active while preventing repeated failed CD notifications.
- Full automatic Docker Hub CD must be re-enabled after a valid repository secret is confirmed.

## Terraform Cloud status

Remote-state migration is intentionally pending. It requires an HCP Terraform organization and API token. The local state remains intact and must not be deleted before the migration is completed and verified.
