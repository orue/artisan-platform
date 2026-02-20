# ADR-001: Kong Ingress Controller over AWS API Gateway

## Status
Accepted

## Context
Need an API gateway for routing, rate limiting, and auth forwarding.

## Decision
Kong Ingress Controller (OSS) deployed on EKS.

## Rationale
- Configuration lives in Git as declarative YAML — fully visible and reviewable
- No per-request pricing (AWS API Gateway charges per million requests)
- Demonstrates understanding of gateway internals, not just managed-service configuration
- Supports custom plugins for future extensibility

## Trade-offs
- More operational responsibility than a fully managed service
- Must manage Kong upgrades and configuration
- Mitigated by Helm chart deployment and Argo CD auto-sync
