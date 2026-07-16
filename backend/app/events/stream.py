"""Event streaming utilities."""

import asyncio
import json
import uuid
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import EventRepository


class EventStreamManager:
    """In-memory pub/sub for SSE event streaming (MVP)."""

    def __init__(self) -> None:
        self._subscribers: dict[uuid.UUID, list[asyncio.Queue]] = {}

    def subscribe(self, execution_id: uuid.UUID) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue()
        self._subscribers.setdefault(execution_id, []).append(queue)
        return queue

    def unsubscribe(self, execution_id: uuid.UUID, queue: asyncio.Queue) -> None:
        subscribers = self._subscribers.get(execution_id, [])
        if queue in subscribers:
            subscribers.remove(queue)
        if not subscribers:
            self._subscribers.pop(execution_id, None)

    async def publish(self, execution_id: uuid.UUID, event_data: dict) -> None:
        for queue in self._subscribers.get(execution_id, []):
            await queue.put(event_data)


event_stream_manager = EventStreamManager()


async def stream_execution_events(
    session: AsyncSession,
    execution_id: uuid.UUID,
) -> AsyncGenerator[dict, None]:
    """Yield SSE events for an execution, including historical and live events."""
    repo = EventRepository(session)
    history = await repo.list_for_execution(execution_id)

    for event in history:
        yield {
            "event": event.type,
            "data": json.dumps(
                {
                    "id": str(event.id),
                    "type": event.type,
                    "payload": event.payload,
                    "created_at": event.created_at.isoformat(),
                }
            ),
        }

    queue = event_stream_manager.subscribe(execution_id)
    try:
        while True:
            try:
                event_data = await asyncio.wait_for(queue.get(), timeout=30.0)
                yield event_data
            except TimeoutError:
                yield {"event": "heartbeat", "data": "{}"}
    finally:
        event_stream_manager.unsubscribe(execution_id, queue)
