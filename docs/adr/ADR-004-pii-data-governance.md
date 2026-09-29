# ADR-004: PII and Data Governance

## Status
Accepted

## Decision
Complaint text and reporter contact are treated as potentially sensitive data. Provider credentials are supplied through environment/deployment secrets and are not committed.

AI processing remains behind the triage provider interface.

## Rationale
Complaint submissions can contain personal information, so logs and telemetry should avoid copying raw complaint text or secrets.

## Consequences
Production deployments must use secret management for provider credentials and avoid exposing PII in observability data.
