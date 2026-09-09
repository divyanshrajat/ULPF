import asyncio
from typing import Any, Protocol


class EventQueue(Protocol):
    async def publish(self, event: Any) -> None:
        ...
        
    async def consume(self) -> Any:
        ...

    def ack(self, event: Any) -> None:
        ...

    def reject(self, event: Any) -> None:
        ...

    def depth(self) -> int:
        ...

class InMemoryEventQueue:
    def __init__(self, maxsize: int = 10000):
        self._queue = asyncio.Queue(maxsize=maxsize)
        self._drop_counter = 0

    async def publish(self, event: Any) -> None:
        await self._queue.put(event)

    async def consume(self) -> Any:
        return await self._queue.get()
        
    def ack(self, event: Any) -> None:
        self._queue.task_done()

    def reject(self, event: Any) -> None:
        # In memory, reject is equivalent to acking since it's removed,
        # but in a real queue like RabbitMQ it might re-queue.
        self._queue.task_done()

    def depth(self) -> int:
        return self._queue.qsize()

# Global singleton for the MVP, typed as the interface
event_queue: EventQueue = InMemoryEventQueue()
