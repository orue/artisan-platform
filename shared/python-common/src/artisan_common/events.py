"""NATS JetStream event publishing and subscribing base.

Provides a thin wrapper around nats-py for consistent event handling
across all Artisan services. Events use the subject convention:
    {domain}.{event_type}
    e.g., art.created, order.paid, notification.email

Usage — Publishing:
    from artisan_common.events import NATSClient

    nats_client = NATSClient(nats_url="nats://localhost:4222")
    await nats_client.connect()
    await nats_client.publish("art.created", {"artwork_id": "abc-123", "title": "Sunset"})

Usage — Subscribing:
    async def handle_art_created(event: dict) -> None:
        print(f"New artwork: {event['artwork_id']}")

    await nats_client.subscribe("art.created", handler=handle_art_created)
"""

import json
from collections.abc import Callable, Coroutine
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import nats
import structlog
from nats.aio.client import Client as NATSConnection
from nats.js.client import JetStreamContext

logger = structlog.get_logger()

# Type alias for event handler functions
EventHandler = Callable[[dict[str, Any]], Coroutine[Any, Any, None]]


class NATSClient:
    """NATS JetStream client for event-driven communication."""

    def __init__(self, nats_url: str = "nats://localhost:4222", stream_name: str = "ARTISAN") -> None:
        self._nats_url = nats_url
        self._stream_name = stream_name
        self._nc: NATSConnection | None = None
        self._js: JetStreamContext | None = None

    async def connect(self) -> None:
        """Connect to NATS and ensure the JetStream stream exists."""
        self._nc = await nats.connect(self._nats_url)
        self._js = self._nc.jetstream()

        # Create or update the stream — idempotent
        await self._js.add_stream(
            name=self._stream_name,
            subjects=[
                "art.>",
                "order.>",
                "notification.>",
            ],
        )
        logger.info("nats_connected", url=self._nats_url, stream=self._stream_name)

    async def publish(self, subject: str, data: dict[str, Any]) -> None:
        """Publish an event to a NATS JetStream subject.

        Wraps the payload in a standard envelope with metadata:
            {
                "event_id": "uuid",
                "subject": "art.created",
                "timestamp": "ISO-8601",
                "data": { ... your payload ... }
            }
        """
        if not self._js:
            msg = "NATS not connected. Call connect() first."
            raise RuntimeError(msg)

        envelope = {
            "event_id": str(uuid4()),
            "subject": subject,
            "timestamp": datetime.now(tz=UTC).isoformat(),
            "data": data,
        }

        payload = json.dumps(envelope).encode()
        ack = await self._js.publish(subject, payload)
        logger.info("event_published", subject=subject, stream=ack.stream, seq=ack.seq)

    async def subscribe(
        self,
        subject: str,
        handler: EventHandler,
        durable_name: str | None = None,
    ) -> None:
        """Subscribe to a NATS JetStream subject with a pull subscription.

        Args:
            subject: NATS subject pattern (e.g., "art.created" or "art.>").
            handler: Async function that receives the event data dict.
            durable_name: Durable consumer name for reliable delivery.
                          Defaults to subject with dots replaced by dashes.
        """
        if not self._js:
            msg = "NATS not connected. Call connect() first."
            raise RuntimeError(msg)

        if durable_name is None:
            durable_name = subject.replace(".", "-").replace(">", "all")

        subscription = await self._js.subscribe(subject, durable=durable_name)
        logger.info("event_subscribed", subject=subject, durable=durable_name)

        async for msg in subscription.messages:
            try:
                envelope = json.loads(msg.data.decode())
                await handler(envelope.get("data", {}))
                await msg.ack()
            except Exception:
                logger.exception("event_handler_error", subject=subject, data=msg.data.decode())
                # NATS will redeliver on nack (or timeout)
                await msg.nak()

    async def close(self) -> None:
        """Gracefully close the NATS connection."""
        if self._nc:
            await self._nc.drain()
            logger.info("nats_disconnected")
