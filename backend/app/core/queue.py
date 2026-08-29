from typing import Protocol, Any, Callable
import asyncio

class EventQueue(Protocol):
    async def push(self, event: Any) -> None:
        ...
        
    async def pop(self) -> Any:
        ...

class InMemoryBoundedQueue:
    def __init__(self, maxsize: int = 10000):
        self._queue = asyncio.Queue(maxsize=maxsize)
        self._drop_counter = 0

    async def push(self, event: Any) -> None:
        try:
            self._queue.put_nowait(event)
        except asyncio.QueueFull:
            # If the queue is full, we could wait, or for UDP we might drop.
            # We'll expose async push to allow backpressure for TCP/HTTP.
            await self._queue.put(event)

    def push_nowait(self, event: Any) -> bool:
        try:
            self._queue.put_nowait(event)
            return True
        except asyncio.QueueFull:
            self._drop_counter += 1
            return False

    async def pop(self) -> Any:
        return await self._queue.get()
        
    def task_done(self):
        self._queue.task_done()

# Global singleton for the MVP
event_queue = InMemoryBoundedQueue()
