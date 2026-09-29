# CivicPulse Runbook

## Local startup
```bash
docker compose up --build
```

Frontend: `http://localhost:8080`

Backend liveness: `/health`
Backend readiness: `/ready`

## Backend checks
```bash
cd backend
pytest -q --cov=app
ruff check app tests scripts
mypy app
alembic upgrade head
python -m scripts.seed
```

## CI
GitHub Actions validates backend and frontend quality gates, Docker builds and Trivy scans, Compose integration, and Kubernetes manifests.

## Troubleshooting
If `/ready` fails, inspect Postgres and Redis first. For HTTP 409 status transitions, check the state-machine transition table. For `/api/stats`, inspect the `X-Cache` header.

## Secrets
Never commit `.env` files or API keys. Use deployment/repository secrets.

## Rollback
Redeploy the previously verified immutable image reference and verify rollout completion with `kubectl rollout status` for Kubernetes.
