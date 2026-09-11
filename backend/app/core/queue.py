"""
core/queue.py — Event queue abstraction.

adds RedisStreamEventQueue, a durable backend behind the same
EventQueue interface every call site already uses (publish/consume/ack/
reject/depth). Nothing in jobs.py, sessions.py, onboarding.py, gateway.py,
or workers/processor.py needs to change — they only ever call the
protocol methods on the `event_queue` singleton at the bottom of this file.

Durability semantics: this gives at-least-once delivery. A message is only
removed from the stream when ack() succeeds; if the process crashes after
consume() but before ack(), XAUTOCLAIM hands the message to the next
consumer once it's been idle past CLAIM_IDLE_MS. That means a crash can
cause one event to be processed twice, never zero times. workers/processor.py
is not currently idempotent on trace_id — if exactly-once matters before
this ships, add a check there (e.g. skip if a NormalizedEvent or DeadLetter
already exists for the trace_id) before doing the reprocessing work.

Not tested against a live Redis in this pass — verify against your actual
Redis container before relying on it: publish a batch, kill the worker
process mid-consume, restart it, and confirm every event still lands in
NormalizedEvent or DeadLetter exactly once (or twice, per the note above —
never zero).
"""
import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Protocol

import redis.asyncio as aioredis

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class EventRecord:
    trace_id: str
    source_id: str
    payload: bytes
    byte_length: int


class EventQueue(Protocol):
    async def publish(self, event: Any) -> None: ...
    async def consume(self) -> Any: ...
    def ack(self, event: Any) -> None: ...
    def reject(self, event: Any) -> None: ...
    def depth(self) -> int: ...


class InMemoryEventQueue:
    """Kept as-is: used directly by tests/test_queue.py, and as a fallback
    when QUEUE_BACKEND=memory (local dev without Redis running)."""

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
        self._queue.task_done()

    def depth(self) -> int:
        return self._queue.qsize()


class RedisStreamEventQueue:
    """
    Durable event queue backed by a Redis Stream + consumer group.
    Events published before a crash remain in the stream and are
    redelivered on the next consume() call after restart.
    """

    STREAM_KEY = "ulpf:events"
    GROUP_NAME = "ulpf-workers"
    CONSUMER_NAME = "worker-1"  # single worker for MVP; make unique per replica if you scale out
    CLAIM_IDLE_MS = 30_000      # reclaim messages a crashed/stalled consumer left pending >30s
    BLOCK_MS = 5000             # how long consume() waits for a new message before looping

    def __init__(self, redis_uri: str):
        self._redis = aioredis.from_url(redis_uri, decode_responses=False)
        self._group_ready = False

    async def _ensure_group(self) -> None:
        if self._group_ready:
            return
        try:
            # id="0" replays anything already in the stream from before this
            # process started (e.g. a prior crash); mkstream creates the
            # stream key itself if it doesn't exist yet.
            await self._redis.xgroup_create(self.STREAM_KEY, self.GROUP_NAME, id="0", mkstream=True)
        except aioredis.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise
        self._group_ready = True

    async def publish(self, event: Any) -> None:
        await self._ensure_group()
        fields = {
            "trace_id": event.trace_id.encode(),
            "source_id": event.source_id.encode(),
            "payload": event.payload,
            "byte_length": str(event.byte_length).encode(),
        }
        await self._redis.xadd(self.STREAM_KEY, fields)

    async def consume(self) -> Any:
        await self._ensure_group()
        while True:
            claimed = await self._reclaim_stale()
            if claimed is not None:
                return claimed

            resp = await self._redis.xreadgroup(
                groupname=self.GROUP_NAME,
                consumername=self.CONSUMER_NAME,
                streams={self.STREAM_KEY: ">"},
                count=1,
                block=self.BLOCK_MS,
            )
            if not resp:
                continue  # BLOCK_MS timeout with nothing new — loop back and re-check reclaim
            _, messages = resp[0]
            msg_id, fields = messages[0]
            return self._to_record(msg_id, fields)

    async def _reclaim_stale(self):
        try:
            _, claimed, _ = await self._redis.xautoclaim(
                self.STREAM_KEY,
                self.GROUP_NAME,
                self.CONSUMER_NAME,
                min_idle_time=self.CLAIM_IDLE_MS,
                start_id="0-0",
                count=1,
            )
        except aioredis.ResponseError:
            return None
        if not claimed:
            return None
        msg_id, fields = claimed[0]
        return self._to_record(msg_id, fields)

    def _to_record(self, msg_id: bytes, fields: dict) -> EventRecord:
        record = EventRecord(
            trace_id=fields[b"trace_id"].decode(),
            source_id=fields[b"source_id"].decode(),
            payload=fields[b"payload"],
            byte_length=int(fields[b"byte_length"]),
        )
        record._redis_msg_id = msg_id  # stashed for ack()/reject(); harmless extra attribute
        return record

    def ack(self, event: Any) -> None:
        msg_id = getattr(event, "_redis_msg_id", None)
        if msg_id is None:
            return
        try:
            asyncio.get_running_loop().create_task(
                self._redis.xack(self.STREAM_KEY, self.GROUP_NAME, msg_id)
            )
        except RuntimeError:
            logger.warning("ack() called with no running event loop; message will be reclaimed after CLAIM_IDLE_MS instead")

    def reject(self, event: Any) -> None:
        # Deliberately a no-op: leaving the message unacked means XAUTOCLAIM
        # redelivers it after CLAIM_IDLE_MS, which is the desired "retry"
        # behavior for a rejected event rather than dropping it.
        pass

    def depth(self) -> int:
        # XLEN requires an await on this async client; not exposed as a sync
        # call. Use `await redis.xlen(RedisStreamEventQueue.STREAM_KEY)` from
        # an async context (e.g. the /api/v1/system/health handler) instead
        # of calling this method if you need a live queue-depth metric.
        return -1


def _build_event_queue() -> EventQueue:
    backend = getattr(settings, "QUEUE_BACKEND", "redis")
    if backend == "memory":
        logger.warning("QUEUE_BACKEND=memory — events are NOT durable across a process restart")
        return InMemoryEventQueue()
    return RedisStreamEventQueue(settings.REDIS_URI)


event_queue: EventQueue = _build_event_queue()
