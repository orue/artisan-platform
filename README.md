# 🎨 Artisan Platform

**A cloud-native microservices platform for an online art gallery — built to demonstrate production-grade architecture, not just code.**

---

## Architecture

| Component | Technology |
|-----------|-----------|
| **Orchestration** | AWS EKS (Kubernetes) |
| **Services** | Python / FastAPI (5 microservices) |
| **API Gateway** | Kong Ingress Controller |
| **Auth** | Keycloak (OAuth2/OIDC) |
| **Database** | PostgreSQL (RDS) |
| **Cache** | Redis (ElastiCache) |
| **Messaging** | NATS JetStream |
| **AI** | AWS Bedrock (Claude) |
| **Payments** | Stripe |
| **Observability** | Grafana + Loki + Tempo + OpenTelemetry |
| **GitOps** | Argo CD + Helm |
| **IaC** | Terraform |
| **CI/CD** | GitHub Actions |

## Services

| Service | Responsibility |
|---------|---------------|
| **auth-service** | OAuth2/OIDC via Keycloak, JWT validation, RBAC |
| **gallery-service** | Artwork CRUD, search, catalog, S3 image storage |
| **order-service** | Cart, checkout, Stripe payment orchestration (Saga pattern) |
| **notification-service** | Email (SES), WebSocket push, event-driven fan-out |
| **ai-service** | AI art descriptions (Bedrock/Claude), smart search |

## Quick Start

```bash
# Clone and set up
git clone https://github.com/<your-username>/artisan-platform.git
cd artisan-platform
make init

# Start local infrastructure
make infra-up

# Run a service (e.g., gallery-service)
make install service=gallery-service
make dev service=gallery-service port=8001

# Open API docs
open http://localhost:8001/docs
