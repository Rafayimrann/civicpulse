# ADR-001: Triage Provider Interface

## Status
Accepted

## Decision
Use a `TriageProvider` interface and select the implementation through `TRIAGE_PROVIDER`. The repository includes hosted LLM, Ollama, rules, and simulated providers.

The service validates structured output and falls back to rules when the active provider fails.

## Rationale
This keeps complaint business logic independent from a specific AI vendor and makes CI deterministic.

## Consequences
New providers implement the interface and are registered through the provider factory.
