# ADR-003: Deploy by Immutable Image Reference

## Status
Accepted

## Decision
Production deployment must use an explicit image reference rather than `latest`. `compose.prod.yaml` requires `IMAGE_TAG` and uses it for backend and frontend images.

## Rationale
An immutable deployment reference makes releases auditable and rollback deterministic.

## Consequences
A release workflow must publish and deploy the exact verified image reference.
