# ADR-002: Frontend Runtime Configuration

## Status
Accepted

## Decision
The frontend calls relative `/api/...` paths instead of embedding an environment-specific backend URL in the production bundle.

Vite proxies `/api` in development and nginx forwards `/api/` to the backend in the containerized deployment.

## Rationale
One built frontend artifact can be promoted across environms without rebuilding for each backend URL.

## Consequences
Reverse-proxy configuration is part of the deployment contract.
