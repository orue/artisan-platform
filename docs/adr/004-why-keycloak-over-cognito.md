# ADR-004: Keycloak over AWS Cognito

## Status
Accepted

## Context
Need an OAuth2/OIDC identity provider for authentication and authorization.

## Decision
Keycloak deployed on EKS via Helm chart.

## Rationale
- Full configuration exported as JSON and stored in the repository
- Demonstrates understanding of OAuth2/OIDC protocols, not just SDK usage
- Free and open-source with no per-MAU pricing
- Supports custom themes, social login, and fine-grained RBAC

## Trade-offs
- Must manage Keycloak deployment, upgrades, and database
- Mitigated by Helm chart, Argo CD, and PostgreSQL on RDS
- Slightly higher operational overhead than a managed service
