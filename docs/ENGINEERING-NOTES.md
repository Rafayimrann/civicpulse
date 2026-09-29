# Engineering Notes

## 1. Laptop vs CI
Three important differences are host dependency state, containerized runtime behavior, and Kubernetes networking/configuration. These are frozen by `.github/workflows/ci.yml`, `backend/Dockerfile`, `frontend/Dockerfile`, `compose.yaml`, and `k8s/base/*.yaml`.

## 2. Pipeline maturity
The current pipeline automates linting, type checks, tests, frontend build, Docker scanning, Compose integration, and Kubernetes validation. The next maturity step is a gated publish/deploy workflow that promotes the same immutable image reference.

## 3. Build once, deploy many
`compose.prod.yaml` requires an explicit `IMAGE_TAG` and uses that reference for both application images. Without an explicit reference, rollback and auditability are ambiguous because a mutable tag can point to different bytes.

## 4. LLM correctness
LLM responses are probabilistic, so CI should not assert one exact natural-language response from an external model. The simulated provider gives deterministic tests while structured outputs are validated before use.

## 5. HPA lag
Observed scale-up time includes metrics collection, HPA reconciliation, scheduling, image availability, and readiness. Faster metrics, tuned behavior, lightweight readiness checks, and available images reduce lag.

## 6. VPA Off
VPA recommendation mode avoids having VPA resize/evict pods while HPA is independently changing replica count from resource utilization. Recommendations can be reviewed and applied deliberately.

## 7. Internal network
Compose `internal: true` prevents general outbound connectivity for services attached only to that network. The backend is attached to edge and internal networks because it serves API traffic while reaching Postgres/Redis. Hosted-provider requests originate from the backend.

## 8. Debugging lesson
Several CI failures came from environment and configuration mismatches: missing test package initialization, FastAPI typing assumptions, frontend lint configguration, and vulnerable dependency/base-image versions. Encoding these checks in CI turns those failures into repeatable gates.
