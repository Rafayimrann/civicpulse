# CivicPulse

Municipal complaint intake, triage, and operations platform. The repository includes the backend, frontend, tests, Docker Compose configuration, Kubernetes manifests, and GitHub Actions CI pipeline.

## Layout

```
backend/
  app/{routes,services,repositories,providers}/   # 4-layer architecture
  app/providers/triage/{base,llm,ollama,rules,simulated,factory}.py
  alembic/versions/                                # schema migrations
  scripts/seed.py                                  # idempotent seed, 32 complaints
  tests/                                            # 30 pytest tests
frontend/
  src/{pages,components,api,types}/
  tests/                                            # 11 vitest tests
```

## Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

cp .env.example .env   # edit DATABASE_URL / REDIS_URL for your environment

# Against a real Postgres + Redis:
alembic upgrade head
python -m scripts.seed
uvicorn app.main:app --reload --timeout-graceful-shutdown 30

# Tests (no external services needed - SQLite + in-memory doubles):
pytest -q --cov=app --cov-report=term-missing
ruff check app tests scripts
```

`TRIAGE_PROVIDER` selects the active triage backend: `llm` (Groq),
`ollama` (local), `rules` (deterministic fallback), or `simulated`
(deterministic fake, used to pin the test suite).

## Frontend

```bash
cd frontend
npm install
npm run dev      # proxies /api to http://localhost:8000 in dev (see vite.config.ts)
npm run build    # tsc -b && vite build
npm test         # vitest run
```

The frontend never bakes an API URL into the build
(`import.meta.env.VITE_API_URL` is intentionally unused). It calls relative
`/api/...` paths; Vite's dev proxy and nginx's `location /api/` block
(`frontend/nginx.conf`) both forward those to the backend, so the same built
artifact works in any environment.

## Test summary

- Backend: 30 pytest tests, 76% coverage, `TRIAGE_PROVIDER=simulated` for
  determinism. Covers valid/invalid state transitions, rate-limit 429s,
  stats cache HIT/MISS + invalidation-on-write, the mandatory
  fallback-to-rules test, and a dedicated prompt-injection guardrail suite.
- Frontend: 11 Vitest tests across Submit, Dashboard, Stats, and the
  validation helper.
