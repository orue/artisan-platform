# ADR-002: NATS JetStream over Kafka / SQS

## Status
Accepted

## Context
Need asynchronous messaging for event-driven communication between services.

## Decision
NATS with JetStream for persistent, at-least-once delivery.

## Rationale
- Single binary, ~50MB RAM footprint vs. Kafka's multi-GB requirement
- JetStream provides stream replay and durable consumers
- Runs identically locally and in Kubernetes
- Perfect scale for 6 services — Kafka is designed for thousands of partitions

## Trade-offs
- Smaller ecosystem and community than Kafka
- Fewer managed service options (no "Amazon MSK for NATS")
- Acceptable for this project's scale; would evaluate Kafka for 50+ services
