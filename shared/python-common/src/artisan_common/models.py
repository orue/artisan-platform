"""Shared Pydantic models used across Artisan services.

These models define the contract between services. When the gallery-service
publishes an "art.created" event, the notification-service and ai-service
both deserialize it using the same ArtworkEvent model. This prevents
schema drift between producer and consumer.
"""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ── Enums ─────────────────────────────────────────────────────


class ArtworkStatus(StrEnum):
    """Lifecycle states for an artwork listing."""

    DRAFT = "draft"
    PUBLISHED = "published"
    SOLD = "sold"
    ARCHIVED = "archived"


class OrderStatus(StrEnum):
    """Lifecycle states for an order."""

    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


# ── Base Models ───────────────────────────────────────────────


class ArtisanModel(BaseModel):
    """Base model with shared configuration for all Artisan models."""

    model_config = ConfigDict(
        from_attributes=True,  # Allows creating from SQLAlchemy ORM objects
        populate_by_name=True,
        str_strip_whitespace=True,
    )


# ── API Response Models ───────────────────────────────────────


class HealthResponse(BaseModel):
    """Standard health check response for all services."""

    status: str = "healthy"
    service: str
    version: str
    environment: str


class PaginatedResponse(BaseModel):
    """Standard paginated response wrapper."""

    items: list[BaseModel] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20
    total_pages: int = 0


# ── Event Models ──────────────────────────────────────────────


class ArtworkEvent(ArtisanModel):
    """Event payload for artwork lifecycle events (art.created, art.updated, etc.)."""

    artwork_id: UUID
    title: str
    artist_id: UUID
    status: ArtworkStatus
    image_url: str | None = None


class OrderEvent(ArtisanModel):
    """Event payload for order lifecycle events (order.placed, order.paid, etc.)."""

    order_id: UUID
    buyer_id: UUID
    artwork_id: UUID
    amount_cents: int
    currency: str = "usd"
    status: OrderStatus
    stripe_payment_intent_id: str | None = None


class NotificationEvent(ArtisanModel):
    """Event payload for notification requests."""

    recipient_id: UUID
    channel: str  # "email" | "websocket"
    template: str
    data: dict[str, str] = Field(default_factory=dict)
    timestamp: datetime | None = None
