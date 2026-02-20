# ADR-003: No Service Mesh in Phase 1

## Status
Accepted (Phase 1) — Revisit for Phase 2

## Context
Considered Linkerd for automatic mTLS, traffic management, and observability.

## Decision
Defer service mesh to Phase 2. Design services to be mesh-ready.

## Rationale
- 6 services don't justify the operational overhead of proxy sidecars
- mTLS achieved at ingress level via Kong + TLS termination
- Service-to-service auth via JWT propagation in Authorization headers
- Observability via OpenTelemetry (independent of any mesh)
- Services include health probes, graceful shutdown, and header propagation — mesh-ready

## Trade-offs
- No automatic mTLS between services within the cluster
- No traffic splitting or canary deployments at the mesh level
- Acceptable for a portfolio project; would add Linkerd in production
